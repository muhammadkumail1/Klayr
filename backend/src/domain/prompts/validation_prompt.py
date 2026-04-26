"""
Validation approach prompt builder.
Designs the statistical validation framework for the experiment.
"""
from __future__ import annotations

SYSTEM = """You are a biostatistician and experimental validation expert. You design rigorous \
statistical validation frameworks for laboratory experiments, including sample size calculations, \
appropriate statistical tests, and control strategies. Return ONLY valid JSON. \
No preamble. No markdown fences."""


def build(refined_hypothesis: str, protocol_steps_summary: str) -> str:
    return f"""
Hypothesis: {refined_hypothesis}

Protocol summary:
{protocol_steps_summary}

Design a complete statistical validation approach for this experiment.

Return ONLY valid JSON matching this exact schema:
{{
  "primary_metric": "string — the single most important quantifiable outcome",
  "success_threshold": "string — exact criterion for hypothesis confirmation, e.g. '>20% increase, p<0.05'",
  "statistical_test": "string — specific test name, e.g. 'two-tailed Student t-test', 'one-way ANOVA with Tukey HSD post-hoc'",
  "controls": ["string — each control condition with its purpose"],
  "sample_size_per_group": 0,
  "power": 0.80,
  "alpha": 0.05,
  "effect_size_estimate": "string — e.g. 'Cohen d=0.8 (large effect) based on prior literature'"
}}

Rules:
- primary_metric: must be directly measurable with the equipment listed in the protocol.
- success_threshold: include both effect size AND p-value criterion.
- statistical_test: choose the test appropriate for the data type and experimental design.
- controls: minimum 2 — one positive control, one negative/vehicle control.
- sample_size_per_group: calculate using power=0.80 and alpha=0.05 for the stated effect size.
- power: typically 0.80 (80%); use 0.90 if the study is high-stakes.
- alpha: typically 0.05; justify if different.
- Do NOT include caveats or disclaimers.
""".strip()
