from fastapi import APIRouter, HTTPException

from api.deps import registry, store
from src.gymdb.domain import INFERRED
from src.gymdb.observe.summaries import summarize_inference

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
        "inference": inferred,
        "summary": summarize_inference(inferred),
        "meta": gym.get("inference_meta", {}),
    }
