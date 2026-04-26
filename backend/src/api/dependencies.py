"""
FastAPI dependency providers — the composition root.

All infrastructure singletons are created here and injected via Depends().
The domain pipeline never knows what implements its ports.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.config import Settings, get_settings
from domain.ports.cache import ICache
from domain.ports.experiment_repo import IExperimentRepo
from domain.ports.lit_search import ILitSearch
from domain.ports.llm_client import ILLMClient
from infrastructure.cache.redis_adapter import RedisCache
from infrastructure.db.postgres_repo import PostgresExperimentRepo
from infrastructure.llm.groq_client import GroqClient
from infrastructure.search.combined_search import CombinedLitSearch


# ---------------------------------------------------------------------------
# LLM Client — one instance for the entire application lifecycle
# ---------------------------------------------------------------------------

@lru_cache
def get_llm_client() -> ILLMClient:
    return GroqClient(api_key=get_settings().groq_api_key)


# ---------------------------------------------------------------------------
# Database session factory
# ---------------------------------------------------------------------------

@lru_cache
def _get_session_factory(db_url: str) -> async_sessionmaker:
    engine = create_async_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )
    return async_sessionmaker(engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

def get_repo(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IExperimentRepo:
    session_factory = _get_session_factory(settings.database_url)
    return PostgresExperimentRepo(session_factory)


# ---------------------------------------------------------------------------
# Redis Cache
# ---------------------------------------------------------------------------

@lru_cache
def _get_redis_client(redis_url: str) -> aioredis.Redis:
    return aioredis.from_url(redis_url, decode_responses=False)


def get_cache(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ICache:
    return RedisCache(_get_redis_client(settings.redis_url))


# ---------------------------------------------------------------------------
# Literature Search — reuses the same LLM client instance
# ---------------------------------------------------------------------------

def get_lit_search(
    llm: Annotated[ILLMClient, Depends(get_llm_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ILitSearch:
    from infrastructure.search.pubmed import PubMedClient
    from infrastructure.search.semantic_scholar import SemanticScholarClient
    from infrastructure.search.combined_search import CombinedLitSearch as _CLS
    return _CLS(
        llm,
        pubmed=PubMedClient(api_key=settings.ncbi_api_key or None),
        semantic_scholar=SemanticScholarClient(api_key=settings.semantic_scholar_api_key or None),
    )
