"""
Materials prompt builder.
Derives a materials list from the protocol steps.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import ProtocolStep

SYSTEM = """You are a laboratory procurement specialist with expertise in biomedical research \
supply chains. Given a protocol, you generate a comprehensive, fully-specified materials list \
with real catalog numbers from Sigma-Aldrich, Thermo Fisher Scientific, or Abcam. \
Return ONLY valid JSON. No preamble. No markdown fences."""


def build(protocol_steps: "list[ProtocolStep]") -> str:
    steps_block = "\n".join(
        f"Step {s.step_number}: {s.title} — {s.description[:200]}"
        for s in protocol_steps
    )

    return f"""
Protocol steps:
{steps_block}

Generate a complete materials and reagents list required to execute this protocol.

Return ONLY valid JSON matching this exact schema:
{{
  "materials": [
    {{
      "name": "string — full IUPAC or trade name",
      "catalog_number": "string — real catalog number (e.g. S7907 for Sigma) or 'CATALOG_TBD' if unknown",
      "supplier": "string — Sigma-Aldrich | Thermo Fisher Scientific | Abcam | ATCC | other",
      "quantity": "string — e.g. '50 mL', '1 kit', '500 mg'",
      "unit_cost_usd": 0.00,
      "total_cost_usd": 0.00,
      "hazard_class": "string | null — GHS hazard class or null if non-hazardous"
    }}
  ]
}}

Rules:
- Include EVERY reagent, buffer, cell line, kit, consumable, and disposable mentioned or implied.
- Use real catalog numbers from Sigma-Aldrich or Thermo Fisher when possible.
- If the exact catalog number is unknown, use 'CATALOG_TBD' — never fabricate one.
- unit_cost_usd: estimate from current catalog prices based on training knowledge.
- total_cost_usd = unit_cost_usd × quantity ordered (round up to standard pack sizes).
- hazard_class: include GHS class for any flammable, corrosive, toxic, or biohazardous material.
- Do NOT list equipment (only consumables and reagents).
""".strip()
