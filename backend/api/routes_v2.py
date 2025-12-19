from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, Depends

from api.deps import get_store
from api.store import GymStore
from api.schemas_v2 import (
    GymResponseV2,
    GymsListResponseV2,
    GymEmbeddingV2
)
from api.embeddings_views import serialize_gym_embedding_v2

from src.gymdb.domain import INFERRED
from src.gymdb.observe.summaries import summarize_inference


router = APIRouter(prefix="/v2", tags=["gyms"])

# --- Helpers ---

def _serialize_inference_v2(gym: dict) -> dict:
    """
    v2 inference serialization.

    Contract:
    - inference is never empty
    - every entry has confidence + source
    """
    inferred = gym.get(INFERRED, {})
    out: dict = {}

    for key, result in inferred.items():
        if not isinstance(result, dict):
            continue

        out[key] = {
            "value": result.get("value"),
            "confidence": result.get("confidence", 1.0),
            "source": result.get("source", "rule"),
            "reasons": result.get("reasons", []),
        }

    # Hard Contrace: Never empty
    if not out:
        out["unknown"] = {
            "value": False,
            "confidence": 0.0,
            "source": "none",
            "reasons": ["no inference rules applied"],
        }

    return out

# --- Routes ---

@router.get("/gyms", response_model=GymsListResponseV2)
def list_gyms_v2(
    region: str | None = None,
    min_conf: float | None = Query(None, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    store: GymStore = Depends(get_store)
):
    region = region or store.default_region

    gyms = store.filter(
        region=region,
        min_conf=min_conf,
        limit=limit,
        offset=offset,
    )

    results = []
    for g in gyms:
        out = dict(g)
        out["inference"] = _serialize_inference_v2(g)
        out["inference_summary"] = summarize_inference(g.get(INFERRED, {}))
        out.pop(INFERRED, None)
        results.append(out)

    return {
        "api_version": "v2",
        "region": region,
        "count": len(results),
        "results": results,
    }
    
@router.get(
    "/gyms/embeddings",
    response_model=list[GymEmbeddingV2],
    tags=["embeddings"],
)
def list_gym_embeddings_v2(
    region: str | None = None,
    store: GymStore = Depends(get_store),
):
    region = region or store.default_region

    gyms = store.filter(region=region)

    results = []
    for g in gyms:
        out = dict(g)
        out["inference"] = _serialize_inference_v2(g)
        out["inference_summary"] = summarize_inference(g.get(INFERRED, {}))
        out.pop(INFERRED, None)
        
        results.append(
            serialize_gym_embedding_v2(out, region=region)  
        )

    return results

@router.get("/gyms/{gym_id}", response_model=GymResponseV2)
def get_gym_v2(
    gym_id: str,
    region: str | None = None,
    store: GymStore = Depends(get_store),
):
    region = region or store.default_region

    gym = store.get_by_id(region, gym_id)
    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    out = dict(gym)
    out["inference"] = _serialize_inference_v2(gym)
    out["inference_summary"] = summarize_inference(gym.get(INFERRED, {}))
    out.pop(INFERRED, None)

    return {
        "api_version": "v2",
        "gym": out,
    }