"""
Output parser unit tests — pure function tests, no I/O.
"""
from __future__ import annotations

import json
import pytest

from domain.parsers.output_parser import (
    parse_biosafety,
    parse_budget,
    parse_hypothesis,
    parse_literature,
    parse_materials,
    parse_protocol,
    parse_risks,
    parse_timeline,
    parse_validation,
)
from domain.entities.experiment import (
    BiosafetyLevel,
    ExperimentDomain,
    NoveltySignal,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(data: dict) -> str:
    return json.dumps(data)


def _fenced(data: dict) -> str:
    return f"```json\n{json.dumps(data)}\n```"


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------

class TestParseHypothesis:
    def test_valid_json(self):
        raw = _json({
            "refined_hypothesis": "If X then Y because Z.",
            "experiment_domain": "cell_biology",
            "sub_hypotheses": ["sub1"],
            "alternative_hypotheses": ["alt1", "alt2"],
            "expected_outcomes": ["outcome1"],
        })
        refined, domain, subs, alts, outcomes = parse_hypothesis(raw)
        assert refined == "If X then Y because Z."
        assert domain == ExperimentDomain.CELL_BIOLOGY
        assert subs == ["sub1"]

    def test_fenced_json_stripped(self):
        data = {"refined_hypothesis": "H", "experiment_domain": "other",
                "sub_hypotheses": [], "alternative_hypotheses": [], "expected_outcomes": []}
        refined, domain, _, _, _ = parse_hypothesis(_fenced(data))
        assert refined == "H"
        assert domain == ExperimentDomain.OTHER

    def test_invalid_json_returns_raw_input(self):
        refined, domain, _, _, _ = parse_hypothesis("not json at all {{{")
        assert "not json" in refined
        assert domain == ExperimentDomain.OTHER


# ---------------------------------------------------------------------------
# Literature
# ---------------------------------------------------------------------------

class TestParseLiterature:
    def test_valid_output(self):
        raw = _json({
            "novelty_signal": "similar_work_exists",
            "gap_analysis": "gap text",
            "references": [{
                "title": "Paper A", "authors": ["Author A"], "year": 2020,
                "url": "https://example.com", "abstract_summary": "Summary",
                "source": "pubmed", "relevance_note": "relevant",
            }],
        })
        result = parse_literature(raw)
        assert result.novelty_signal == NoveltySignal.SIMILAR_EXISTS
        assert result.gap_analysis == "gap text"
        assert len(result.references) == 1

    def test_invalid_json_returns_safe_default(self):
        result = parse_literature("broken {")
        assert result.novelty_signal == NoveltySignal.NOT_FOUND
        assert result.references == []

    def test_max_3_references_enforced(self):
        refs = [{"title": f"P{i}", "authors": [], "year": 2020, "url": "u",
                 "abstract_summary": None, "source": "s", "relevance_note": ""}
                for i in range(10)]
        raw = _json({"novelty_signal": "not_found", "gap_analysis": "", "references": refs})
        result = parse_literature(raw)
        assert len(result.references) <= 3


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class TestParseProtocol:
    def test_valid_steps(self):
        raw = _json({"steps": [
            {"step_number": 1, "title": "T", "description": "D", "duration_minutes": 30,
             "equipment_needed": ["microscope"], "notes": None},
        ]})
        steps = parse_protocol(raw)
        assert len(steps) == 1
        assert steps[0].step_number == 1
        assert steps[0].equipment_needed == ["microscope"]

    def test_bad_json_returns_empty_list(self):
        assert parse_protocol("garbage") == []

    def test_missing_steps_key_returns_empty_list(self):
        assert parse_protocol(_json({"data": []})) == []


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

class TestParseMaterials:
    def test_valid_materials(self):
        raw = _json({"materials": [
            {"name": "PBS", "catalog_number": "P5493", "supplier": "Sigma-Aldrich",
             "quantity": "500 mL", "unit_cost_usd": 15.0, "total_cost_usd": 15.0,
             "hazard_class": None},
        ]})
        mats = parse_materials(raw)
        assert len(mats) == 1
        assert mats[0].catalog_number == "P5493"

    def test_catalog_tbd_accepted(self):
        raw = _json({"materials": [
            {"name": "Mystery Reagent", "catalog_number": "CATALOG_TBD",
             "supplier": "Unknown", "quantity": "1 unit",
             "unit_cost_usd": 0.0, "total_cost_usd": 0.0},
        ]})
        mats = parse_materials(raw)
        assert mats[0].catalog_number == "CATALOG_TBD"


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class TestParseBudget:
    def test_valid_budget(self):
        raw = _json({
            "line_items": [
                {"category": "reagents", "description": "All reagents", "cost_usd": 100.0},
                {"category": "personnel", "description": "Tech time", "cost_usd": 500.0},
            ],
            "grand_total_usd": 600.0,
            "currency_note": "USD",
        })
        budget = parse_budget(raw)
        assert budget is not None
        assert budget.grand_total_usd == 600.0
        assert len(budget.line_items) == 2

    def test_bad_json_returns_none(self):
        assert parse_budget("not json") is None


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TestParseTimeline:
    def test_valid_phases(self):
        raw = _json({"phases": [
            {"phase_name": "Procurement", "duration_days": 7,
             "tasks": ["Order", "Setup", "Test"], "depends_on": [], "milestone": "Ready"},
        ]})
        phases = parse_timeline(raw)
        assert len(phases) == 1
        assert phases[0].phase_name == "Procurement"
        assert phases[0].milestone == "Ready"

    def test_empty_phases_returns_empty_list(self):
        assert parse_timeline(_json({"phases": []})) == []


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestParseValidation:
    def test_valid_validation(self):
        raw = _json({
            "primary_metric": "viability %",
            "success_threshold": ">85%",
            "statistical_test": "t-test",
            "controls": ["positive", "negative"],
            "sample_size_per_group": 3,
            "power": 0.80,
            "alpha": 0.05,
            "effect_size_estimate": "large",
        })
        val = parse_validation(raw)
        assert val is not None
        assert val.primary_metric == "viability %"
        assert val.sample_size_per_group == 3

    def test_bad_json_returns_none(self):
        assert parse_validation("oops") is None


# ---------------------------------------------------------------------------
# Biosafety
# ---------------------------------------------------------------------------

class TestParseBiosafety:
    def test_valid_bsl2(self):
        raw = _json({
            "level": "BSL-2",
            "hazardous_materials": ["HeLa cells"],
            "required_ppe": ["gloves", "lab coat"],
            "waste_disposal_protocol": "Autoclave",
            "special_requirements": ["Class II cabinet"],
            "regulatory_notes": "IBC approval needed",
        })
        bio = parse_biosafety(raw)
        assert bio is not None
        assert bio.level == BiosafetyLevel.BSL2

    def test_bad_json_returns_none(self):
        assert parse_biosafety("broken") is None


# ---------------------------------------------------------------------------
# Risks
# ---------------------------------------------------------------------------

class TestParseRisks:
    def test_valid_risks(self):
        raw = _json({"risks": [
            {"description": "Cell contamination", "severity": "high",
             "likelihood": "medium", "mitigation": "Use sterile technique"},
        ]})
        risks = parse_risks(raw)
        assert len(risks) == 1
        assert risks[0].severity == "high"

    def test_bad_json_returns_empty_list(self):
        assert parse_risks("bad") == []
