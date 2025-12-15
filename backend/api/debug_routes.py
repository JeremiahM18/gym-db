from fastapi import APIRouter, HTTPException

from api.deps import registry, store
from src.gymdb.domain import INFERRED
from src.gymdb.observe.summaries import summarize_inference
from src.gymdb.observe.audit import diff_inference
from src.gymdb.observe.metrics import snapshot_metrics

router = APIRouter(prefix="/debug")

@router.get("/gyms/{gym_id}/inference")
def debug_gym_inference(
    gym_id: str,
    region: str | None = None,
):
    region = region or registry.default_region
    gym = store.get_by_id(region, gym_id)

    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    inferred = gym.get(INFERRED, {})

    return {
        "gym_id": gym_id,
        "region": region,
        "inference": inferred,
        "summary": summarize_inference(inferred),
        "meta": gym.get("inference_meta", {}),
    }

@router.post("/inference/diff")
def debug_inference_diff(payload: dict) -> dict:
    """
    Compare two inference objects and return changed values.
    """
    before = payload.get("before", {}) or {}
    after = payload.get("after", {}) or {}

    return {
        "diff": diff_inference(before, after)
    }

@router.get("/metrics")
def debug_metrics():
    return{"inference_hits": snapshot_metrics()}