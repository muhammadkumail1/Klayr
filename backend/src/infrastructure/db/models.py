"""
SQLAlchemy 2.0 table definitions for the infrastructure layer.
Uses JSONB columns for complex nested structures — pragmatic choice for a research tool
where the schema evolves rapidly with each experiment domain.
"""
from __future__ import annotations

import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ExperimentPlanRow(Base):
    __tablename__ = "experiment_plans"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    refined_hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    experiment_domain: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    feedback_incorporated: Mapped[bool] = mapped_column(nullable=False, default=False)
    quality_score: Mapped[float | None] = mapped_column(nullable=True)
    # Full plan serialized as JSONB for fast retrieval and flexible querying
    plan_json: Mapped[dict] = mapped_column(JSONB, nullable=False)


class FeedbackEntryRow(Base):
    __tablename__ = "feedback_entries"

    feedback_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    plan_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(64), nullable=False)
    experiment_domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    correction: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
