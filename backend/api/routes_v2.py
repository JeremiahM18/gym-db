from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth.dependencies import require_user
from api.deps import get_gym_store
from api.embeddings_views import serialize_gym_embedding_v2
from api.normalizers import (
    normalize_inference,
    normalize_inference_meta,
    normalize_source_provenance,
)
from api.schemas_v2 import GymEmbeddingV2, GymResponseV2, GymsListResponseV2
from gymdb.domain.processing import normalize_name
from gymdb.gyms.protocol import GymStoreProtocol
from gymdb.gyms.queries import get_gym_by_id, list_gyms
from gymdb.observe.summaries import summarize_inference

# v2 API contract is considered stable
# Changes require schema + test updates

router = APIRouter(prefix="/v2", tags=["gyms"], dependencies=[Depends(require_user)])


def _translate_store_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=500, detail="Internal server error")


def _serialize_gym(gym: dict) -> dict:
    out = dict(gym)
    out["norm_name"] = str(out.get("norm_name") or normalize_name(out["name"]))

    raw = out.pop("inferred", None) or out.get("inference")
    out["inference"] = normalize_inference(raw)
    out["inference_meta"] = normalize_inference_meta(gym.get("inference_meta"))
    out["source_provenance"] = normalize_source_provenance(
        gym.get("source_provenance")
    )
    out["inference_summary"] = summarize_inference(out["inference"])
    return out


@router.get("/gyms", response_model=GymsListResponseV2)
def list_gyms_v2(
    region: str | None = None,
    min_conf: float | None = Query(None, ge=0.0, le=1.0),
    tier: str | None = None,
    specialty: str | None = None,
    lifter_friendly: bool | None = None,
    is_24_7: bool | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: float | None = Query(None, gt=0.0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    store: GymStoreProtocol = Depends(get_gym_store),
):
    region = region or store.default_region

    try:
        gyms = list_gyms(
            store=store,
            region=region,
            min_conf=min_conf,
            tier=tier,
            specialty=specialty,
            lifter_friendly=lifter_friendly,
            is_24_7=is_24_7,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise _translate_store_error(exc) from exc

    results = [_serialize_gym(gym) for gym in gyms]

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
    store: GymStoreProtocol = Depends(get_gym_store),
):
    region = region or store.default_region

    try:
        gyms = list_gyms(
            store=store,
            region=region,
            min_conf=None,
            limit=500,
            offset=0,
        )
    except Exception as exc:
        raise _translate_store_error(exc) from exc

    return [
        serialize_gym_embedding_v2(_serialize_gym(gym), region=region) for gym in gyms
    ]


@router.get("/gyms/{gym_id}", response_model=GymResponseV2)
def get_gym_v2(
    gym_id: str,
    region: str | None = None,
    store: GymStoreProtocol = Depends(get_gym_store),
):
    region = region or store.default_region

    try:
        gym = get_gym_by_id(store=store, region=region, gym_id=gym_id)
    except Exception as exc:
        raise _translate_store_error(exc) from exc
    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")

    return {
        "api_version": "v2",
        "gym": _serialize_gym(gym),
    }
