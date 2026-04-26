"""
Redis implementation of ICache.
Uses redis.asyncio (bundled with redis-py ≥ 4.2).
"""
from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis

from domain.ports.cache import ICache

logger = logging.getLogger(__name__)


class RedisCache(ICache):
    """
    Thin Redis adapter. Connection is managed externally (passed in) so
    the same pool is shared across all FastAPI requests.
    """

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self._client.get(key)
            return value.decode() if value else None
        except Exception as exc:
            logger.warning("Cache GET failed for key '%s': %s", key, exc)
            return None

    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        try:
            await self._client.setex(key, ttl_seconds, value)
        except Exception as exc:
            logger.warning("Cache SET failed for key '%s': %s", key, exc)

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except Exception as exc:
            logger.warning("Cache DELETE failed for key '%s': %s", key, exc)
