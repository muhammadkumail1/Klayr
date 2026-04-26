"""
Pipeline integration tests — zero external calls.
Uses MockLLM + MockLitSearch from conftest.py.
"""
from __future__ import annotations

import pytest

from domain.pipeline.graph import build_pipeline
from domain.pipeline.state import PipelineState
from domain.entities.experiment import ExperimentDomain, NoveltySignal


INITIAL_STATE: PipelineState = {
    "raw_input": "Does trehalose preserve HeLa cells better than DMSO?",
    "refined_hypothesis": "",
    "experiment_domain": ExperimentDomain.OTHER,
    "sub_hypotheses": [],
    "alternative_hypotheses": [],
    "expected_outcomes": [],
    "literature_result": None,
    "protocol_steps": None,
    "materials": None,
    "budget": None,
    "timeline": None,
    "validation": None,
    "biosafety": None,
    "risks": [],
    "few_shot_examples": [],
    "errors": [],
    "final_plan": None,
}


@pytest.mark.asyncio
async def test_pipeline_runs_end_to_end(mock_llm, mock_lit_search):
    """Full pipeline completes without errors and populates all state keys."""
    pipeline = build_pipeline(mock_llm, mock_lit_search)
    result = await pipeline.ainvoke(INITIAL_STATE)

    assert result["refined_hypothesis"], "refined_hypothesis should be populated"
    assert result["literature_result"] is not None
    assert result["protocol_steps"], "protocol_steps should not be empty"
    assert result["materials"], "materials should not be empty"
    assert result["budget"] is not None
    assert result["timeline"], "timeline should not be empty"
    assert result["validation"] is not None
    assert result["biosafety"] is not None
    assert isinstance(result["risks"], list)


@pytest.mark.asyncio
async def test_pipeline_hypothesis_refinement(mock_llm, mock_lit_search):
    pipeline = build_pipeline(mock_llm, mock_lit_search)
    result = await pipeline.ainvoke(INITIAL_STATE)

    assert result["experiment_domain"] == ExperimentDomain.CELL_BIOLOGY
    assert len(result["sub_hypotheses"]) >= 1
    assert len(result["alternative_hypotheses"]) >= 1
    assert len(result["expected_outcomes"]) >= 1


@pytest.mark.asyncio
async def test_pipeline_literature_qc(mock_llm, mock_lit_search):
    pipeline = build_pipeline(mock_llm, mock_lit_search)
    result = await pipeline.ainvoke(INITIAL_STATE)

    lit = result["literature_result"]
    assert lit.novelty_signal == NoveltySignal.SIMILAR_EXISTS
    assert lit.gap_analysis != ""
    assert len(lit.references) >= 1


@pytest.mark.asyncio
async def test_pipeline_protocol_steps_numbered_sequentially(mock_llm, mock_lit_search):
    pipeline = build_pipeline(mock_llm, mock_lit_search)
    result = await pipeline.ainvoke(INITIAL_STATE)

    steps = result["protocol_steps"]
    assert steps
    for i, step in enumerate(steps):
        assert step.step_number == i + 1, f"Step {i+1} has step_number={step.step_number}"


@pytest.mark.asyncio
async def test_pipeline_budget_positive(mock_llm, mock_lit_search):
    pipeline = build_pipeline(mock_llm, mock_lit_search)
    result = await pipeline.ainvoke(INITIAL_STATE)

    budget = result["budget"]
    assert budget is not None
    assert budget.grand_total_usd > 0


@pytest.mark.asyncio
async def test_pipeline_streaming_events(mock_llm, mock_lit_search):
    """SSE on_event callback receives events for every node."""
    events = []

    async def collect(event: dict) -> None:
        events.append(event)

    pipeline = build_pipeline(mock_llm, mock_lit_search, on_event=collect)
    await pipeline.ainvoke(INITIAL_STATE)

    node_names = {e["node"] for e in events if "node" in e}
    expected_nodes = {
        "refine_hypothesis", "literature_qc", "generate_protocol",
        "generate_materials", "generate_budget", "generate_timeline",
        "generate_validation", "assess_safety_and_risks",
    }
    assert node_names == expected_nodes, f"Missing nodes: {expected_nodes - node_names}"
