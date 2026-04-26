"""
POST /api/run        — synchronous pipeline execution, returns full plan
POST /api/run/stream — SSE streaming endpoint for real-time progress updates
"""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.dependencies import get_cache, get_lit_search, get_llm_client, get_repo
from domain.entities.experiment import (
    ExperimentDomain,
    ExperimentPlan,
    LiteratureResult,
    NoveltySignal,
    Budget,
)
from domain.pipeline.graph import build_pipeline
from domain.pipeline.quality_gate import compute_quality_score, validate_plan
from domain.pipeline.state import PipelineState
from domain.ports.cache import ICache
from domain.ports.experiment_repo import IExperimentRepo
from domain.ports.lit_search import ILitSearch
from domain.ports.llm_client import ILLMClient

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    hypothesis: str
    domain: str = "other"   # ExperimentDomain value, used for few-shot retrieval

    model_config = {"str_strip_whitespace": True}


class RunResponse(BaseModel):
    plan_id: str
    quality_score: float
    quality_errors: list[str]
    plan: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_initial_state(hypothesis: str, shots: list) -> PipelineState:
    return {
        "raw_input": hypothesis,
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
        "few_shot_examples": shots,
        "errors": [],
        "final_plan": None,
    }


def assemble_plan(state: PipelineState) -> ExperimentPlan:
    """Merge completed pipeline state into a validated ExperimentPlan."""
    lit = state.get("literature_result") or LiteratureResult(
        novelty_signal=NoveltySignal.NOT_FOUND
    )
    budget = state.get("budget")
    if budget is None:
        from domain.entities.experiment import BudgetLine
        budget = Budget(line_items=[], grand_total_usd=0.0)

    plan = ExperimentPlan(
        plan_id=uuid.uuid4(),
        hypothesis=state["raw_input"],
        refined_hypothesis=state.get("refined_hypothesis") or state["raw_input"],
        experiment_domain=state.get("experiment_domain", ExperimentDomain.OTHER),
        sub_hypotheses=state.get("sub_hypotheses", []),
        alternative_hypotheses=state.get("alternative_hypotheses", []),
        expected_outcomes=state.get("expected_outcomes", []),
        literature_result=lit,
        protocol_steps=state.get("protocol_steps") or [],
        materials=state.get("materials") or [],
        budget=budget,
        timeline=state.get("timeline") or [],
        validation=state.get("validation"),  # type: ignore[arg-type]
        biosafety=state.get("biosafety"),
        risks=state.get("risks", []),
        created_at=datetime.datetime.utcnow(),
        feedback_incorporated=bool(state.get("few_shot_examples")),
    )

    errors = validate_plan(plan)
    plan.quality_score = compute_quality_score(plan)
    if errors:
        logger.warning("Plan %s quality gate errors: %s", plan.plan_id, errors)

    return plan


# ---------------------------------------------------------------------------
# POST /api/run  (synchronous)
# ---------------------------------------------------------------------------

@router.post("/api/run", response_model=RunResponse, status_code=status.HTTP_200_OK)
async def run_pipeline(
    body: RunRequest,
    llm: Annotated[ILLMClient, Depends(get_llm_client)],
    lit: Annotated[ILitSearch, Depends(get_lit_search)],
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    cache: Annotated[ICache, Depends(get_cache)],
) -> RunResponse:
    """
    Execute the full AI Scientist pipeline and return the complete experiment plan.
    Typical latency: 25–45 s (8 LLM calls + 2 parallel search APIs).
    """
    cache_key = f"plan:{hash(body.hypothesis.strip().lower())}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info("Cache hit for hypothesis: %.60s", body.hypothesis)
        data = json.loads(cached)
        return RunResponse(**data)

    shots = await repo.get_recent_feedback(domain=body.domain, limit=3)
    pipeline = build_pipeline(llm, lit)
    initial_state = _build_initial_state(body.hypothesis, shots)

    try:
        result = await pipeline.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Pipeline execution failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {exc}",
        )

    plan = assemble_plan(result)
    await repo.save(plan)

    response = RunResponse(
        plan_id=str(plan.plan_id),
        quality_score=plan.quality_score or 0.0,
        quality_errors=validate_plan(plan),
        plan=plan.model_dump(mode="json"),
    )
    await cache.set(cache_key, response.model_dump_json(), ttl_seconds=3600)
    return response


# ---------------------------------------------------------------------------
# POST /api/run/stream  (SSE — real-time progress)
# ---------------------------------------------------------------------------

@router.post("/api/run/stream")
async def run_pipeline_stream(
    body: RunRequest,
    llm: Annotated[ILLMClient, Depends(get_llm_client)],
    lit: Annotated[ILitSearch, Depends(get_lit_search)],
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
) -> StreamingResponse:
    """
    Stream pipeline progress as Server-Sent Events.
    Each node completion emits a JSON event.
    Final event has type="complete" and contains the full plan.
    """
    event_queue: asyncio.Queue = asyncio.Queue()

    async def on_event(event: dict) -> None:
        await event_queue.put(event)

    async def event_generator():
        shots = await repo.get_recent_feedback(domain=body.domain, limit=3)
        pipeline = build_pipeline(llm, lit, on_event=on_event)
        initial_state = _build_initial_state(body.hypothesis, shots)

        async def run_pipeline_task():
            try:
                result = await pipeline.ainvoke(initial_state)
                plan = assemble_plan(result)
                await repo.save(plan)
                await event_queue.put({
                    "type": "complete",
                    "plan_id": str(plan.plan_id),
                    "quality_score": plan.quality_score,
                    "plan": plan.model_dump(mode="json"),
                })
            except Exception as exc:
                logger.exception("Streaming pipeline failed")
                await event_queue.put({"type": "error", "message": str(exc)})

        task = asyncio.create_task(run_pipeline_task())

        # Yield events until complete or error
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=120.0)
                yield f"data: {json.dumps(event, default=str)}\n\n"
                if event.get("type") in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                # Heartbeat keeps the connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        await task  # ensure cleanup

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
