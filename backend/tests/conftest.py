"""
Pytest configuration and shared fixtures.
All domain tests are self-contained — no running services required.
"""
from __future__ import annotations

import json
import uuid
import datetime
import pytest

from domain.entities.experiment import (
    Budget,
    BudgetLine,
    ExperimentDomain,
    ExperimentPlan,
    FeedbackEntry,
    LiteratureResult,
    NoveltySignal,
    Paper,
    ProtocolStep,
    Reagent,
    TimelinePhase,
    ValidationApproach,
)
from domain.ports.llm_client import ILLMClient
from domain.ports.lit_search import ILitSearch


# ---------------------------------------------------------------------------
# Mock implementations (zero external calls)
# ---------------------------------------------------------------------------

class MockLLM(ILLMClient):
    """Returns minimal valid JSON for any agent prompt based on system string keywords."""

    async def complete(self, system: str, prompt: str) -> str:
        sys_lower = system.lower()

        if "hypothesis" in sys_lower:
            return json.dumps({
                "refined_hypothesis": "If trehalose is added at 10% v/v, then HeLa cell viability after cryopreservation will exceed 85%, because trehalose stabilizes cell membranes during freeze-thaw cycles.",
                "experiment_domain": "cell_biology",
                "sub_hypotheses": ["Trehalose increases post-thaw viability vs DMSO"],
                "independent_variable": "cryoprotectant type",
                "dependent_variable": "post-thaw cell viability (%)",
                "proposed_mechanism": "membrane stabilization via hydrogen bonding",
                "alternative_hypotheses": ["DMSO provides equivalent protection", "Cell line is resistant to both"],
                "expected_outcomes": [">85% viability", "p<0.05 vs DMSO control", "No morphological changes"],
            })

        if "literature" in sys_lower or "reviewer" in sys_lower:
            return json.dumps({
                "novelty_signal": "similar_work_exists",
                "gap_analysis": "No direct comparison of trehalose vs DMSO in HeLa cells at 10% v/v has been published.",
                "methodological_insights": ["Use controlled-rate freezer", "Trypan blue exclusion for viability"],
                "references": [{
                    "title": "Trehalose as a cryoprotectant for mammalian cells",
                    "authors": ["Smith J", "Lee K"],
                    "year": 2021,
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                    "abstract_summary": "Study showing trehalose effectiveness.",
                    "source": "pubmed",
                    "relevance_note": "Directly relevant to hypothesis",
                }],
            })

        if "protocol" in sys_lower:
            return json.dumps({
                "steps": [
                    {"step_number": 1, "title": "Prepare cells", "description": "Culture HeLa cells to 80% confluence in DMEM + 10% FBS at 37°C, 5% CO2.", "duration_minutes": 1440, "equipment_needed": ["CO2 incubator", "T-75 flask"], "notes": None},
                    {"step_number": 2, "title": "Prepare cryoprotectant", "description": "Dissolve trehalose in PBS to 10% w/v, filter sterilize 0.22 µm.", "duration_minutes": 30, "equipment_needed": ["sterile filter", "biosafety cabinet"], "notes": None},
                    {"step_number": 3, "title": "Trypsinize cells", "description": "Remove medium, wash 1x PBS, add 2 mL 0.25% trypsin-EDTA, incubate 5 min 37°C.", "duration_minutes": 10, "equipment_needed": ["CO2 incubator"], "notes": None},
                    {"step_number": 4, "title": "Count cells", "description": "Resuspend in 8 mL DMEM, count via hemocytometer. Adjust to 1×10^6 cells/mL.", "duration_minutes": 20, "equipment_needed": ["hemocytometer", "microscope"], "notes": None},
                    {"step_number": 5, "title": "Freeze cells", "description": "Add cryoprotectant 1:1, transfer to cryovials, freeze at -1°C/min to -80°C.", "duration_minutes": 60, "equipment_needed": ["Mr. Frosty freezing container", "-80°C freezer"], "notes": "Critical: controlled rate freezing is essential"},
                    {"step_number": 6, "title": "Thaw cells", "description": "Transfer vials to 37°C water bath, thaw within 2 min, dilute 1:10 in warm DMEM.", "duration_minutes": 10, "equipment_needed": ["37°C water bath"], "notes": None},
                    {"step_number": 7, "title": "Assess viability", "description": "Mix 1:1 with 0.4% trypan blue, count viable (clear) vs non-viable (blue) cells.", "duration_minutes": 20, "equipment_needed": ["hemocytometer", "microscope"], "notes": None},
                    {"step_number": 8, "title": "Statistical analysis", "description": "Calculate mean viability ± SD for n=3 replicates. Run two-tailed t-test vs DMSO control.", "duration_minutes": 60, "equipment_needed": ["statistical software"], "notes": None},
                ]
            })

        if "procurement" in sys_lower or "materials" in sys_lower or "supply" in sys_lower:
            return json.dumps({
                "materials": [
                    {"name": "Trehalose dihydrate", "catalog_number": "T9449", "supplier": "Sigma-Aldrich", "quantity": "25 g", "unit_cost_usd": 45.0, "total_cost_usd": 45.0, "hazard_class": None},
                    {"name": "DMSO (cell culture grade)", "catalog_number": "D2650", "supplier": "Sigma-Aldrich", "quantity": "100 mL", "unit_cost_usd": 38.0, "total_cost_usd": 38.0, "hazard_class": "GHS07"},
                    {"name": "HeLa cells (ATCC CCL-2)", "catalog_number": "CCL-2", "supplier": "ATCC", "quantity": "1 vial", "unit_cost_usd": 350.0, "total_cost_usd": 350.0, "hazard_class": "BSL-2"},
                ]
            })

        if "finance" in sys_lower or "budget" in sys_lower:
            return json.dumps({
                "line_items": [
                    {"category": "reagents", "description": "All reagents and consumables", "cost_usd": 433.0},
                    {"category": "personnel", "description": "Technician time (20 hrs @ $35/hr)", "cost_usd": 700.0},
                    {"category": "overhead", "description": "26% IDC on direct costs", "cost_usd": 294.58},
                ],
                "grand_total_usd": 1427.58,
                "currency_note": "All costs in USD",
            })

        if "project manager" in sys_lower or "timeline" in sys_lower:
            return json.dumps({
                "phases": [
                    {"phase_name": "Procurement & Setup", "duration_days": 7, "tasks": ["Order reagents", "Prepare cryovials", "Validate equipment"], "depends_on": [], "milestone": "All materials in hand"},
                    {"phase_name": "Main Experiment", "duration_days": 5, "tasks": ["Culture HeLa cells", "Freeze/thaw experiment", "Viability assay"], "depends_on": ["Procurement & Setup"], "milestone": "Raw viability data collected"},
                    {"phase_name": "Data Analysis", "duration_days": 3, "tasks": ["Statistical analysis", "Generate figures", "Interpret results"], "depends_on": ["Main Experiment"], "milestone": "Analysis complete"},
                    {"phase_name": "Writeup", "duration_days": 3, "tasks": ["Draft methods", "Draft results", "Peer review"], "depends_on": ["Data Analysis"], "milestone": "Report submitted"},
                ]
            })

        if "biostatistician" in sys_lower or "validation" in sys_lower:
            return json.dumps({
                "primary_metric": "Post-thaw cell viability (%)",
                "success_threshold": ">85% viability, p<0.05 vs DMSO control",
                "statistical_test": "Two-tailed Student's t-test",
                "controls": ["DMSO 10% v/v (positive control)", "No cryoprotectant (negative control)"],
                "sample_size_per_group": 3,
                "power": 0.80,
                "alpha": 0.05,
                "effect_size_estimate": "Cohen d=0.8 (large effect) based on prior literature",
            })

        if "biosafety" in sys_lower or "safety officer" in sys_lower:
            return json.dumps({
                "level": "BSL-2",
                "hazardous_materials": ["HeLa cells (human-derived)", "DMSO (irritant)"],
                "required_ppe": ["nitrile gloves (double)", "lab coat", "safety goggles"],
                "waste_disposal_protocol": "Autoclave biological waste; chemical waste via licensed contractor",
                "special_requirements": ["Class II biosafety cabinet for cell work", "IBC registration for HeLa cells"],
                "regulatory_notes": "IBC approval required for use of human-derived cell lines",
            })

        if "risk" in sys_lower:
            return json.dumps({
                "risks": [
                    {"description": "Cell contamination during thaw", "severity": "high", "likelihood": "medium", "mitigation": "Use sterile technique throughout; test mycoplasma before experiment"},
                    {"description": "Inconsistent freezing rate", "severity": "high", "likelihood": "low", "mitigation": "Use calibrated Mr. Frosty or controlled-rate freezer; log temperature curve"},
                    {"description": "Trypan blue undercount due to aggregates", "severity": "medium", "likelihood": "medium", "mitigation": "Vortex gently before counting; use automated cell counter as backup"},
                    {"description": "Reagent supply delay (CATALOG_TBD items)", "severity": "medium", "likelihood": "low", "mitigation": "Order 2 weeks in advance; identify alternative supplier"},
                ]
            })

        return "{}"


