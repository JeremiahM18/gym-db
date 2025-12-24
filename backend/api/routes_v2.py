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
from api.normalizers import normalize_inference_meta, normalize_inference
from api.auth.dependencies import require_user

from src.gymdb.observe.summaries import summarize_inference

# v2 API contract is considered stable
# Changes require schema + test updates

router = APIRouter(prefix="/v2", tags=["gyms"], dependencies=[Depends(require_user)],)


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

        raw = out.pop("inferred", None) or out.get("inference")
        out["inference"] = normalize_inference(raw)

        out["inference_meta"] = normalize_inference_meta(
            g.get("inference_meta")
        )

        out["inference_summary"] = summarize_inference(out["inference"])
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
        inferred = normalize_inference(
            g.get("inferred") or g.get("inference")
        )

        out = dict(g)
        out["inference"] = inferred
        out["inference_meta"] = normalize_inference_meta(
            g.get("inference_meta")
        )

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

    raw = out.pop("inferred", None) or out.get("inference")
    out["inference"] = normalize_inference(raw)

    out["inference_meta"] = normalize_inference_meta(
        gym.get("inference_meta")
    )

    out["inference_summary"] = summarize_inference(out["inference"])

    return {
        "api_version": "v2",
        "gym": out,
    }