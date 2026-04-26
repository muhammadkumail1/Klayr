from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from domain.entities.experiment import ExperimentPlan, FeedbackEntry


class IExperimentRepo(ABC):
    """Port: persistence for experiment plans and scientist feedback."""

    @abstractmethod
    async def save(self, plan: ExperimentPlan) -> None:
        """Upsert an ExperimentPlan by plan_id."""
        ...

    @abstractmethod
    async def get(self, plan_id: UUID) -> Optional[ExperimentPlan]:
        """Return an ExperimentPlan or None if not found."""
        ...

    @abstractmethod
    async def list_plans(self, limit: int = 20, offset: int = 0) -> list[ExperimentPlan]:
        """Return a paginated list of plans ordered by created_at DESC."""
        ...

    @abstractmethod
    async def save_feedback(self, entry: FeedbackEntry) -> None:
        """Persist a scientist's correction."""
        ...

    @abstractmethod
    async def get_recent_feedback(
        self,
        domain: str,
        limit: int = 3,
    ) -> list[FeedbackEntry]:
        """Return the *limit* most recent FeedbackEntries for *domain*,
        used as few-shot examples in the protocol prompt."""
        ...
