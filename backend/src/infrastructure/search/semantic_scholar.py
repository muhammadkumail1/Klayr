"""
Semantic Scholar search implementation.
Uses the public Graph API — free tier supports up to 100 req/5 min.
Optional API key env var raises that limit.
"""
from __future__ import annotations

import logging
import os

import httpx

from domain.entities.experiment import Paper
from domain.ports.lit_search import ILitSearch

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,authors,year,externalIds,abstract"
_TIMEOUT = 12.0


class SemanticScholarClient(ILitSearch):
    """Queries the Semantic Scholar Graph API."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")

    async def search(self, query: str) -> list[Paper]:
        headers = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_BASE_URL}/paper/search",
                params={"query": query, "limit": 5, "fields": _FIELDS},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        results: list[Paper] = []
        for p in data.get("data", []):
            doi = (p.get("externalIds") or {}).get("DOI", "")
            results.append(
                Paper(
                    title=p.get("title", ""),
                    authors=[a["name"] for a in (p.get("authors") or [])[:3]],
                    year=p.get("year") or 0,
                    url=f"https://www.semanticscholar.org/paper/{p['paperId']}",
                    abstract=p.get("abstract"),
                    abstract_summary=None,
                    source="semantic_scholar",
                    relevance_note=doi,  # temp DOI storage for dedup
                )
            )

        logger.debug("SemanticScholar returned %d results for query: %.80s", len(results), query)
        return results
