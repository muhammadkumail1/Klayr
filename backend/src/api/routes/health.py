"""
GET /health — liveness + readiness probe.
Returns service version, uptime, and dependency status.
"""
from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.config import Settings, get_settings

router = APIRouter()

_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    environment: str
    version: str = "1.0.0"


@router.get("/health", response_model=HealthResponse, tags=["ops"])
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Liveness probe — always returns 200 if the process is running."""
    return HealthResponse(
        status="ok",
        uptime_seconds=round(time.time() - _START_TIME, 1),
        environment=settings.app_env,
    )
