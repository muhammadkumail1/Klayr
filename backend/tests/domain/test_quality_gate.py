"""
Quality gate unit tests.
"""
from __future__ import annotations

import pytest

from domain.pipeline.quality_gate import compute_quality_score, validate_plan
from domain.entities.experiment import (
    Budget,
    BudgetLine,
    ExperimentPlan,
    ProtocolStep,
    TimelinePhase,
)


class TestValidatePlan:
    def test_valid_plan_has_no_errors(self, sample_plan):
        errors = validate_plan(sample_plan)
        # Allow biosafety warning only
        hard_errors = [e for e in errors if not e.startswith("WARNING")]
        assert hard_errors == [], f"Unexpected errors: {hard_errors}"

    def test_empty_protocol_steps_flagged(self, sample_plan):
        sample_plan.protocol_steps = []
        errors = validate_plan(sample_plan)
        assert any("Protocol" in e for e in errors)

    def test_too_few_steps_flagged(self, sample_plan):
        sample_plan.protocol_steps = [
            ProtocolStep(step_number=1, title="A", description="D", duration_minutes=10),
            ProtocolStep(step_number=2, title="B", description="D", duration_minutes=10),
        ]
        errors = validate_plan(sample_plan)
        assert any("minimum" in e.lower() for e in errors)

    def test_misnumbered_steps_flagged(self, sample_plan):
        sample_plan.protocol_steps[2] = ProtocolStep(
            step_number=99, title="X", description="D", duration_minutes=10
        )
        errors = validate_plan(sample_plan)
        assert any("numbering" in e.lower() for e in errors)

    def test_empty_materials_flagged(self, sample_plan):
        sample_plan.materials = []
        errors = validate_plan(sample_plan)
        assert any("material" in e.lower() for e in errors)

    def test_missing_validation_flagged(self, sample_plan):
        sample_plan.validation = None
        errors = validate_plan(sample_plan)
        assert any("validation" in e.lower() for e in errors)

    def test_budget_mismatch_flagged(self, sample_plan):
        sample_plan.budget = Budget(
            line_items=[BudgetLine(category="reagents", description="all", cost_usd=100.0)],
            grand_total_usd=9999.0,   # intentional mismatch
        )
        # Force the mismatch by bypassing the model_validator
        object.__setattr__(sample_plan.budget, "grand_total_usd", 9999.0)
        errors = validate_plan(sample_plan)
        assert any("budget" in e.lower() for e in errors)

    def test_unknown_timeline_dependency_flagged(self, sample_plan):
        sample_plan.timeline[1].depends_on = ["NonExistentPhase"]
        errors = validate_plan(sample_plan)
        assert any("depends on unknown" in e.lower() for e in errors)


class TestComputeQualityScore:
    def test_full_plan_scores_high(self, sample_plan):
        sample_plan.biosafety = sample_plan.biosafety  # already set
        score = compute_quality_score(sample_plan)
        assert score >= 70.0, f"Expected >=70, got {score}"

    def test_empty_plan_scores_low(self, sample_plan):
        sample_plan.protocol_steps = []
        sample_plan.materials = []
        sample_plan.timeline = []
        sample_plan.validation = None
        score = compute_quality_score(sample_plan)
        assert score < 50.0

    def test_score_is_capped_at_100(self, sample_plan):
        score = compute_quality_score(sample_plan)
        assert score <= 100.0
