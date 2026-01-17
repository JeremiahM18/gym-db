from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends


from api.auth.dependencies import require_admin
from api.auth.internal import require_internal_enabled

from api.deps import get_gym_store
from src.gymdb.gyms.store_postgres import PostgresGymStore

from src.gymdb.domain import INFERRED
from src.gymdb.observe.summaries import summarize_inference
from src.gymdb.observe.audit import diff_inference
from src.gymdb.observe.metrics import snapshot_metrics

router = APIRouter(
    prefix="/debug", 
    tags=["debug"],
    include_in_schema=False,
    dependencies=[
        Depends(require_internal_enabled),
        Depends(require_admin),
    ],
    
    )

# Debug Gym Endpoints


@router.get("/gyms/{gym_id}/inference")
def debug_gym_inference(
    gym_id: str,
    region: str | None = None,
    store: PostgresGymStore = Depends(get_gym_store),
):
    """
    Debug-only endpoint exposing raw inference data for a gym.

    Notes:
    - NOT part of the public API contract
    - Auth-gated via internal + admin dependencies
    - Uses the same GymStore as the public API to avoid divergence
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

# Inference Debug Utilities

@router.post("/inference/diff")
def debug_inference_diff(payload: dict) -> dict:
    """
    Compare two inference objects and return changed values.

    Stateless by design (no dataset or DB access).
    Intended for debugging inference evolution.
    """
    before = payload.get("before") or {}
    after = payload.get("after") or {}

    return {
        "diff": diff_inference(before, after)
    }

@router.get(
    "/metrics",
    include_in_schema=False,
)
def debug_metrics():
    """
    Snapshot inference metrics.
    
    Safe to call without DB or dataset access.
    """
    return{"inference_hits": snapshot_metrics()}