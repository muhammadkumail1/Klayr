"""
POST /api/optimize  — LLM-powered cost optimization for an experiment plan.

Given a saved plan, the LLM proposes alternative suppliers/strategies for
each reagent/material line that reduces cost while preserving scientific validity.
"""
from __future__ import annotations

import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_cache, get_llm_client, get_repo
from domain.ports.cache import ICache
from domain.ports.experiment_repo import IExperimentRepo
from domain.ports.llm_client import ILLMClient

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    plan_id: UUID
    mode: str = "standard"   # "lean" | "standard" | "premium"


class OptimizationItem(BaseModel):
    item: str
    original_supplier: str
    alt_supplier: str
    original_cost: float
    optimized_cost: float
    savings_pct: float
    risk: str            # "Low" | "Medium" | "High"
    notes: str = ""


class OptimizeResponse(BaseModel):
    plan_id: str
    mode: str
    optimizations: list[OptimizationItem]
    total_original_usd: float
    total_optimized_usd: float
    total_savings_pct: float


# ---------------------------------------------------------------------------
# System + prompt
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are a senior laboratory procurement specialist and research budget advisor. "
    "Your task is to propose cost-saving alternatives for laboratory materials and reagents "
    "without compromising scientific validity or experimental reproducibility."
)


def _build_optimize_prompt(materials: list[dict], mode: str) -> str:
    mode_guidance = {
        "lean": "Maximize cost reduction. Prefer generic suppliers. Accept medium risk tradeoffs.",
        "standard": "Balance cost and quality. Prefer reputable suppliers with good reviews. Low to medium risk.",
        "premium": "Preserve quality. Only suggest alternatives from top-tier suppliers. Minimal risk.",
    }
    mat_lines = "\n".join(
        f"- {m.get('name', 'Unknown')}: supplier={m.get('supplier', 'Unknown')}, "
        f"qty={m.get('quantity', '1')}, total_cost=${m.get('total_cost_usd', 0):.2f}"
        for m in materials
    )
    return f"""
Optimization mode: {mode} — {mode_guidance.get(mode, mode_guidance['standard'])}

Materials list:
{mat_lines}

For each material, propose the best cost-saving alternative.
Respond with a JSON array. Each element must have exactly these keys:
- "item": original item name
- "original_supplier": current supplier
- "alt_supplier": proposed alternative supplier
- "original_cost": original total cost as number
- "optimized_cost": proposed cost as number
- "savings_pct": percentage saved as number (0-100)
- "risk": "Low" | "Medium" | "High"
- "notes": one sentence justification

Return only valid JSON array, no markdown fences, no extra text.
"""


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/api/optimize", response_model=OptimizeResponse)
async def optimize_plan(
    body: OptimizeRequest,
    llm: Annotated[ILLMClient, Depends(get_llm_client)],
    repo: Annotated[IExperimentRepo, Depends(get_repo)],
    cache: Annotated[ICache, Depends(get_cache)],
) -> OptimizeResponse:
    """
    Use LLM to generate cost-optimized alternatives for every material in a saved plan.
    Results are cached per (plan_id, mode) for 2 hours.
    """
    cache_key = f"optimize:{body.plan_id}:{body.mode}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info("Optimize cache hit for plan %s mode %s", body.plan_id, body.mode)
        return OptimizeResponse(**json.loads(cached))

    plan = await repo.get(body.plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {body.plan_id} not found.",
        )

    materials_data = [m.model_dump() for m in plan.materials]
    if not materials_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This plan has no materials to optimize.",
        )

    prompt = _build_optimize_prompt(materials_data, body.mode)
    raw = await llm.complete(_SYSTEM, prompt)

    # Parse LLM output
    try:
        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0]
        items_data = json.loads(cleaned.strip())
        if not isinstance(items_data, list):
            items_data = items_data.get("optimizations", [])
    except Exception as exc:
        logger.exception("Failed to parse LLM optimize output: %s", exc)
        items_data = []

    optimizations: list[OptimizationItem] = []
    for item in items_data:
        try:
            optimizations.append(OptimizationItem(**item))
        except Exception:
            continue

    # Compute totals
    total_original = sum(o.original_cost for o in optimizations)
    total_optimized = sum(o.optimized_cost for o in optimizations)
    savings_pct = (
        round((1 - total_optimized / total_original) * 100, 1)
        if total_original > 0
        else 0.0
    )

    result = OptimizeResponse(
        plan_id=str(body.plan_id),
        mode=body.mode,
        optimizations=optimizations,
        total_original_usd=round(total_original, 2),
        total_optimized_usd=round(total_optimized, 2),
        total_savings_pct=savings_pct,
    )

    await cache.set(cache_key, result.model_dump_json(), ttl_seconds=7200)
    return result
