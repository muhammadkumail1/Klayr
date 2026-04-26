"""
Timeline prompt builder.
Creates a phased project timeline from the protocol and budget.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import ProtocolStep, Budget

SYSTEM = """You are a research project manager with deep experience planning academic and industry \
lab experiments. Given a protocol and budget, you produce a realistic phased timeline with \
dependencies, milestones, and task assignments. Return ONLY valid JSON. \
No preamble. No markdown fences."""


def build(protocol_steps: "list[ProtocolStep]", budget: "Budget") -> str:
    total_protocol_minutes = sum(s.duration_minutes for s in protocol_steps)
    total_protocol_days = round(total_protocol_minutes / (60 * 8), 1)  # 8-hour workdays

    steps_summary = "\n".join(
        f"Step {s.step_number}: {s.title} ({s.duration_minutes} min)"
        for s in protocol_steps
    )
    budget_summary = f"Total budget: ${budget.grand_total_usd:.2f}"

    return f"""
Protocol summary ({len(protocol_steps)} steps, ~{total_protocol_days} lab-days of bench time):
{steps_summary}

{budget_summary}

Generate a realistic phased project timeline from procurement through data analysis and writeup.

Return ONLY valid JSON matching this exact schema:
{{
  "phases": [
    {{
      "phase_name": "string — e.g. 'Procurement & Setup', 'Pilot Run', 'Main Experiment', 'Data Analysis', 'Writeup'",
      "duration_days": 0,
      "tasks": ["string — specific actionable task"],
      "depends_on": ["string — phase_name of phases that must complete first, or empty list"],
      "milestone": "string | null — key deliverable at end of phase, or null"
    }}
  ]
}}

Rules:
- Include these mandatory phases: Procurement & Setup, Optimization/Pilot, Main Experiment, \
Data Analysis, Writeup & Review.
- depends_on: ensure no circular dependencies.
- duration_days: be realistic — cell culture experiments take weeks, not hours.
- milestone: at least 3 phases must have a defined milestone.
- tasks: minimum 3 tasks per phase, each specific enough for a lab notebook entry.
- Do NOT include caveats or confidence disclaimers.
""".strip()
