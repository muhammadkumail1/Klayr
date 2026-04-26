"""
Budget prompt builder.
Derives a categorized budget from the materials list.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import Reagent

SYSTEM = """You are a research finance specialist familiar with academic and biotech lab budgeting. \
Given a materials list, you build a complete, categorized experiment budget covering reagents, \
equipment rental, personnel time, and overhead. Return ONLY valid JSON. No preamble. \
No markdown fences."""


def build(materials: "list[Reagent]") -> str:
    materials_block = "\n".join(
        f"- {m.name} | {m.supplier} #{m.catalog_number} | {m.quantity} | ${m.total_cost_usd:.2f}"
        for m in materials
    )
    reagent_total = sum(m.total_cost_usd for m in materials)

    return f"""
Materials list (reagents/consumables):
{materials_block}

Reagents subtotal: ${reagent_total:.2f}

Build a full experiment budget broken into standard grant/lab categories.

Return ONLY valid JSON matching this exact schema:
{{
  "line_items": [
    {{
      "category": "string — reagents | equipment_rental | personnel | consumables | overhead | other",
      "description": "string — what this cost covers",
      "cost_usd": 0.00
    }}
  ],
  "grand_total_usd": 0.00,
  "currency_note": "string"
}}

Rules:
- reagents: sum ALL material costs from the list above — do not change them.
- equipment_rental: estimate core facility rates (flow cytometer ~$80/hr, confocal ~$120/hr, etc.).
- personnel: estimate technician time at $35/hr; postdoc time at $55/hr.
- consumables: pipette tips, tubes, plates not already in the materials list.
- overhead: apply 26% indirect cost rate on direct costs (standard NIH rate for academic labs).
- grand_total_usd MUST equal the exact sum of all line_item cost_usd values.
- Do NOT include caveats or confidence disclaimers.
""".strip()
