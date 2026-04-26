"""
CombinedLitSearch — calls PubMed + Semantic Scholar concurrently,
deduplicates by DOI (then by title), keeps top 3, and generates
LLM-based abstract summaries for each result.

This is the ILitSearch implementation injected into the pipeline.
"""
from __future__ import annotations

import asyncio
import logging

from domain.entities.experiment import Paper
from domain.ports.lit_search import ILitSearch
from domain.ports.llm_client import ILLMClient
from infrastructure.search.pubmed import PubMedClient
from infrastructure.search.semantic_scholar import SemanticScholarClient

logger = logging.getLogger(__name__)

_SUMMARIZE_SYSTEM = (
    "You are a scientific assistant. Summarize the following abstract in 2-3 sentences, "
    "plain English, focusing on what was done and what was found. "
    "Return only the summary — no preamble, no markdown."
)


class CombinedLitSearch(ILitSearch):
    """
    Aggregates PubMed + Semantic Scholar results.

    Design choices:
    - PubMed results take priority in merge order (better biomedical abstracts).
    - Deduplication: primary by DOI, secondary by title prefix (first 60 chars).
    - Top-3 papers get LLM-generated abstract summaries (concurrent calls).
    - A failure in either source never blocks the pipeline.
    """

    def __init__(
        self,
        llm: ILLMClient,
        pubmed: "PubMedClient | None" = None,
        semantic_scholar: "SemanticScholarClient | None" = None,
    ) -> None:
        self._pubmed = pubmed or PubMedClient()
        self._ss = semantic_scholar or SemanticScholarClient()
        self._llm = llm

    async def search(self, query: str) -> list[Paper]:
        # Concurrent fetch from both sources
        pm_results, ss_results = await asyncio.gather(
            self._safe_search(self._pubmed, query),
            self._safe_search(self._ss, query),
        )

        # Merge: PubMed first for biomedical priority
        merged: list[Paper] = []
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()

        for paper in pm_results + ss_results:
            doi = paper.relevance_note.strip()
            title_key = paper.title.lower()[:60]

            if doi and doi in seen_dois:
                continue
            if title_key in seen_titles:
                continue

            if doi:
                seen_dois.add(doi)
            seen_titles.add(title_key)
            merged.append(paper)

        top3 = merged[:3]
        if not top3:
            logger.warning("CombinedLitSearch: both sources returned no results for: %.80s", query)
            return []

        # Concurrent abstract summarisation
        summaries = await asyncio.gather(*[self._summarize(p) for p in top3])
        for paper, summary in zip(top3, summaries):
            paper.abstract_summary = summary
            paper.relevance_note = ""  # clear the temp DOI field

        logger.debug("CombinedLitSearch: returning %d deduplicated papers", len(top3))
        return top3

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _safe_search(self, client: ILitSearch, query: str) -> list[Paper]:
        """Run a search; return empty list on any failure."""
        try:
            return await client.search(query)
        except Exception as exc:
            logger.warning("Search source %s failed (non-fatal): %s", type(client).__name__, exc)
            return []

    async def _summarize(self, paper: Paper) -> str:
        """Generate a 2–3 sentence LLM summary of the abstract."""
        if not paper.abstract:
            return "Abstract not available."
        try:
            return await self._llm.complete(
                system=_SUMMARIZE_SYSTEM,
                prompt=paper.abstract,
            )
        except Exception as exc:
            logger.warning("Abstract summarization failed for '%s': %s", paper.title[:60], exc)
            # Graceful fallback: truncated raw abstract
            return paper.abstract[:300] + ("..." if len(paper.abstract) > 300 else "")
