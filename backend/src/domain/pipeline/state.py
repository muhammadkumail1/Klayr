"""
Pipeline state definition.
TypedDict keeps LangGraph state fully typed without leaking framework objects.
"""
from __future__ import annotations

from typing import Callable, Coroutine, Optional, TypedDict

from domain.entities.experiment import (
    BiosafetyAssessment,
    Budget,
    ExperimentDomain,
    ExperimentPlan,
    FeedbackEntry,
    LiteratureResult,
    ProtocolStep,
    Reagent,
    RiskFactor,
    TimelinePhase,
    ValidationApproach,
)


class PipelineState(TypedDict, total=False):
    # --- Input ---
    raw_input: str

    # --- Hypothesis agent ---
    refined_hypothesis: str
    experiment_domain: ExperimentDomain
    sub_hypotheses: list[str]
    alternative_hypotheses: list[str]
    expected_outcomes: list[str]

    # --- Literature agent ---
    literature_result: Optional[LiteratureResult]

    # --- Protocol agent ---
    protocol_steps: Optional[list[ProtocolStep]]

    # --- Materials agent ---
    materials: Optional[list[Reagent]]

    # --- Budget agent ---
    budget: Optional[Budget]

    # --- Timeline agent ---
    timeline: Optional[list[TimelinePhase]]

    # --- Validation agent ---
    validation: Optional[ValidationApproach]

    # --- Biosafety agent ---
    biosafety: Optional[BiosafetyAssessment]

    # --- Risk agent ---
    risks: list[RiskFactor]

    # --- Feedback injection (few-shot loop) ---
    few_shot_examples: list[FeedbackEntry]

    # --- Bookkeeping ---
    errors: list[str]
    final_plan: Optional[ExperimentPlan]

    # --- Streaming hook (not serialized, injected at runtime only) ---
    # on_event: Optional[Callable[[dict], Coroutine]]   # excluded from TypedDict for LangGraph compat
