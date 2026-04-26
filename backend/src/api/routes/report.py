"""
GET /api/report/{plan_id}          — generate Markdown final report for a plan.
GET /api/report/{plan_id}/download — download as text file attachment.
"""
from __future__ import annotations

import datetime
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from api.dependencies import get_cache, get_repo
from domain.ports.cache import ICache
from domain.ports.experiment_repo import IExperimentRepo

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ReportResponse(BaseModel):
    plan_id: str
    title: str
    markdown: str
    word_count: int
    created_at: str


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

def _format_list(items: list[str], indent: int = 0) -> str:
    prefix = "  " * indent
    return "\n".join(f"{prefix}- {item}" for item in items) if items else f"{prefix}*(none)*"


def generate_markdown_report(plan) -> str:  # plan: ExperimentPlan
    """Convert an ExperimentPlan into a comprehensive Markdown report."""
    lines: list[str] = []

    # Title
    title = plan.refined_hypothesis[:80] if plan.refined_hypothesis else "Experiment Plan"
    lines += [
        f"# Experiment Report",
        f"",
        f"**Plan ID:** `{plan.plan_id}`  ",
        f"**Domain:** {plan.experiment_domain.value.replace('_', ' ').title()}  ",
        f"**Generated:** {plan.created_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Quality Score:** {plan.quality_score:.1f}/100" if plan.quality_score else "**Quality Score:** N/A",
        f"",
        f"---",
        f"",
    ]

    # Hypothesis
    lines += [
        f"## 1. Hypothesis",
        f"",
        f"**Original:** {plan.hypothesis}",
        f"",
        f"**Refined:** {plan.refined_hypothesis}",
        f"",
    ]

    if plan.sub_hypotheses:
        lines += ["**Sub-hypotheses:**", ""]
        for h in plan.sub_hypotheses:
            lines.append(f"- {h}")
        lines.append("")

    if plan.alternative_hypotheses:
        lines += ["**Alternative Hypotheses:**", ""]
        for h in plan.alternative_hypotheses:
            lines.append(f"- {h}")
        lines.append("")

    if plan.expected_outcomes:
        lines += ["**Expected Outcomes:**", ""]
        for o in plan.expected_outcomes:
            lines.append(f"- {o}")
        lines.append("")

    # Literature Review
    lit = plan.literature_result
    lines += [
        f"## 2. Literature Review",
        f"",
        f"**Novelty Signal:** {lit.novelty_signal.value.replace('_', ' ').title()}",
        f"",
    ]
    if lit.gap_analysis:
        lines += [f"**Gap Analysis:**", f"", f"{lit.gap_analysis}", f""]

    if lit.references:
        lines += ["**Key References:**", ""]
        for i, ref in enumerate(lit.references, 1):
            authors = ", ".join(ref.authors[:3])
            if len(ref.authors) > 3:
                authors += " et al."
            lines.append(f"{i}. **{ref.title}**  ")
            lines.append(f"   {authors} ({ref.year}) — {ref.source.title()}")
            if ref.abstract_summary:
                lines.append(f"   > {ref.abstract_summary}")
            if ref.url and ref.url != "https://placeholder.url":
                lines.append(f"   [View Paper]({ref.url})")
            lines.append("")

    # Protocol
    lines += [
        f"## 3. Experimental Protocol",
        f"",
    ]
    for step in plan.protocol_steps:
        lines += [
            f"### Step {step.step_number}: {step.title}",
            f"",
            f"{step.description}",
            f"",
            f"- **Duration:** {step.duration_minutes} minutes",
        ]
        if step.equipment_needed:
            lines.append(f"- **Equipment:** {', '.join(step.equipment_needed)}")
        if step.notes:
            lines.append(f"- **Notes:** {step.notes}")
        lines.append("")

    # Materials
    lines += [
        f"## 4. Materials & Reagents",
        f"",
        f"| # | Name | Supplier | Catalog # | Quantity | Unit Cost | Total Cost | Hazard |",
        f"|---|------|----------|-----------|----------|-----------|------------|--------|",
    ]
    for i, m in enumerate(plan.materials, 1):
        hazard = m.hazard_class or "—"
        lines.append(
            f"| {i} | {m.name} | {m.supplier} | {m.catalog_number} | "
            f"{m.quantity} | ${m.unit_cost_usd:.2f} | ${m.total_cost_usd:.2f} | {hazard} |"
        )
    lines.append("")

    # Budget
    budget = plan.budget
    lines += [
        f"## 5. Budget",
        f"",
        f"| Category | Description | Cost (USD) |",
        f"|----------|-------------|------------|",
    ]
    for line in budget.line_items:
        lines.append(f"| {line.category.title()} | {line.description} | ${line.cost_usd:.2f} |")
    lines += [
        f"| **TOTAL** | | **${budget.grand_total_usd:.2f}** |",
        f"",
        f"*{budget.currency_note}*",
        f"",
    ]

    # Timeline
    lines += [
        f"## 6. Timeline",
        f"",
    ]
    for i, phase in enumerate(plan.timeline, 1):
        lines += [
            f"### Phase {i}: {phase.phase_name} ({phase.duration_days} days)",
            f"",
        ]
        if phase.milestone:
            lines.append(f"**Milestone:** {phase.milestone}  ")
        if phase.depends_on:
            lines.append(f"**Depends on:** {', '.join(phase.depends_on)}  ")
        lines.append("")
        for task in phase.tasks:
            lines.append(f"- {task}")
        lines.append("")

    # Validation
    if plan.validation:
        v = plan.validation
        lines += [
            f"## 7. Validation & Statistics",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Primary metric | {v.primary_metric} |",
            f"| Success threshold | {v.success_threshold} |",
            f"| Statistical test | {v.statistical_test} |",
        ]
        if v.sample_size_per_group:
            lines.append(f"| Sample size / group | {v.sample_size_per_group} |")
        if v.power:
            lines.append(f"| Statistical power | {v.power * 100:.0f}% |")
        if v.alpha:
            lines.append(f"| Alpha (significance) | {v.alpha} |")
        if v.effect_size_estimate:
            lines.append(f"| Effect size | {v.effect_size_estimate} |")
        lines.append("")
        if v.controls:
            lines += ["**Controls:**", ""]
            for c in v.controls:
                lines.append(f"- {c}")
            lines.append("")

    # Biosafety
    if plan.biosafety:
        bio = plan.biosafety
        lines += [
            f"## 8. Biosafety Assessment",
            f"",
            f"**Biosafety Level:** {bio.level.value}",
            f"",
        ]
        if bio.hazardous_materials:
            lines += ["**Hazardous Materials:**", ""]
            for h in bio.hazardous_materials:
                lines.append(f"- {h}")
            lines.append("")
        if bio.required_ppe:
            lines += ["**Required PPE:**", ""]
            for p in bio.required_ppe:
                lines.append(f"- {p}")
            lines.append("")
        if bio.waste_disposal_protocol:
            lines += [f"**Waste Disposal:** {bio.waste_disposal_protocol}", ""]
        if bio.special_requirements:
            lines += ["**Special Requirements:**", ""]
            for r in bio.special_requirements:
                lines.append(f"- {r}")
            lines.append("")
        if bio.regulatory_notes:
            lines += [f"**Regulatory Notes:** {bio.regulatory_notes}", ""]

    # Risks
    if plan.risks:
        lines += [
            f"## 9. Risk Assessment",
            f"",
            f"| Risk | Severity | Likelihood | Mitigation |",
            f"|------|----------|------------|------------|",
        ]
        for r in plan.risks:
            lines.append(
                f"| {r.description} | {r.severity.title()} | {r.likelihood.title()} | {r.mitigation} |"
            )
        lines.append("")

    # Footer
    lines += [
        f"---",
        f"",
        f"*Report generated by **The AI Scientist** — Fulcrum Science × Hack-Nation MIT Hackathon.*  ",
        f"*This plan was produced using LangGraph + Groq (llama-3.3-70b-versatile) with real-time literature QC via PubMed & Semantic Scholar.*",
        f"",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/api/report/{plan_id}", response_model=ReportResponse)
async def get_report(
    plan_id: UUID,
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    cache: Annotated[ICache, Depends(get_cache)],
) -> ReportResponse:
    """Generate and return a Markdown report for a saved experiment plan."""
    cache_key = f"report:{plan_id}"
    cached = await cache.get(cache_key)
    if cached:
        import json as _json
        return ReportResponse(**_json.loads(cached))

    plan = await repo.get(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found.",
        )

    markdown = generate_markdown_report(plan)
    title = (plan.refined_hypothesis or plan.hypothesis)[:80]
    word_count = len(markdown.split())

    result = ReportResponse(
        plan_id=str(plan_id),
        title=title,
        markdown=markdown,
        word_count=word_count,
        created_at=datetime.datetime.utcnow().isoformat(),
    )

    await cache.set(cache_key, result.model_dump_json(), ttl_seconds=3600)
    return result


@router.get("/api/report/{plan_id}/download")
async def download_report(
    plan_id: UUID,
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    cache: Annotated[ICache, Depends(get_cache)],
) -> PlainTextResponse:
    """Return the report as a downloadable Markdown text file."""
    cache_key = f"report:{plan_id}"
    plan = await repo.get(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found.",
        )

    markdown = generate_markdown_report(plan)
    filename = f"experiment_report_{str(plan_id)[:8]}.md"

    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
