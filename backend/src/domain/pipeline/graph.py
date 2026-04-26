"""
LangGraph pipeline — the core orchestration graph.

Each node:
  1. Builds a prompt (pure domain function)
  2. Sends it to the LLM (via port)
  3. Parses the result (pure domain function)
  4. Writes back to state

Nothing else happens inside a node.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

from langgraph.graph import END, StateGraph

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
from domain.pipeline.state import PipelineState
from domain.ports.lit_search import ILitSearch
from domain.ports.llm_client import ILLMClient
from domain.prompts import (
    biosafety_prompt,
    budget_prompt,
    hypothesis_prompt,
    literature_prompt,
    materials_prompt,
    protocol_prompt,
    risk_prompt,
    timeline_prompt,
    validation_prompt,
)

logger = logging.getLogger(__name__)

# Type alias for the optional streaming callback
EventCallback = Optional[Callable[[dict], Coroutine[Any, Any, None]]]


async def _emit(callback: EventCallback, event: dict) -> None:
    """Fire-and-forget the streaming callback; swallow errors to never block the pipeline."""
    if callback is None:
        return
    try:
        await callback(event)
    except Exception as exc:
        logger.warning("Event callback error (non-fatal): %s", exc)


def build_pipeline(
    llm: ILLMClient,
    lit_search: ILitSearch,
    on_event: EventCallback = None,
) -> Any:
    """
    Build and compile the LangGraph StateGraph.

    Parameters
    ----------
    llm        : ILLMClient implementation (injected by FastAPI)
    lit_search : ILitSearch implementation (injected by FastAPI)
    on_event   : optional async callable; receives dicts like
                 {"node": "generate_protocol", "status": "complete"}
                 Used by the SSE streaming endpoint.
    """

    # ------------------------------------------------------------------
    # Node 1 — Hypothesis refinement
    # ------------------------------------------------------------------
    async def refine_hypothesis(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "refine_hypothesis", "status": "started"})
        prompt = hypothesis_prompt.build(state["raw_input"])
        raw = await llm.complete(system=hypothesis_prompt.SYSTEM, prompt=prompt)
        refined, domain, subs, alts, outcomes = parse_hypothesis(raw)
        state["refined_hypothesis"] = refined
        state["experiment_domain"] = domain
        state["sub_hypotheses"] = subs
        state["alternative_hypotheses"] = alts
        state["expected_outcomes"] = outcomes
        await _emit(on_event, {"node": "refine_hypothesis", "status": "complete",
                               "data": {"refined_hypothesis": refined, "domain": domain}})
        return state

    # ------------------------------------------------------------------
    # Node 2 — Literature QC
    # ------------------------------------------------------------------
    async def run_literature_qc(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "literature_qc", "status": "started"})
        papers = await lit_search.search(state["refined_hypothesis"])
        prompt = literature_prompt.build(state["refined_hypothesis"], papers)
        raw = await llm.complete(system=literature_prompt.SYSTEM, prompt=prompt)
        lit_result = parse_literature(raw)
        state["literature_result"] = lit_result
        await _emit(on_event, {"node": "literature_qc", "status": "complete",
                               "data": {"novelty_signal": lit_result.novelty_signal,
                                        "papers_found": len(lit_result.references)}})
        return state

    # ------------------------------------------------------------------
    # Node 3 — Protocol generation
    # ------------------------------------------------------------------
    async def generate_protocol(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "generate_protocol", "status": "started"})
        prompt = protocol_prompt.build(
            state["refined_hypothesis"],
            state["literature_result"],
            state.get("few_shot_examples", []),
        )
        raw = await llm.complete(system=protocol_prompt.SYSTEM, prompt=prompt)
        steps = parse_protocol(raw)
        if not steps:
            state["errors"] = state.get("errors", []) + ["Protocol generation returned no steps"]
        state["protocol_steps"] = steps
        await _emit(on_event, {"node": "generate_protocol", "status": "complete",
                               "data": {"steps_count": len(steps)}})
        return state

    # ------------------------------------------------------------------
    # Node 4 — Materials list
    # ------------------------------------------------------------------
    async def generate_materials(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "generate_materials", "status": "started"})
        prompt = materials_prompt.build(state["protocol_steps"] or [])
        raw = await llm.complete(system=materials_prompt.SYSTEM, prompt=prompt)
        mats = parse_materials(raw)
        if not mats:
            state["errors"] = state.get("errors", []) + ["Materials generation returned empty list"]
        state["materials"] = mats
        await _emit(on_event, {"node": "generate_materials", "status": "complete",
                               "data": {"materials_count": len(mats)}})
        return state

    # ------------------------------------------------------------------
    # Node 5 — Budget
    # ------------------------------------------------------------------
    async def generate_budget(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "generate_budget", "status": "started"})
        prompt = budget_prompt.build(state["materials"] or [])
        raw = await llm.complete(system=budget_prompt.SYSTEM, prompt=prompt)
        budget = parse_budget(raw)
        if budget is None:
            state["errors"] = state.get("errors", []) + ["Budget generation failed"]
        state["budget"] = budget
        await _emit(on_event, {"node": "generate_budget", "status": "complete",
                               "data": {"total_usd": budget.grand_total_usd if budget else 0}})
        return state

    # ------------------------------------------------------------------
    # Node 6 — Timeline
    # ------------------------------------------------------------------
    async def generate_timeline(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "generate_timeline", "status": "started"})
        prompt = timeline_prompt.build(
            state["protocol_steps"] or [],
            state["budget"],
        )
        raw = await llm.complete(system=timeline_prompt.SYSTEM, prompt=prompt)
        phases = parse_timeline(raw)
        if not phases:
            state["errors"] = state.get("errors", []) + ["Timeline generation returned no phases"]
        state["timeline"] = phases
        await _emit(on_event, {"node": "generate_timeline", "status": "complete",
                               "data": {"phases_count": len(phases)}})
        return state

    # ------------------------------------------------------------------
    # Node 7 — Validation design
    # ------------------------------------------------------------------
    async def generate_validation(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "generate_validation", "status": "started"})
        steps_summary = "\n".join(
            f"Step {s.step_number}: {s.title}"
            for s in (state["protocol_steps"] or [])
        )
        prompt = validation_prompt.build(state["refined_hypothesis"], steps_summary)
        raw = await llm.complete(system=validation_prompt.SYSTEM, prompt=prompt)
        val = parse_validation(raw)
        if val is None:
            state["errors"] = state.get("errors", []) + ["Validation design failed"]
        state["validation"] = val
        await _emit(on_event, {"node": "generate_validation", "status": "complete"})
        return state

    # ------------------------------------------------------------------
    # Node 8 — Biosafety + Risks (run concurrently inside the node)
    # ------------------------------------------------------------------
    async def assess_safety_and_risks(state: PipelineState) -> PipelineState:
        await _emit(on_event, {"node": "assess_safety_and_risks", "status": "started"})

        mats = state.get("materials") or []
        steps = state.get("protocol_steps") or []

        bio_prompt = biosafety_prompt.build(mats, steps)
        rsk_prompt = risk_prompt.build(steps, mats)

        bio_raw, rsk_raw = await asyncio.gather(
            llm.complete(system=biosafety_prompt.SYSTEM, prompt=bio_prompt),
            llm.complete(system=risk_prompt.SYSTEM, prompt=rsk_prompt),
        )

        state["biosafety"] = parse_biosafety(bio_raw)
        state["risks"] = parse_risks(rsk_raw)

        await _emit(on_event, {"node": "assess_safety_and_risks", "status": "complete",
                               "data": {"risks_count": len(state["risks"]),
                                        "bsl": state["biosafety"].level if state["biosafety"] else "unknown"}})
        return state

    # ------------------------------------------------------------------
    # Graph assembly
    # ------------------------------------------------------------------
    graph = StateGraph(PipelineState)

    graph.add_node("refine_hypothesis", refine_hypothesis)
    graph.add_node("literature_qc", run_literature_qc)
    graph.add_node("generate_protocol", generate_protocol)
    graph.add_node("generate_materials", generate_materials)
    graph.add_node("generate_budget", generate_budget)
    graph.add_node("generate_timeline", generate_timeline)
    graph.add_node("generate_validation", generate_validation)
    graph.add_node("assess_safety_and_risks", assess_safety_and_risks)

    graph.set_entry_point("refine_hypothesis")
    graph.add_edge("refine_hypothesis", "literature_qc")
    graph.add_edge("literature_qc", "generate_protocol")
    graph.add_edge("generate_protocol", "generate_materials")
    graph.add_edge("generate_materials", "generate_budget")
    graph.add_edge("generate_budget", "generate_timeline")
    graph.add_edge("generate_timeline", "generate_validation")
    graph.add_edge("generate_validation", "assess_safety_and_risks")
    graph.add_edge("assess_safety_and_risks", END)

    return graph.compile()
