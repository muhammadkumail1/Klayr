"""
POST /api/literature/search  — direct literature search endpoint.

Allows the standalone Literature page to search PubMed + Semantic Scholar
without running the full pipeline.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from api.dependencies import get_lit_search
from domain.ports.lit_search import ILitSearch

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class LitSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    limit: int = Field(default=10, ge=1, le=20)

    model_config = {"str_strip_whitespace": True}


class PaperOut(BaseModel):
    title: str
    authors: list[str]
    year: int
    url: str
    abstract: str | None = None
    abstract_summary: str | None = None
    source: str
    similarity: int = 0   # placeholder, not computed here


class LitSearchResponse(BaseModel):
    query: str
    count: int
    papers: list[PaperOut]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/api/literature/search",
    response_model=LitSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_literature(
    body: LitSearchRequest,
    lit: Annotated[ILitSearch, Depends(get_lit_search)],
) -> LitSearchResponse:
    """
    Search PubMed and Semantic Scholar for papers matching the query.
    Returns deduplicated, ranked results.
    """
    try:
        papers = await lit.search(body.query)
    except Exception as exc:
        logger.exception("Literature search failed: %s", exc)
        papers = []

    papers_out: list[PaperOut] = []
    for p in papers[: body.limit]:
        papers_out.append(
            PaperOut(
                title=p.title,
                authors=p.authors,
                year=p.year,
                url=p.url,
                abstract=p.abstract,
                abstract_summary=p.abstract_summary,
                source=p.source,
            )
        )

    return LitSearchResponse(
        query=body.query,
        count=len(papers_out),
        papers=papers_out,
    )
