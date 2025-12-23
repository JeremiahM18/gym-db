from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from api.deps import get_store
from api.store import GymStore

from src.gymdb.domain import INFERRED
from src.gymdb.observe.summaries import summarize_inference
from src.gymdb.observe.audit import diff_inference
from src.gymdb.observe.metrics import snapshot_metrics

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/gyms/{gym_id}/inference")
def debug_gym_inference(
    gym_id: str,
    region: str | None = None,
    store: GymStore = Depends(get_store),
):
    """
    Debug view of raw inference artifacts.

    This endpoint intentionally exposes internal structures.
    It is NOT part of the public API contract.
    """
    region = region or store.default_region
    gym = store.get_by_id(region, gym_id)

    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    inferred = gym.get(INFERRED)
    if inferred is None:
        raise HTTPException(
            status_code=500,
            detail="Inference missing from gym record",
        )
    inference_meta = gym.get("inference_meta")
    if inference_meta is None:
        raise HTTPException(
            status_code=500,
            detail="Inference metadata missing from gym record",
        )

    return {
        "gym_id": gym_id,
        "region": region,
        "inference": inferred,      # typed InferenceResult objects
        "summary": summarize_inference(inferred),
        "meta": inference_meta,
    }

@router.post("/inference/diff")
def debug_inference_diff(payload: dict) -> dict:
    """
    Compare two inference objects and return changed values.

    Stateless by design (no store access).
    Intended for debugging inference evolution.
    """
    before = payload.get("before") or {}
    after = payload.get("after") or {}

    return {
        "diff": diff_inference(before, after)
    }

@router.get("/metrics")
def debug_metrics():
    """
    Snapshot inference metrics.
    Safe to call without DB or dataset access.
    """
    return{"inference_hits": snapshot_metrics()}