from abc import ABC, abstractmethod
from typing import Optional


class ICache(ABC):
    """Port: key-value cache (Redis or in-memory for testing)."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Return the cached string value, or None on miss / expired."""
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        """Store *value* under *key* with an optional TTL."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Evict *key* from the cache (no-op if key does not exist)."""
        ...