class MockLitSearch(ILitSearch):
    async def search(self, query: str) -> list[Paper]:
        return [
            Paper(
                title="Trehalose as a cryoprotectant for mammalian cells",
                authors=["Smith J", "Lee K"],
                year=2021,
                url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                abstract="Trehalose stabilizes cell membranes during cryopreservation...",
                abstract_summary="Trehalose effectively protects mammalian cells during freezing.",
                source="pubmed",
                relevance_note="",
            )
        ]


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm() -> MockLLM:
    return MockLLM()


@pytest.fixture
def mock_lit_search() -> MockLitSearch:
    return MockLitSearch()


@pytest.fixture
def sample_plan() -> ExperimentPlan:
    """A fully populated ExperimentPlan for quality gate and parser tests."""
    return ExperimentPlan(
        plan_id=uuid.uuid4(),
        hypothesis="Does trehalose preserve HeLa cells better than DMSO?",
        refined_hypothesis="If trehalose is used at 10% v/v, then post-thaw HeLa cell viability will exceed 85%, because trehalose stabilizes membranes.",
        experiment_domain=ExperimentDomain.CELL_BIOLOGY,
        sub_hypotheses=["Trehalose > DMSO for viability", "No morphological differences"],
        alternative_hypotheses=["DMSO is equivalent", "Cell line is insensitive"],
        expected_outcomes=[">85% viability", "p<0.05", "Intact morphology"],
        literature_result=LiteratureResult(
            novelty_signal=NoveltySignal.SIMILAR_EXISTS,
            gap_analysis="No direct HeLa comparison at 10% v/v published.",
            references=[
                Paper(title="Trehalose cryoprotection", authors=["Smith J"], year=2021,
                      url="https://pubmed.ncbi.nlm.nih.gov/1/", relevance_note=""),
            ],
        ),
        protocol_steps=[
            ProtocolStep(step_number=i, title=f"Step {i}", description=f"Detailed description for step {i} with exact conditions.", duration_minutes=30, equipment_needed=["incubator"])
            for i in range(1, 9)
        ],
        materials=[
            Reagent(name="Trehalose", catalog_number="T9449", supplier="Sigma-Aldrich", quantity="25g", unit_cost_usd=45.0, total_cost_usd=45.0),
            Reagent(name="DMSO", catalog_number="D2650", supplier="Sigma-Aldrich", quantity="100mL", unit_cost_usd=38.0, total_cost_usd=38.0),
        ],
        budget=Budget(
            line_items=[
                BudgetLine(category="reagents", description="All reagents", cost_usd=83.0),
                BudgetLine(category="personnel", description="Tech time", cost_usd=700.0),
            ],
            grand_total_usd=783.0,
        ),
        timeline=[
            TimelinePhase(phase_name="Procurement", duration_days=7, tasks=["Order reagents", "Setup equipment", "Validate protocols"], depends_on=[]),
            TimelinePhase(phase_name="Experiment", duration_days=5, tasks=["Culture cells", "Freeze/thaw", "Viability assay"], depends_on=["Procurement"], milestone="Data collected"),
            TimelinePhase(phase_name="Analysis", duration_days=3, tasks=["Stats", "Figures", "Writeup"], depends_on=["Experiment"], milestone="Report complete"),
        ],
        validation=ValidationApproach(
            primary_metric="Post-thaw viability %",
            success_threshold=">85%, p<0.05",
            statistical_test="Two-tailed t-test",
            controls=["DMSO positive control", "No cryoprotectant negative control"],
            sample_size_per_group=3,
            power=0.80,
            alpha=0.05,
        ),
        created_at=datetime.datetime.utcnow(),
    )
