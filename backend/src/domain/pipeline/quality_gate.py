"""
Quality gate — validates a completed ExperimentPlan against scientific best practices.

Returns a list of error strings. An empty list means the plan passed.
Also computes a quality_score (0–100) based on completeness and rigor.

Pure domain logic — no I/O, no framework imports.
"""
from __future__ import annotations

import math
from domain.entities.experiment import ExperimentPlan


def validate_plan(plan: ExperimentPlan) -> list[str]:
    """Run all validation checks. Returns list of error messages (empty = pass)."""
    errors: list[str] = []

    # ------------------------------------------------------------------
    # Hypothesis
    # ------------------------------------------------------------------
    if not plan.refined_hypothesis or len(plan.refined_hypothesis) < 20:
        errors.append("Refined hypothesis is too short or missing.")
    if not plan.sub_hypotheses:
        errors.append("No sub-hypotheses decomposed from the main hypothesis.")

    # ------------------------------------------------------------------
    # Literature
    # ------------------------------------------------------------------
    if plan.literature_result is None:
        errors.append("Literature result is missing.")
    else:
        if not plan.literature_result.gap_analysis:
            errors.append("Literature gap analysis is empty.")

    # ------------------------------------------------------------------
    # Protocol
    # ------------------------------------------------------------------
    if not plan.protocol_steps:
        errors.append("Protocol has no steps.")
    else:
        if len(plan.protocol_steps) < 3:
            errors.append(
                f"Protocol has only {len(plan.protocol_steps)} step(s); minimum is 3."
            )
        # Check sequential numbering
        for idx, step in enumerate(plan.protocol_steps):
            if step.step_number != idx + 1:
                errors.append(
                    f"Protocol step numbering is inconsistent at position {idx + 1} "
                    f"(expected {idx + 1}, got {step.step_number})."
                )
                break  # one numbering error is enough to flag
        # Ensure no step has zero duration
        zero_dur = [s.step_number for s in plan.protocol_steps if s.duration_minutes <= 0]
        if zero_dur:
            errors.append(f"Steps {zero_dur} have zero or negative duration.")

    # ------------------------------------------------------------------
    # Materials
    # ------------------------------------------------------------------
    if not plan.materials:
        errors.append("No materials listed.")
    else:
        tbd = [m.name for m in plan.materials if m.catalog_number == "CATALOG_TBD"]
        if len(tbd) > len(plan.materials) * 0.5:
            errors.append(
                f"{len(tbd)}/{len(plan.materials)} materials have unresolved "
                f"catalog numbers (>50% CATALOG_TBD)."
            )
        # Check for negative costs
        neg_cost = [m.name for m in plan.materials if m.total_cost_usd < 0]
        if neg_cost:
            errors.append(f"Negative cost on material(s): {neg_cost}.")

    # ------------------------------------------------------------------
    # Budget
    # ------------------------------------------------------------------
    if plan.budget is None:
        errors.append("Budget is missing.")
    else:
        if plan.budget.grand_total_usd <= 0:
            errors.append("Budget grand total must be positive.")
        if not plan.budget.line_items:
            errors.append("Budget has no line items.")
        else:
            calculated = round(sum(li.cost_usd for li in plan.budget.line_items), 2)
            if abs(calculated - plan.budget.grand_total_usd) > 1.00:
                errors.append(
                    f"Budget line items sum to ${calculated:.2f} but grand_total_usd "
                    f"is ${plan.budget.grand_total_usd:.2f} (delta > $1.00)."
                )

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------
    if not plan.timeline:
        errors.append("Timeline has no phases.")
    else:
        if len(plan.timeline) < 2:
            errors.append("Timeline has fewer than 2 phases; likely incomplete.")
        # Check for circular depends_on references
        phase_names = {p.phase_name for p in plan.timeline}
        for phase in plan.timeline:
            unknown_deps = set(phase.depends_on) - phase_names - {phase.phase_name}
            if unknown_deps:
                errors.append(
                    f"Timeline phase '{phase.phase_name}' depends on unknown "
                    f"phases: {unknown_deps}."
                )

    # ------------------------------------------------------------------
    # Validation approach
    # ------------------------------------------------------------------
    if plan.validation is None:
        errors.append("Validation approach is missing.")
    else:
        if not plan.validation.primary_metric:
            errors.append("Validation: primary_metric is empty.")
        if not plan.validation.controls:
            errors.append("Validation: no controls defined.")
        if not plan.validation.statistical_test:
            errors.append("Validation: no statistical test specified.")

    # ------------------------------------------------------------------
    # Biosafety (warning-only — does not fail the plan)
    # ------------------------------------------------------------------
    if plan.biosafety is None:
        errors.append("WARNING: Biosafety assessment is missing.")

    return errors


