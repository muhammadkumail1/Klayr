"""
FastAPI route tests — uses TestClient with mocked dependencies.
"""
from __future__ import annotations

import json
import uuid
import datetime
from typing import Optional
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.dependencies import get_llm_client, get_lit_search, get_repo, get_cache
from domain.entities.experiment import (
    Budget,
    BudgetLine,
    ExperimentDomain,
    ExperimentPlan,
    FeedbackEntry,
    LiteratureResult,
    NoveltySignal,
    ProtocolStep,
    Reagent,
    TimelinePhase,
    ValidationApproach,
)
from domain.ports.cache import ICache
from domain.ports.experiment_repo import IExperimentRepo


# ---------------------------------------------------------------------------
# In-memory stub implementations
# ---------------------------------------------------------------------------

class InMemoryRepo(IExperimentRepo):
    def __init__(self):
        self._plans: dict[UUID, ExperimentPlan] = {}
        self._feedback: list[FeedbackEntry] = []

    async def save(self, plan: ExperimentPlan) -> None:
        self._plans[plan.plan_id] = plan

    async def get(self, plan_id: UUID) -> Optional[ExperimentPlan]:
        return self._plans.get(plan_id)

    async def list_plans(self, limit=20, offset=0) -> list[ExperimentPlan]:
        plans = sorted(self._plans.values(), key=lambda p: p.created_at, reverse=True)
        return plans[offset: offset + limit]

    async def save_feedback(self, entry: FeedbackEntry) -> None:
        self._feedback.append(entry)

    async def get_recent_feedback(self, domain: str, limit: int = 3) -> list[FeedbackEntry]:
        return []


class InMemoryCache(ICache):
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def in_memory_repo():
    return InMemoryRepo()


@pytest.fixture
def in_memory_cache():
    return InMemoryCache()


@pytest.fixture
def test_client(mock_llm, mock_lit_search, in_memory_repo, in_memory_cache):
    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_lit_search] = lambda: mock_lit_search
    app.dependency_overrides[get_repo] = lambda: in_memory_repo
    app.dependency_overrides[get_cache] = lambda: in_memory_cache
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data


class TestRunEndpoint:
    def test_run_returns_plan(self, test_client):
        resp = test_client.post(
            "/api/run",
            json={"hypothesis": "Does trehalose preserve HeLa cells better than DMSO?", "domain": "cell_biology"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "plan_id" in data
        assert "plan" in data
        assert data["quality_score"] >= 0

    def test_run_plan_saved_to_repo(self, test_client, in_memory_repo):
        resp = test_client.post(
            "/api/run",
            json={"hypothesis": "Test hypothesis for saving", "domain": "other"},
        )
        assert resp.status_code == 200
        plan_id = uuid.UUID(resp.json()["plan_id"])
        import asyncio
        plan = asyncio.get_event_loop().run_until_complete(in_memory_repo.get(plan_id))
        assert plan is not None


class TestPlanEndpoints:
    def test_get_plan_not_found_returns_404(self, test_client):
        resp = test_client.get(f"/api/plan/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_list_plans_empty(self, test_client):
        resp = test_client.get("/api/plans")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestFeedbackEndpoint:
    def test_submit_feedback_returns_201(self, test_client):
        resp = test_client.post(
            "/api/feedback",
            json={
                "plan_id": str(uuid.uuid4()),
                "section": "protocol",
                "original_content": "Original step description",
                "correction": "Use 0.05% trypsin instead of 0.25%",
                "experiment_domain": "cell_biology",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "stored"
        assert "feedback_id" in data
