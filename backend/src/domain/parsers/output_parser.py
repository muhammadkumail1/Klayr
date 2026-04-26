"""
Output parsers — pure functions that parse LLM JSON responses into typed domain models.

Rules:
1. Strip markdown fences before parsing.
2. Validate via Pydantic.
3. On failure: log raw output + exception, return a safe default — never raise to the route.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from domain.entities.experiment import (
    BiosafetyAssessment,
    BiosafetyLevel,
    Budget,
    BudgetLine,
    ExperimentDomain,
    LiteratureResult,
    NoveltySignal,
    Paper,
    ProtocolStep,
    Reagent,
    RiskFactor,
    TimelinePhase,
    ValidationApproach,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean(raw: str) -> str:
    """Strip markdown code fences and leading/trailing whitespace."""
    return (
        raw.replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )


def _loads(raw: str) -> Optional[dict | list]:
    cleaned = _clean(raw)
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------

def parse_hypothesis(raw: str) -> tuple[str, ExperimentDomain, list[str], list[str], list[str]]:
    """Returns (refined_hypothesis, domain, sub_hypotheses, alternative_hypotheses, expected_outcomes)."""
    try:
        data = _loads(raw)
        domain = ExperimentDomain(data.get("experiment_domain", "other"))
        return (
            data["refined_hypothesis"],
            domain,
            data.get("sub_hypotheses", []),
            data.get("alternative_hypotheses", []),
            data.get("expected_outcomes", []),
        )
    except Exception as exc:
        logger.error("hypothesis parse failed: %s\nRaw: %.300s", exc, raw)
        return raw, ExperimentDomain.OTHER, [], [], []


# ---------------------------------------------------------------------------
# Literature
# ---------------------------------------------------------------------------

def parse_literature(raw: str) -> LiteratureResult:
    try:
        data = _loads(raw)
        papers = [
            Paper(
                title=p.get("title", ""),
                authors=p.get("authors", []),
                year=p.get("year") or 0,
                url=p.get("url", ""),
                abstract_summary=p.get("abstract_summary"),
                source=p.get("source", "unknown"),
                relevance_note=p.get("relevance_note", ""),
            )
            for p in data.get("references", [])
        ]
        return LiteratureResult(
            novelty_signal=NoveltySignal(data.get("novelty_signal", "not_found")),
            gap_analysis=data.get("gap_analysis", ""),
            references=papers[:3],
        )
    except Exception as exc:
        logger.error("literature parse failed: %s\nRaw: %.300s", exc, raw)
        return LiteratureResult(
            novelty_signal=NoveltySignal.NOT_FOUND,
            gap_analysis="",
            references=[],
        )


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

def parse_protocol(raw: str) -> list[ProtocolStep]:
    try:
        data = _loads(raw)
        return [
            ProtocolStep(
                step_number=s["step_number"],
                title=s["title"],
                description=s["description"],
                duration_minutes=s["duration_minutes"],
                equipment_needed=s.get("equipment_needed", []),
                notes=s.get("notes"),
            )
            for s in data["steps"]
        ]
    except Exception as exc:
        logger.error("protocol parse failed: %s\nRaw: %.300s", exc, raw)
        return []


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def parse_materials(raw: str) -> list[Reagent]:
    try:
        data = _loads(raw)
        return [
            Reagent(
                name=m["name"],
                catalog_number=m.get("catalog_number", "CATALOG_TBD"),
                supplier=m.get("supplier", "Unknown"),
                quantity=m.get("quantity", "1 unit"),
                unit_cost_usd=float(m.get("unit_cost_usd", 0.0)),
                total_cost_usd=float(m.get("total_cost_usd", 0.0)),
                hazard_class=m.get("hazard_class"),
            )
            for m in data["materials"]
        ]
    except Exception as exc:
        logger.error("materials parse failed: %s\nRaw: %.300s", exc, raw)
        return []


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

def parse_budget(raw: str) -> Optional[Budget]:
    try:
        data = _loads(raw)
        line_items = [
            BudgetLine(
                category=li["category"],
                description=li["description"],
                cost_usd=float(li["cost_usd"]),
            )
            for li in data["line_items"]
        ]
        return Budget(
            line_items=line_items,
            grand_total_usd=float(data.get("grand_total_usd", 0.0)),
            currency_note=data.get(
                "currency_note",
                "All costs in USD, estimates based on current catalog prices",
            ),
        )
    except Exception as exc:
        logger.error("budget parse failed: %s\nRaw: %.300s", exc, raw)
        return None


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

def parse_timeline(raw: str) -> list[TimelinePhase]:
    try:
        data = _loads(raw)
        phases = data.get("phases") or data  # some LLMs return the list directly
        if isinstance(phases, list):
            return [
                TimelinePhase(
                    phase_name=p["phase_name"],
                    duration_days=p["duration_days"],
                    tasks=p.get("tasks", []),
                    depends_on=p.get("depends_on", []),
                    milestone=p.get("milestone"),
                )
                for p in phases
            ]
        return []
    except Exception as exc:
        logger.error("timeline parse failed: %s\nRaw: %.300s", exc, raw)
        return []


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def parse_validation(raw: str) -> Optional[ValidationApproach]:
    try:
        data = _loads(raw)
        return ValidationApproach(
            primary_metric=data["primary_metric"],
            success_threshold=data["success_threshold"],
            statistical_test=data["statistical_test"],
            controls=data.get("controls", []),
            sample_size_per_group=data.get("sample_size_per_group"),
            power=data.get("power"),
            alpha=data.get("alpha"),
            effect_size_estimate=data.get("effect_size_estimate"),
        )
    except Exception as exc:
        logger.error("validation parse failed: %s\nRaw: %.300s", exc, raw)
        return None


# ---------------------------------------------------------------------------
# Biosafety
# ---------------------------------------------------------------------------

def parse_biosafety(raw: str) -> Optional[BiosafetyAssessment]:
    try:
        data = _loads(raw)
        return BiosafetyAssessment(
            level=BiosafetyLevel(data.get("level", "unknown")),
            hazardous_materials=data.get("hazardous_materials", []),
            required_ppe=data.get("required_ppe", []),
            waste_disposal_protocol=data.get("waste_disposal_protocol", ""),
            special_requirements=data.get("special_requirements", []),
            regulatory_notes=data.get("regulatory_notes"),
        )
    except Exception as exc:
        logger.error("biosafety parse failed: %s\nRaw: %.300s", exc, raw)
        return None


# ---------------------------------------------------------------------------
# Risks
# ---------------------------------------------------------------------------

def parse_risks(raw: str) -> list[RiskFactor]:
    try:
        data = _loads(raw)
        return [
            RiskFactor(
                description=r["description"],
                severity=r.get("severity", "medium"),
                likelihood=r.get("likelihood", "medium"),
                mitigation=r["mitigation"],
            )
            for r in data.get("risks", [])
        ]
    except Exception as exc:
        logger.error("risks parse failed: %s\nRaw: %.300s", exc, raw)
        return []
