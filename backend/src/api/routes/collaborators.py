"""
GET /api/collaborators  — LLM-powered collaboration finder.

Given a plan's hypothesis + domain, generates a ranked list of realistic
researcher profiles working in overlapping areas.
"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator

from api.dependencies import get_cache, get_llm_client, get_repo
from domain.ports.cache import ICache
from domain.ports.experiment_repo import IExperimentRepo
from domain.ports.llm_client import ILLMClient

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class CollaboratorProfile(BaseModel):
    name: str
    initials: str
    institution: str
    department: str = ""
    match_pct: int
    topic: str
    recent_publication: str = ""
    domains: list[str] = []

    @field_validator("domains", mode="before")
    @classmethod
    def coerce_domains(cls, v: object) -> list[str]:
        """Accept both a JSON array and a space/comma-separated string from LLM."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # split on comma or whitespace; filter empty tokens
            import re
            return [t.strip() for t in re.split(r"[,\s]+", v) if t.strip()]
        return []


class CollaboratorsResponse(BaseModel):
    plan_id: Optional[str] = None
    query: Optional[str] = None
    collaborators: list[CollaboratorProfile]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are an academic networking assistant for scientific researchers. "
    "Generate realistic researcher profiles that work in overlapping domains to "
    "a given research hypothesis. Profiles should reflect real academic institutions "
    "and plausible research topics."
)


def _build_collab_prompt(hypothesis: str, domain: str) -> str:
    return f"""
Research hypothesis: {hypothesis}
Experiment domain: {domain}

Generate 4 researcher profiles who work in areas highly relevant to this hypothesis.
Each profile should have:
- A realistic academic name
- A real university or research institute
- Specific department
- Match percentage (60-98)
- One-sentence topic description that overlaps with the hypothesis
- A plausible recent publication title
- 2-4 relevant research domains/tags

Respond with a JSON array. Each element must have exactly these keys:
- "name": "Dr./Prof. Full Name"
- "initials": two-letter abbreviation of name
- "institution": university or institute name
- "department": department or lab name
- "match_pct": integer 60-98
- "topic": one-sentence research focus
- "recent_publication": a plausible paper title
- "domains": array of 2-4 short domain tags

Return only valid JSON array, no markdown fences, no extra text.
"""


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get("/api/collaborators", response_model=CollaboratorsResponse)
async def find_collaborators(
    llm: Annotated[ILLMClient, Depends(get_llm_client)],
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    cache: Annotated[ICache, Depends(get_cache)],
    plan_id: Optional[UUID] = Query(default=None),
    query: Optional[str] = Query(default=None),
    domain: str = Query(default="other"),
) -> CollaboratorsResponse:
    """
    Return AI-generated researcher profiles relevant to a plan or search query.
    Pass either plan_id (to use the saved hypothesis) or query (free-form text).
    """
    hypothesis = query or ""
    plan_id_str: Optional[str] = None

    if plan_id:
        plan = await repo.get(plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan {plan_id} not found.",
            )
        hypothesis = plan.refined_hypothesis or plan.hypothesis
        domain = plan.experiment_domain.value
        plan_id_str = str(plan_id)

    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either plan_id or query parameter.",
        )

    cache_key = f"collab:{hash(hypothesis[:100])}:{domain}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info("Collaborators cache hit")
        return CollaboratorsResponse(**json.loads(cached))

    prompt = _build_collab_prompt(hypothesis, domain)
    raw = await llm.complete(_SYSTEM, prompt)

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0]
        profiles_data = json.loads(cleaned.strip())
        if not isinstance(profiles_data, list):
            profiles_data = profiles_data.get("collaborators", [])
    except Exception as exc:
        logger.exception("Failed to parse collaborators output: %s", exc)
        profiles_data = []

    profiles: list[CollaboratorProfile] = []
    for p in profiles_data:
        try:
            profiles.append(CollaboratorProfile(**p))
        except Exception:
            continue

    result = CollaboratorsResponse(
        plan_id=plan_id_str,
        query=query,
        collaborators=profiles,
    )

    await cache.set(cache_key, result.model_dump_json(), ttl_seconds=3600)
    return result
