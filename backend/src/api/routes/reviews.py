"""
POST /api/reviews        — submit a scientist review with rating for a plan.
GET  /api/reviews        — retrieve all reviews for a plan.
"""
from __future__ import annotations

import datetime
import logging
import uuid
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_repo
from domain.ports.experiment_repo import IExperimentRepo

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# In-memory review store (Redis-style per session).
# For production this would be a DB table; here we use a module-level dict
# since this is a hackathon project and reviews don't need to persist across restarts.
# ---------------------------------------------------------------------------

_reviews: dict[str, list[dict]] = {}   # plan_id_str -> list of review dicts


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ReviewRequest(BaseModel):
    plan_id: UUID
    section: str            # "protocol" | "materials" | "budget" | "timeline" | "validation"
    rating: float = Field(ge=1.0, le=5.0)
    comment: str
    correction: str = ""
    reviewer_name: str = "Anonymous Reviewer"

    model_config = {"str_strip_whitespace": True}


class ReviewEntry(BaseModel):
    review_id: str
    plan_id: str
    section: str
    rating: float
    comment: str
    correction: str
    reviewer_name: str
    initials: str
    created_at: str


class ReviewsResponse(BaseModel):
    plan_id: str
    reviews: list[ReviewEntry]
    avg_rating: float
    count: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/api/reviews", status_code=status.HTTP_201_CREATED)
async def submit_review(
    body: ReviewRequest,
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
) -> ReviewEntry:
    """
    Store a scientist review for an experiment plan.
    Also persists as a feedback entry (correction loop) if correction is provided.
    """
    plan_id_str = str(body.plan_id)

    # If there's a correction, persist to feedback loop too
    if body.correction.strip():
        try:
            from domain.entities.experiment import FeedbackEntry
            from domain.entities.experiment import ExperimentDomain

            # Fetch plan to get domain
            plan = await repo.get(body.plan_id)
            domain_str = plan.experiment_domain.value if plan else "other"

            entry = FeedbackEntry(
                feedback_id=uuid.uuid4(),
                plan_id=body.plan_id,
                section=body.section,
                original_content=body.comment,
                correction=body.correction,
                experiment_domain=domain_str,
                created_at=datetime.datetime.utcnow(),
            )
            await repo.save_feedback(entry)
        except Exception as exc:
            logger.warning("Failed to persist feedback from review: %s", exc)

    # Build initials from reviewer name
    parts = body.reviewer_name.strip().split()
    initials = "".join(p[0].upper() for p in parts[:2]) if parts else "AR"

    review = ReviewEntry(
        review_id=str(uuid.uuid4()),
        plan_id=plan_id_str,
        section=body.section,
        rating=body.rating,
        comment=body.comment,
        correction=body.correction,
        reviewer_name=body.reviewer_name,
        initials=initials,
        created_at=datetime.datetime.utcnow().isoformat(),
    )

    if plan_id_str not in _reviews:
        _reviews[plan_id_str] = []
    _reviews[plan_id_str].append(review.model_dump())

    logger.info("Review submitted for plan %s: rating=%.1f", plan_id_str, body.rating)
    return review


@router.get("/api/reviews", response_model=ReviewsResponse)
async def get_reviews(
    plan_id: UUID = Query(...),
) -> ReviewsResponse:
    """Return all reviews for a given plan_id."""
    plan_id_str = str(plan_id)
    reviews_data = _reviews.get(plan_id_str, [])

    reviews = [ReviewEntry(**r) for r in reviews_data]
    avg_rating = (
        round(sum(r.rating for r in reviews) / len(reviews), 2) if reviews else 0.0
    )

    return ReviewsResponse(
        plan_id=plan_id_str,
        reviews=reviews,
        avg_rating=avg_rating,
        count=len(reviews),
    )
