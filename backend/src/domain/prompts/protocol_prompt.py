"""
Protocol prompt builder.
Incorporates few-shot feedback corrections from prior scientist reviews.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import LiteratureResult, FeedbackEntry

SYSTEM = """You are an expert laboratory protocol writer with 20 years of wet lab experience. \
You ground every protocol step in published methodology from protocols.io, Nature Protocols, \
or peer-reviewed sources. You generate detailed, operationally realistic step-by-step protocols \
that a real lab technician can execute without additional guidance. \
Return ONLY valid JSON. No preamble. No markdown fences."""


def build(
    refined_hypothesis: str,
    lit_result: "LiteratureResult",
    few_shots: "list[FeedbackEntry]",
) -> str:
    shot_block = ""
    if few_shots:
        corrections = "\n".join(
            f"  - [{s.section.upper()}] {s.correction}" for s in few_shots
        )
        shot_block = (
            "\nPRIOR SCIENTIST CORRECTIONS — incorporate ALL of these:\n"
            + corrections
            + "\n"
        )

    refs_block = ""
    if lit_result.references:
        refs_block = "Methodological context from literature:\n" + "\n".join(
            f"- {p.title} ({p.year}): {p.abstract_summary or 'N/A'}"
            for p in lit_result.references
        )

    return f"""
Hypothesis: {refined_hypothesis}
Novelty signal: {lit_result.novelty_signal}
Literature gap: {lit_result.gap_analysis}
{refs_block}
{shot_block}
Generate a complete, step-by-step laboratory protocol. Each step must be operationally \
specific: exact concentrations, temperatures, centrifuge speeds, incubation times.

Return ONLY valid JSON matching this exact schema:
{{
  "steps": [
    {{
      "step_number": 1,
      "title": "string — concise action title",
      "description": "string — full operational detail, exact conditions",
      "duration_minutes": 0,
      "equipment_needed": ["string"],
      "notes": "string | null — safety warnings, troubleshooting tips, or null"
    }}
  ]
}}

Rules:
- Minimum 8 steps, maximum 20. Cover setup, execution, measurement, and cleanup.
- Ground each step in published methodology (protocols.io, Nature Protocols, ATCC guidelines).
- Include control preparation as an explicit step.
- equipment_needed: list every piece of equipment required for that specific step.
- notes: include GHS hazard warnings for any hazardous reagents.
- Do NOT include caveats or confidence disclaimers.
""".strip()