def compute_quality_score(plan: ExperimentPlan) -> float:
    """
    Return a 0–100 quality score based on completeness AND scientific rigor.

    Scoring is intentionally differential — each dimension rewards depth beyond
    the bare minimum so plans actually spread across the 0–100 range.

    Dimensions and max points:
      Hypothesis depth       15 pts
      Literature rigor       20 pts
      Protocol thoroughness  20 pts
      Materials specificity  10 pts
      Budget granularity      5 pts
      Timeline completeness  10 pts
      Validation rigour      15 pts
      Safety & risk           5 pts
    ──────────────────────────────
    Total                   100 pts
    """
    score = 0.0

    # ── 1. Hypothesis depth (15 pts) ─────────────────────────────────────────
    hyp = plan.refined_hypothesis or ""
    # Length proxy for specificity: 50+ words → 4 pts, 100+ words → 6 pts
    hyp_words = len(hyp.split())
    score += min(hyp_words / 17, 6)                          # 0–6 pts
    # Sub-hypotheses: 1 pt each up to 4
    score += min(len(plan.sub_hypotheses), 4)                # 0–4 pts
    # Alternative hypotheses (scientific rigour): 1 pt each up to 3
    score += min(len(plan.alternative_hypotheses), 3)        # 0–3 pts
    # Expected outcomes listed
    if getattr(plan, "expected_outcomes", None):
        score += min(len(plan.expected_outcomes), 2)         # 0–2 pts

    # ── 2. Literature rigor (20 pts) ─────────────────────────────────────────
    if plan.literature_result:
        lit = plan.literature_result
        # References: 2 pts each, up to 10 pts (5 refs = max)
        score += min(len(lit.references) * 2, 10)            # 0–10 pts
        # Gap analysis depth: 50 words → 2 pts, 150 words → 6 pts
        gap_words = len((lit.gap_analysis or "").split())
        score += min(gap_words / 25, 6)                      # 0–6 pts
        # Novelty signal bonus
        novelty = str(getattr(lit, "novelty_signal", "")).lower()
        if "highly_novel" in novelty or "highly novel" in novelty:
            score += 4                                        # 4 pts
        elif "novel" in novelty and "incremental" not in novelty:
            score += 2                                        # 2 pts

    # ── 3. Protocol thoroughness (20 pts) ────────────────────────────────────
    steps = plan.protocol_steps or []
    if steps:
        # Step count: 1 pt per step, max 6 pts
        score += min(len(steps), 6)                          # 0–6 pts
        # Average description length: ≥ 100 words per step → 5 pts
        avg_desc = sum(len(s.description.split()) for s in steps) / len(steps)
        score += min(avg_desc / 20, 5)                       # 0–5 pts
        # Equipment specified in steps
        steps_with_equip = sum(1 for s in steps if s.equipment_needed)
        score += min(steps_with_equip / max(len(steps), 1) * 5, 5)  # 0–5 pts
        # Steps with notes (extra detail)
        steps_with_notes = sum(1 for s in steps if getattr(s, "notes", None))
        score += min(steps_with_notes, 4)                    # 0–4 pts

    # ── 4. Materials specificity (10 pts) ────────────────────────────────────
    mats = plan.materials or []
    if mats:
        # Catalog numbers resolved
        resolved = sum(1 for m in mats if m.catalog_number and m.catalog_number != "CATALOG_TBD")
        score += min(resolved / max(len(mats), 1) * 6, 6)   # 0–6 pts
        # Hazard class annotated
        hazard_annotated = sum(1 for m in mats if getattr(m, "hazard_class", None))
        score += min(hazard_annotated / max(len(mats), 1) * 4, 4)  # 0–4 pts

    # ── 5. Budget granularity (5 pts) ─────────────────────────────────────────
    if plan.budget and plan.budget.grand_total_usd > 0:
        items = plan.budget.line_items or []
        # 5+ distinct categories → full marks
        categories = {li.category for li in items}
        score += min(len(categories), 5)                     # 0–5 pts

    # ── 6. Timeline completeness (10 pts) ────────────────────────────────────
    phases = plan.timeline or []
    if phases:
        # Phase count: 2 pts each, max 6 pts
        score += min(len(phases) * 2, 6)                     # 0–6 pts
        # Milestones defined
        phases_with_milestone = sum(1 for p in phases if getattr(p, "milestone", None))
        score += min(phases_with_milestone, 2)               # 0–2 pts
        # Dependencies wired up
        phases_with_deps = sum(1 for p in phases if getattr(p, "depends_on", None))
        score += min(phases_with_deps, 2)                    # 0–2 pts

    # ── 7. Validation rigour (15 pts) ────────────────────────────────────────
    val = plan.validation
    if val:
        score += 2                                            # has validation
        if val.primary_metric:
            score += 2
        if val.statistical_test:
            score += 2
        if val.sample_size_per_group and val.sample_size_per_group > 0:
            score += 2
        if getattr(val, "power", None):
            score += 1
        if getattr(val, "alpha", None):
            score += 1
        if getattr(val, "effect_size_estimate", None):
            score += 1
        controls = val.controls or []
        score += min(len(controls), 4)                       # 0–4 pts

    # ── 8. Safety & risk (5 pts) ─────────────────────────────────────────────
    if plan.biosafety:
        bio = plan.biosafety
        score += 1
        if getattr(bio, "required_ppe", None):
            score += 1
        if getattr(bio, "waste_disposal_protocol", None):
            score += 1
    risks = plan.risks or []
    if risks:
        # Reward diversity: high + medium + low all present
        severities = {r.severity.lower() for r in risks}
        score += min(len(severities), 2)                     # 0–2 pts

    return round(min(score, 100.0), 1)
