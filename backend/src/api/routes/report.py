"""
GET /api/report/{plan_id}          — generate Markdown final report for a plan.
GET /api/report/{plan_id}/download — download as Markdown text file attachment.
GET /api/report/{plan_id}/pdf      — download as a styled PDF file.
"""
from __future__ import annotations

import datetime
import io
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
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


# ---------------------------------------------------------------------------
# PDF generator
# ---------------------------------------------------------------------------

def generate_pdf_report(plan, markdown: str) -> bytes:
    """Render the experiment plan as a styled PDF using fpdf2."""
    from fpdf import FPDF

    def _safe(text: str, max_len: int = 0) -> str:
        """Replace characters outside Latin-1 so Helvetica can render them."""
        replacements = {
            "\u2014": "--", "\u2013": "-", "\u2019": "'", "\u2018": "'",
            "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
            "\u00b0": " deg", "\u03bc": "u", "\u03b1": "alpha",
            "\u03b2": "beta", "\u03b3": "gamma",
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        # Strip anything still outside Latin-1
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        if max_len and len(text) > max_len:
            text = text[:max_len - 1] + "+"
        return text

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(15, 23, 42)   # dark navy
            self.rect(0, 0, 210, 18, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 11)
            self.set_xy(10, 4)
            self.cell(0, 10, "The AI Scientist -- Experiment Report", ln=False)
            self.set_text_color(0, 0, 0)
            self.ln(18)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, f"Page {self.page_no()} | Fulcrum Science x Hack-Nation MIT Hackathon | LangGraph + Groq", align="C")
            self.set_text_color(0, 0, 0)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 22, 15)
    pdf.add_page()

    # ── Helpers ──────────────────────────────────────────────────────────────
    def h1(text: str):
        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, _safe(text), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def h2(text: str):
        pdf.set_fill_color(30, 58, 138)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _safe(text), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    def h3(text: str):
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, _safe(text), ln=True)
        pdf.set_text_color(0, 0, 0)

    def body(text: str, indent: int = 0):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(15 + indent)
        pdf.multi_cell(0, 5, _safe(text))

    def bullet(text: str, indent: int = 5):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(15 + indent)
        pdf.multi_cell(0, 5, _safe(f"*  {text}"))

    def kv(key: str, value: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_x(15)
        pdf.cell(45, 5, _safe(key) + ":", ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _safe(str(value)))

    def rule():
        pdf.set_draw_color(200, 200, 200)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)

    # ── Cover ─────────────────────────────────────────────────────────────────
    title = (plan.refined_hypothesis or plan.hypothesis)[:90]
    h1(f"Experiment Report")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.multi_cell(0, 7, title)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    domain = plan.experiment_domain.value.replace("_", " ").title()
    score = f"{plan.quality_score:.1f}/100" if plan.quality_score else "N/A"
    generated = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    kv("Plan ID", str(plan.plan_id)[:18] + "...")
    kv("Domain", domain)
    kv("Quality Score", score)
    kv("Generated", generated)
    rule()

    # ── 1. Hypothesis ────────────────────────────────────────────────────────
    h2("1.  Hypothesis")
    kv("Original", plan.hypothesis)
    if plan.refined_hypothesis and plan.refined_hypothesis != plan.hypothesis:
        kv("Refined", plan.refined_hypothesis)
    pdf.ln(2)
    if plan.sub_hypotheses:
        h3("Sub-hypotheses")
        for h in plan.sub_hypotheses:
            bullet(h)
        pdf.ln(2)
    if plan.expected_outcomes:
        h3("Expected Outcomes")
        for o in plan.expected_outcomes:
            bullet(o)
        pdf.ln(2)

    # ── 2. Literature Review ─────────────────────────────────────────────────
    h2("2.  Literature Review")
    if plan.literature_result:
        lit = plan.literature_result
        signal = lit.novelty_signal.value.replace("_", " ").title() if hasattr(lit.novelty_signal, "value") else str(lit.novelty_signal).replace("_", " ").title()
        kv("Novelty Signal", signal)
        if lit.gap_analysis:
            body(lit.gap_analysis)
        if lit.references:
            h3("References")
            for p in lit.references:
                authors = ", ".join(p.authors[:2]) + (" et al." if len(p.authors) > 2 else "")
                bullet(f"{p.title} - {authors} ({p.year})")
    pdf.ln(2)

    # ── 3. Protocol ──────────────────────────────────────────────────────────
    h2("3.  Experimental Protocol")
    for step in plan.protocol_steps or []:
        h3(f"Step {step.step_number}: {step.title}")
        body(step.description, indent=3)
        kv("  Duration", f"{step.duration_minutes} min")
        if step.equipment_needed:
            kv("  Equipment", ", ".join(step.equipment_needed))
        if step.notes:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_x(18)
            pdf.set_text_color(150, 80, 0)
            pdf.multi_cell(0, 4, _safe(f"Note: {step.notes}"))
            pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    # ── 4. Materials ─────────────────────────────────────────────────────────
    h2("4.  Materials & Reagents")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    cols = [8, 55, 35, 25, 28, 28, 18]
    headers = ["#", "Name", "Supplier", "Catalog", "Qty", "Cost (USD)", "Hazard"]
    for w, hdr in zip(cols, headers):
        pdf.cell(w, 6, hdr, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 7)
    for i, m in enumerate(plan.materials or [], 1):
        row_fill = i % 2 == 0
        pdf.set_fill_color(248, 250, 252) if row_fill else pdf.set_fill_color(255, 255, 255)
        vals = [
            str(i), _safe(m.name[:28]), _safe(m.supplier[:18]), _safe((m.catalog_number or "-")[:12]),
            _safe(str(m.quantity)[:12]), f"${m.total_cost_usd:.2f}", _safe((m.hazard_class or "-")[:10]),
        ]
        for w, v in zip(cols, vals):
            pdf.cell(w, 5, v, border=1, fill=row_fill)
        pdf.ln()
    pdf.ln(3)

    # ── 5. Budget ────────────────────────────────────────────────────────────
    h2("5.  Budget Summary")
    if plan.budget:
        for item in plan.budget.line_items:
            bullet(f"{item.category.title()}: {item.description[:60]} -- ${item.cost_usd:,.2f}")
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 58, 138)
        pdf.cell(0, 7, f"Grand Total:  ${plan.budget.grand_total_usd:,.2f} USD", ln=True)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # ── 6. Timeline ──────────────────────────────────────────────────────────
    h2("6.  Timeline")
    for phase in plan.timeline or []:
        h3(f"{phase.phase_name}  ({phase.duration_days} days)")
        if phase.milestone:
            kv("  Milestone", phase.milestone)
        for t in phase.tasks:
            bullet(t, indent=8)
        pdf.ln(1)

    # ── 7. Validation ────────────────────────────────────────────────────────
    h2("7.  Validation & Statistics")
    if plan.validation:
        v = plan.validation
        kv("Primary Metric", v.primary_metric)
        kv("Success Threshold", v.success_threshold)
        kv("Statistical Test", v.statistical_test)
        if v.sample_size_per_group:
            kv("Sample Size / Group", str(v.sample_size_per_group))
        if v.power:
            kv("Power", f"{int(v.power * 100)}%")
        if v.effect_size_estimate:
            kv("Effect Size", v.effect_size_estimate)
        if v.controls:
            h3("Controls")
            for c in v.controls:
                bullet(c)
    pdf.ln(2)

    # ── 8. Biosafety ─────────────────────────────────────────────────────────
    h2("8.  Biosafety Assessment")
    if plan.biosafety:
        b = plan.biosafety
        kv("Biosafety Level", b.level)
        if b.hazardous_materials:
            h3("Hazardous Materials")
            for m in b.hazardous_materials:
                bullet(m)
        if b.required_ppe:
            h3("Required PPE")
            for p in b.required_ppe:
                bullet(p)
        if b.waste_disposal_protocol:
            h3("Waste Disposal")
            body(b.waste_disposal_protocol, indent=3)
        if b.regulatory_notes:
            kv("Regulatory Notes", b.regulatory_notes)
    pdf.ln(2)

    # ── 9. Risk Assessment ───────────────────────────────────────────────────
    h2("9.  Risk Assessment")
    for risk in plan.risks or []:
        pdf.set_font("Helvetica", "B", 9)
        sev_color = (185, 28, 28) if risk.severity.lower() == "high" else (161, 98, 7) if risk.severity.lower() == "medium" else (21, 128, 61)
        pdf.set_text_color(*sev_color)
        pdf.cell(0, 5, _safe(f"[{risk.severity.upper()}] {risk.description[:90]}"), ln=True)
        pdf.set_text_color(0, 0, 0)
        kv("  Likelihood", risk.likelihood)
        kv("  Mitigation", risk.mitigation[:100])
        pdf.ln(1)

    # ── Footer note ───────────────────────────────────────────────────────────
    rule()
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Generated by The AI Scientist | Fulcrum Science x Hack-Nation MIT Hackathon | LangGraph + Groq (llama-3.3-70b-versatile) | PubMed & Semantic Scholar")
    pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# GET /api/report/{plan_id}/pdf
# ---------------------------------------------------------------------------

@router.get("/api/report/{plan_id}/pdf")
async def download_report_pdf(
    plan_id: UUID,
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    cache: Annotated[ICache, Depends(get_cache)],
) -> Response:
    """Return the experiment report as a downloadable PDF."""
    plan = await repo.get(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found.",
        )

    # Reuse cached markdown if available (avoids double LLM calls)
    cache_key = f"report:{plan_id}"
    cached = await cache.get(cache_key)
    import json as _json
    markdown = _json.loads(cached)["markdown"] if cached else generate_markdown_report(plan)

    try:
        pdf_bytes = generate_pdf_report(plan, markdown)
    except Exception as exc:
        logger.exception("PDF generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        )

    filename = f"experiment_report_{str(plan_id)[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

