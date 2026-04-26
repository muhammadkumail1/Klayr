"""
Literature QC prompt builder.
Pure function — receives the refined hypothesis and fetched Paper objects.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.experiment import Paper

SYSTEM = """You are a senior scientific literature reviewer with expertise in biomedical research. \
Given a hypothesis and a set of retrieved papers, you assess novelty, identify literature gaps, \
and extract the most relevant methodological insights. Return ONLY valid JSON. \
No preamble. No markdown fences."""


def build(refined_hypothesis: str, papers: "list[Paper]") -> str:
    papers_block = ""
    if papers:
        entries = []
        for i, p in enumerate(papers, 1):
            summary = p.abstract_summary or p.abstract or "No abstract available."
            entries.append(
                f"[{i}] Title: {p.title}\n"
                f"    Authors: {', '.join(p.authors[:3])}\n"
                f"    Year: {p.year} | Source: {p.source}\n"
                f"    URL: {p.url}\n"
                f"    Summary: {summary}"
            )
        papers_block = "\n\n".join(entries)
    else:
        papers_block = "No papers were retrieved. Treat as not_found."

    return f"""
Hypothesis: {refined_hypothesis}

Retrieved Literature ({len(papers)} papers):
{papers_block}

Assess novelty and identify what is missing in current literature.

Return ONLY valid JSON matching this exact schema:
{{
  "novelty_signal": "not_found | similar_work_exists | exact_match_found",
  "gap_analysis": "string — 2-4 sentences describing what is NOT yet studied or answered by existing literature, and why this experiment adds value",
  "methodological_insights": ["string — key methodological takeaway from each paper relevant to designing this experiment"],
  "references": [
    {{
      "title": "string",
      "authors": ["string"],
      "year": 0,
      "url": "string",
      "abstract_summary": "string",
      "source": "string",
      "relevance_note": "string — one sentence: why this paper is relevant to the hypothesis"
    }}
  ]
}}

Rules:
- novelty_signal must be exactly one of the three enum values.
- references: include only papers directly relevant to this hypothesis (max 3).
- relevance_note: must explain the specific connection to the hypothesis, not just describe the paper.
- gap_analysis: focus on what this experiment uniquely contributes.
""".strip()
