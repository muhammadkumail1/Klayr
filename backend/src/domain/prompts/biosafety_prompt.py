"""
Biosafety assessment prompt builder.
Identifies hazards and required safety measures from materials and protocol.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import Reagent, ProtocolStep

SYSTEM = """You are a laboratory biosafety officer and chemical hygiene expert. Given a list of \
materials and a protocol, you assess the biosafety level required and produce a complete safety \
plan covering PPE, waste disposal, and regulatory requirements. \
Return ONLY valid JSON. No preamble. No markdown fences."""


def build(materials: "list[Reagent]", protocol_steps: "list[ProtocolStep]") -> str:
    materials_block = "\n".join(
        f"- {m.name} (hazard: {m.hazard_class or 'unknown'})"
        for m in materials
    )
    steps_block = "\n".join(
        f"Step {s.step_number}: {s.title}" + (f" [NOTE: {s.notes}]" if s.notes else "")
        for s in protocol_steps
    )

    return f"""
Materials in use:
{materials_block}

Protocol steps:
{steps_block}

Assess the biosafety requirements for this experiment.

Return ONLY valid JSON matching this exact schema:
{{
  "level": "BSL-1 | BSL-2 | BSL-3 | BSL-4 | unknown",
  "hazardous_materials": ["string — material name and hazard type"],
  "required_ppe": ["string — specific PPE item, e.g. 'nitrile gloves (double)', 'N95 respirator'"],
  "waste_disposal_protocol": "string — specific disposal method per regulatory standard (EPA/DOT/institutional)",
  "special_requirements": ["string — e.g. 'biosafety cabinet class II required', 'IBC approval needed'"],
  "regulatory_notes": "string | null — any IBC, IRB, DEA, or other regulatory approvals required"
}}

Rules:
- BSL-1: non-pathogenic organisms, standard lab practice.
- BSL-2: moderate hazard pathogens, requires biosafety cabinet for aerosol-generating procedures.
- BSL-3: serious/potentially lethal pathogens, requires negative-pressure room.
- BSL-4: life-threatening pathogens, no treatment available — requires full-pressure suit.
- required_ppe: be specific (glove type, goggle type, coat type).
- If no biological hazards, return BSL-1 with appropriate chemical safety measures.
""".strip()
