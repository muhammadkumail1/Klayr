"""
PostgreSQL implementation of IExperimentRepo using async SQLAlchemy 2.0.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.experiment import ExperimentPlan, FeedbackEntry
from domain.ports.experiment_repo import IExperimentRepo
from infrastructure.db.models import ExperimentPlanRow, FeedbackEntryRow

logger = logging.getLogger(__name__)


class PostgresExperimentRepo(IExperimentRepo):
    """
    Stores ExperimentPlan as JSONB (via model_dump) and FeedbackEntry rows
    in a separate table indexed by domain for fast few-shot retrieval.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    # ExperimentPlan
    # ------------------------------------------------------------------

    async def save(self, plan: ExperimentPlan) -> None:
        async with self._session_factory() as session:
            row = await session.get(ExperimentPlanRow, plan.plan_id)
            plan_dict = plan.model_dump(mode="json")
            if row is None:
                row = ExperimentPlanRow(
                    plan_id=plan.plan_id,
                    hypothesis=plan.hypothesis,
                    refined_hypothesis=plan.refined_hypothesis,
                    experiment_domain=plan.experiment_domain.value,
                    created_at=plan.created_at,
                    feedback_incorporated=plan.feedback_incorporated,
                    quality_score=plan.quality_score,
                    plan_json=plan_dict,
                )
                session.add(row)
            else:
                row.plan_json = plan_dict
                row.quality_score = plan.quality_score
                row.feedback_incorporated = plan.feedback_incorporated
            await session.commit()
            logger.debug("Saved plan %s", plan.plan_id)

    async def get(self, plan_id: UUID) -> Optional[ExperimentPlan]:
        async with self._session_factory() as session:
            row = await session.get(ExperimentPlanRow, plan_id)
            if row is None:
                return None
            return ExperimentPlan.model_validate(row.plan_json)

    async def list_plans(self, limit: int = 20, offset: int = 0) -> list[ExperimentPlan]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ExperimentPlanRow)
                .order_by(desc(ExperimentPlanRow.created_at))
                .limit(limit)
                .offset(offset)
            )
            rows = result.scalars().all()
            return [ExperimentPlan.model_validate(r.plan_json) for r in rows]

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    async def save_feedback(self, entry: FeedbackEntry) -> None:
        async with self._session_factory() as session:
            row = FeedbackEntryRow(
                feedback_id=entry.feedback_id,
                plan_id=entry.plan_id,
                section=entry.section,
                experiment_domain=entry.experiment_domain,
                original_content=entry.original_content,
                correction=entry.correction,
                created_at=entry.created_at,
            )
            session.add(row)
            await session.commit()
            logger.debug("Saved feedback %s", entry.feedback_id)

    async def get_recent_feedback(
        self,
        domain: str,
        limit: int = 3,
    ) -> list[FeedbackEntry]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(FeedbackEntryRow)
                .where(FeedbackEntryRow.experiment_domain == domain)
                .order_by(desc(FeedbackEntryRow.created_at))
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                FeedbackEntry(
                    feedback_id=r.feedback_id,
                    plan_id=r.plan_id,
                    section=r.section,
                    original_content=r.original_content,
                    correction=r.correction,
                    experiment_domain=r.experiment_domain,
                    created_at=r.created_at,
                )
                for r in rows
            ]
