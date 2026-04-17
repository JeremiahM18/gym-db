from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from requests import RequestException

from api.auth.dependencies import require_user
from api.deps import get_gym_store
from api.embeddings_views import serialize_gym_embedding_v2
from api.normalizers import serialize_gym, translate_store_error
from api.schemas_v2 import (
    GeocodeResponseV2,
    GymEmbeddingV2,
    GymResponseV2,
    GymsListResponseV2,
)
from api.settings import APISettings, get_settings
from gymdb.gyms.protocol import GymStoreProtocol
from gymdb.gyms.queries import get_gym_by_id, list_gyms
from gymdb.infrastructure.tomtom_client import TomTomClient

# v2 API contract is considered stable
# Changes require schema + test updates

router = APIRouter(prefix="/v2", tags=["gyms"], dependencies=[Depends(require_user)])


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
        raise translate_store_error(exc) from exc

    results = [serialize_gym(gym) for gym in gyms]

    return {
        "api_version": "v2",
        "region": region,
        "count": len(results),
        "has_more": len(results) == limit,
        "results": results,
    }


@router.get("/geocode", response_model=GeocodeResponseV2, tags=["geocode"])
def geocode_location_v2(
    q: str = Query(..., min_length=2, description="City, neighborhood, or place name"),
    limit: int = Query(5, ge=1, le=10),
    settings: APISettings = Depends(get_settings),
):
    if not settings.tomtom_api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "TomTom geocoding is unavailable because TOMTOM_API_KEY is not "
                "configured."
            ),
        )

    client = TomTomClient(
        api_key=settings.tomtom_api_key,
        base_url=settings.tomtom_base_url,
    )
    try:
        places = client.geocode(query=q, limit=limit)
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom geocoding is temporarily unavailable.",
        ) from exc

    return {
        "api_version": "v2",
        "query": q,
        "count": len(places),
        "results": [
            {
                "id": place.id,
                "name": place.name,
                "lat": place.lat,
                "lon": place.lon,
                "address": place.address,
                "city": place.city,
                "country_code": place.country_code,
            }
            for place in places
        ],
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
        raise translate_store_error(exc) from exc

    return [
        serialize_gym_embedding_v2(serialize_gym(gym), region=region) for gym in gyms
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
        raise translate_store_error(exc) from exc
    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")

    return {
        "api_version": "v2",
        "gym": serialize_gym(gym),
    }
