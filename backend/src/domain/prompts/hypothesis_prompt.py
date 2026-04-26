"""
Hypothesis prompt builder.
Pure function — no imports outside stdlib/domain entities.
"""

SYSTEM = """You are a scientific hypothesis analyst and methodologist with a PhD in experimental \
design. Your job is to sharpen vague research questions into precise, testable, falsifiable \
hypotheses in standard form: "If [independent variable], then [dependent variable], because \
[mechanism]." You also identify the experiment domain and decompose compound hypotheses into \
atomic sub-hypotheses. Return ONLY valid JSON. No preamble. No markdown fences."""


def build(raw_input: str) -> str:
    return f"""
Raw hypothesis input from scientist:
\"\"\"{raw_input}\"\"\"

Analyze and refine this into a rigorous scientific hypothesis.

Return ONLY valid JSON matching this exact schema:
{{
  "refined_hypothesis": "string — precise, falsifiable, in If/Then/Because form",
  "experiment_domain": "one of: cell_biology | molecular_biology | biochemistry | microbiology | diagnostics | pharmacology | neuroscience | chemistry | other",
  "sub_hypotheses": ["string", "..."],
  "independent_variable": "string",
  "dependent_variable": "string",
  "proposed_mechanism": "string",
  "alternative_hypotheses": ["string", "..."],
  "expected_outcomes": ["string — specific measurable outcome if hypothesis is confirmed", "..."]
}}

Rules:
- sub_hypotheses: list every independently testable component. If the hypothesis is already atomic, return a list with one entry equal to refined_hypothesis.
- alternative_hypotheses: at least 2 competing explanations the experiment must rule out.
- expected_outcomes: at least 3 specific, quantifiable predictions.
- Do NOT include caveats, confidence levels, or disclaimers.
""".strip()
