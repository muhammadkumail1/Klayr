"""
Domain Entities — pure Pydantic v2 models.
Zero framework imports. Zero infrastructure imports.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class NoveltySignal(str, Enum):
    NOT_FOUND = "not_found"
    SIMILAR_EXISTS = "similar_work_exists"
    EXACT_MATCH = "exact_match_found"


class BiosafetyLevel(str, Enum):
    BSL1 = "BSL-1"
    BSL2 = "BSL-2"
    BSL3 = "BSL-3"
    BSL4 = "BSL-4"
    UNKNOWN = "unknown"


class ExperimentDomain(str, Enum):
    CELL_BIOLOGY = "cell_biology"
    MOLECULAR_BIOLOGY = "molecular_biology"
    BIOCHEMISTRY = "biochemistry"
    MICROBIOLOGY = "microbiology"
    DIAGNOSTICS = "diagnostics"
    PHARMACOLOGY = "pharmacology"
    NEUROSCIENCE = "neuroscience"
    CHEMISTRY = "chemistry"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Literature
# ---------------------------------------------------------------------------

class Paper(BaseModel):
    title: str
    authors: list[str]
    year: int
    url: str
    abstract: Optional[str] = None
    abstract_summary: Optional[str] = None   # LLM-generated 2–3 sentence summary
    source: str = "unknown"                  # "pubmed" | "semantic_scholar"
    relevance_note: str = ""                 # temp DOI storage; cleared after dedup


class LiteratureResult(BaseModel):
    novelty_signal: NoveltySignal
    gap_analysis: str = ""          # What is missing in current literature
    references: list[Paper] = Field(default_factory=list, max_length=3)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class ProtocolStep(BaseModel):
    step_number: int
    title: str
    description: str
    duration_minutes: int
    equipment_needed: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Materials & Budget
# ---------------------------------------------------------------------------

class Reagent(BaseModel):
    name: str
    catalog_number: str             # "CATALOG_TBD" when unknown
    supplier: str                   # Sigma-Aldrich | Thermo Fisher | etc.
    quantity: str
    unit_cost_usd: float
    total_cost_usd: float
    hazard_class: Optional[str] = None   # GHS hazard class if applicable


class BudgetLine(BaseModel):
    category: str    # "reagents" | "equipment" | "personnel" | "overhead"
    description: str
    cost_usd: float


class Budget(BaseModel):
    line_items: list[BudgetLine]
    grand_total_usd: float
    currency_note: str = "All costs in USD, estimates based on current catalog prices"

    @model_validator(mode="after")
    def _check_total(self) -> "Budget":
        calculated = round(sum(li.cost_usd for li in self.line_items), 2)
        if abs(calculated - self.grand_total_usd) > 1.0:
            # Correct silently rather than raise — LLM outputs are approximate
            self.grand_total_usd = calculated
        return self


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelinePhase(BaseModel):
    phase_name: str
    duration_days: int
    tasks: list[str]
    depends_on: list[str] = Field(default_factory=list)
    milestone: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation & Statistics
# ---------------------------------------------------------------------------

class ValidationApproach(BaseModel):
    primary_metric: str
    success_threshold: str
    statistical_test: str
    controls: list[str]
    sample_size_per_group: Optional[int] = None
    power: Optional[float] = None        # e.g. 0.80
    alpha: Optional[float] = None        # e.g. 0.05
    effect_size_estimate: Optional[str] = None


# ---------------------------------------------------------------------------
# Biosafety
# ---------------------------------------------------------------------------

class BiosafetyAssessment(BaseModel):
    level: BiosafetyLevel
    hazardous_materials: list[str] = Field(default_factory=list)
    required_ppe: list[str] = Field(default_factory=list)
    waste_disposal_protocol: str = ""
    special_requirements: list[str] = Field(default_factory=list)
    regulatory_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------

class RiskFactor(BaseModel):
    description: str
    severity: str          # "low" | "medium" | "high"
    likelihood: str        # "low" | "medium" | "high"
    mitigation: str


# ---------------------------------------------------------------------------
# Core Plan
# ---------------------------------------------------------------------------

class ExperimentPlan(BaseModel):
    plan_id: UUID
    hypothesis: str                   # raw user input
    refined_hypothesis: str           # LLM-refined
    experiment_domain: ExperimentDomain = ExperimentDomain.OTHER
    sub_hypotheses: list[str] = Field(default_factory=list)
    literature_result: LiteratureResult
    protocol_steps: list[ProtocolStep]
    materials: list[Reagent]
    budget: Budget
    timeline: list[TimelinePhase]
    validation: ValidationApproach
    biosafety: Optional[BiosafetyAssessment] = None
    risks: list[RiskFactor] = Field(default_factory=list)
    expected_outcomes: list[str] = Field(default_factory=list)
    alternative_hypotheses: list[str] = Field(default_factory=list)
    quality_score: Optional[float] = None   # 0–100 computed by quality_gate
    created_at: datetime.datetime
    feedback_incorporated: bool = False


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackEntry(BaseModel):
    feedback_id: UUID
    plan_id: UUID
    section: str            # "protocol" | "materials" | "budget" | "timeline" | "validation"
    original_content: str
    correction: str
    experiment_domain: str  # free-form tag, e.g. "cell_biology"
    created_at: datetime.datetime
