"""
Risk assessment prompt builder.
Identifies potential failure modes and mitigation strategies.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import ProtocolStep, Reagent

SYSTEM = """You are a research risk analyst and experimental troubleshooting expert with extensive \
wet lab experience. You identify technical, biological, and logistical risks in experimental \
protocols and propose specific, actionable mitigation strategies. \
Return ONLY valid JSON. No preamble. No markdown fences."""


def build(protocol_steps: "list[ProtocolStep]", materials: "list[Reagent]") -> str:
    steps_block = "\n".join(
        f"Step {s.step_number}: {s.title} — {s.description[:150]}"
        for s in protocol_steps
    )
    catalog_tbd = [m.name for m in materials if m.catalog_number == "CATALOG_TBD"]
    tbd_note = f"\nMaterials with unresolved catalog numbers: {', '.join(catalog_tbd)}" if catalog_tbd else ""

    return f"""
Protocol steps:
{steps_block}
{tbd_note}

Identify all significant risks in this experimental workflow.

Return ONLY valid JSON matching this exact schema:
{{
  "risks": [
    {{
      "description": "string — specific risk scenario",
      "severity": "low | medium | high",
      "likelihood": "low | medium | high",
      "mitigation": "string — specific, actionable mitigation step"
    }}
  ]
}}

Rules:
- Minimum 4 risks, maximum 10.
- Cover: technical failure risks, biological variability risks, reagent/supply risks, \
timeline risks, and data quality risks.
- severity: impact on experiment validity if the risk materializes.
- likelihood: probability of occurrence without mitigation.
- mitigation: must be a specific action (not generic advice like "be careful").
- If CATALOG_TBD items exist, include a supply chain risk for each.
""".strip()
