"""
POST /api/feedback — submit a scientist's correction for a plan section.

Corrections are stored and retrieved as few-shot examples for future pipeline
runs in the same experiment domain (the feedback loop mechanism).
"""
from __future__ import annotations

import datetime
import logging
import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from api.dependencies import get_repo
from domain.entities.experiment import FeedbackEntry
from domain.ports.experiment_repo import IExperimentRepo

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    plan_id: UUID
    section: str            # "protocol" | "materials" | "budget" | "timeline" | "validation"
    original_content: str
    correction: str
    experiment_domain: str  # e.g. "cell_biology"

    model_config = {"str_strip_whitespace": True}


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/api/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackRequest,
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
) -> dict:
    """
    Store a scientist's correction as a few-shot example.
    Future pipeline runs for the same domain will automatically incorporate these.
    """
    entry = FeedbackEntry(
        feedback_id=uuid.uuid4(),
        plan_id=body.plan_id,
        section=body.section,
        original_content=body.original_content,
        correction=body.correction,
        experiment_domain=body.experiment_domain,
        created_at=datetime.datetime.utcnow(),
    )
    await repo.save_feedback(entry)
    logger.info(
        "Stored feedback %s for plan %s [domain=%s section=%s]",
        entry.feedback_id,
        entry.plan_id,
        entry.experiment_domain,
        entry.section,
    )
    return {"status": "stored", "feedback_id": str(entry.feedback_id)}
