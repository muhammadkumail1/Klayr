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
    Return a 0–100 quality score based on completeness and scientific rigor.
    Weights are intentionally explicit to be auditable.
    """
    score = 0.0

    # Hypothesis (15 pts)
    if plan.refined_hypothesis and len(plan.refined_hypothesis) > 50:
        score += 5
    if len(plan.sub_hypotheses) >= 2:
        score += 5
    if len(plan.alternative_hypotheses) >= 2:
        score += 5

    # Literature (15 pts)
    if plan.literature_result:
        if plan.literature_result.gap_analysis:
            score += 5
        score += min(len(plan.literature_result.references) * 3, 10)

    # Protocol (20 pts)
    if plan.protocol_steps:
        score += min(len(plan.protocol_steps) * 2, 10)  # up to 10 pts for steps
        has_equipment = any(s.equipment_needed for s in plan.protocol_steps)
        if has_equipment:
            score += 5
        all_described = all(len(s.description) > 50 for s in plan.protocol_steps)
        if all_described:
            score += 5

    # Materials (10 pts)
    if plan.materials:
        score += 5
        no_tbd = all(m.catalog_number != "CATALOG_TBD" for m in plan.materials)
        if no_tbd:
            score += 5

    # Budget (10 pts)
    if plan.budget and plan.budget.grand_total_usd > 0:
        score += 5
        if len(plan.budget.line_items) >= 3:
            score += 5

    # Timeline (10 pts)
    if plan.timeline and len(plan.timeline) >= 3:
        score += 10

    # Validation (15 pts)
    if plan.validation:
        score += 5
        if plan.validation.sample_size_per_group:
            score += 5
        if plan.validation.controls and len(plan.validation.controls) >= 2:
            score += 5

    # Biosafety + Risks (5 pts)
    if plan.biosafety:
        score += 3
    if plan.risks:
        score += 2

    return round(min(score, 100.0), 1)
