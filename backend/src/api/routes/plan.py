"""
GET   /api/plan/{plan_id}           — retrieve a saved experiment plan
GET   /api/plans                    — paginated list of all plans
POST  /api/plans/recalculate-scores — recompute quality scores for all plans
"""
from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_repo
from domain.pipeline.quality_gate import compute_quality_score
from domain.ports.experiment_repo import IExperimentRepo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/plan/{plan_id}")
async def get_plan(
    plan_id: UUID,
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
) -> dict:
    """Return a single experiment plan by its UUID."""
    plan = await repo.get(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found.",
        )
    return plan.model_dump(mode="json")


@router.get("/api/plans")
async def list_plans(
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """Return a paginated list of experiment plans ordered by creation date (newest first)."""
    plans = await repo.list_plans(limit=limit, offset=offset)
    return {
        "count": len(plans),
        "offset": offset,
        "plans": [
            {
                "plan_id": str(p.plan_id),
                "hypothesis": p.hypothesis[:120],
                "experiment_domain": p.experiment_domain,
                "quality_score": p.quality_score,
                "feedback_incorporated": p.feedback_incorporated,
                "created_at": p.created_at.isoformat(),
            }
            for p in plans
        ],
    }


@router.post("/api/plans/recalculate-scores")
async def recalculate_quality_scores(
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
) -> dict:
    """Recompute quality scores for all stored plans using the current algorithm."""
    plans = await repo.list_plans(limit=1000, offset=0)
    updated = 0
    for plan in plans:
        old_score = plan.quality_score
        plan.quality_score = compute_quality_score(plan)
        if plan.quality_score != old_score:
            await repo.save(plan)
            updated += 1
    logger.info("Recalculated quality scores: %d/%d plans updated", updated, len(plans))
    return {"total": len(plans), "updated": updated}
