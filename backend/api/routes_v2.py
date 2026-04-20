from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from requests import RequestException

from api.auth.dependencies import require_user
from api.deps import enforce_live_search_rate_limit, get_gym_store, get_tomtom_client
from api.embeddings_views import serialize_gym_embedding_v2
from api.normalizers import serialize_domain_gym, serialize_gym, translate_store_error
from api.schemas_v2 import (
    GeocodeResponseV2,
    GymEmbeddingV2,
    GymResponseV2,
    GymsListResponseV2,
    LiveGymSearchResponseV2,
)
from gymdb.application.coverage import apply_tomtom_coverage
from gymdb.domain.inference import apply_inference
from gymdb.domain.processing import (
    compute_gym_id,
    deduplicate,
    haversine_meters,
    normalize_name,
)
from gymdb.domain.scoring import compute_confidence
from gymdb.gyms.protocol import GymStoreProtocol
from gymdb.gyms.queries import get_gym_by_id, list_gyms
from gymdb.infrastructure.overpass_client import OverpassUnavailableError, fetch_gyms
from gymdb.infrastructure.tomtom_client import TomTomClient

# v2 API contract is considered stable
# Changes require schema + test updates

router = APIRouter(prefix="/v2", tags=["gyms"], dependencies=[Depends(require_user)])


_BROAD_LIVE_SEARCH_TERMS = {
    "",
    "gym",
    "gyms",
    "fitness",
    "fitness_center",
    "fitness_centre",
}


def _matches_live_query(gym, query: str) -> bool:
    normalized_query = normalize_name(query)
    if normalized_query in _BROAD_LIVE_SEARCH_TERMS:
        return True

    search_parts = [
        gym.name,
        gym.norm_name,
        *(str(value) for value in gym.tags.values()),
        *(str(result.value) for result in gym.inferred.values()),
    ]
    search_blob = normalize_name(" ".join(search_parts))
    return normalized_query in search_blob


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
            limit=limit + 1,
            offset=offset,
        )
    except Exception as exc:
        raise translate_store_error(exc) from exc

    has_more = len(gyms) > limit
    results = [serialize_gym(gym) for gym in gyms[:limit]]

    return {
        "api_version": "v2",
        "region": region,
        "count": len(results),
        "has_more": has_more,
        "results": results,
    }


@router.get("/geocode", response_model=GeocodeResponseV2, tags=["geocode"])
async def geocode_location_v2(
    q: str = Query(..., min_length=2, description="City, neighborhood, or place name"),
    limit: int = Query(5, ge=1, le=10),
    tomtom_client: TomTomClient | None = Depends(get_tomtom_client),
):
    if tomtom_client is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "TomTom geocoding is unavailable because TOMTOM_API_KEY is not "
                "configured."
            ),
        )

    try:
        places = await asyncio.to_thread(tomtom_client.geocode, query=q, limit=limit)
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
    "/live/search",
    response_model=LiveGymSearchResponseV2,
    tags=["live-search"],
)
async def live_search_gyms_v2(
    place: str = Query(..., min_length=2, description="City, neighborhood, or place"),
    q: str = Query(
        "gym",
        min_length=1,
        description="Gym name, brand, or search term. Defaults to gym.",
    ),
    radius_m: int = Query(25_000, ge=500, le=400_000),
    limit: int = Query(25, ge=1, le=50),
    _: None = Depends(enforce_live_search_rate_limit),
    tomtom_client: TomTomClient | None = Depends(get_tomtom_client),
):
    if tomtom_client is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "TomTom live search is unavailable because TOMTOM_API_KEY is not "
                "configured."
            ),
        )

    try:
        origins = await asyncio.to_thread(tomtom_client.geocode, query=place, limit=1)
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom place resolution is temporarily unavailable.",
        ) from exc

    if not origins:
        raise HTTPException(
            status_code=404,
            detail=f'No place match found for "{place}".',
        )

    origin = origins[0]
    search_query = q.strip() or "gym"

    try:
        elements = await asyncio.to_thread(fetch_gyms, radius_m, origin.lat, origin.lon)
    except OverpassUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    gyms = deduplicate(elements)
    for gym in gyms:
        gym.id = compute_gym_id(gym.norm_name, gym.lat, gym.lon)

    try:
        places = await asyncio.to_thread(
            tomtom_client.search_gyms,
            lat=origin.lat,
            lon=origin.lon,
            radius_m=radius_m,
            limit=max(len(gyms) * 2, 100),
        )
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom live verification is temporarily unavailable.",
        ) from exc

    apply_tomtom_coverage(gyms, places)

    for gym in gyms:
        compute_confidence(gym)
        apply_inference(gym)

    filtered_gyms = [
        gym for gym in gyms if _matches_live_query(gym, search_query)
    ]
    filtered_gyms.sort(
        key=lambda gym: haversine_meters(origin.lat, origin.lon, gym.lat, gym.lon)
    )
    limited_gyms = filtered_gyms[:limit]

    return {
        "api_version": "v2",
        "query": search_query,
        "place_query": place,
        "count": len(limited_gyms),
        "radius_m": radius_m,
        "origin": {
            "id": origin.id,
            "name": origin.name,
            "lat": origin.lat,
            "lon": origin.lon,
            "address": origin.address,
            "city": origin.city,
            "country_code": origin.country_code,
        },
        "results": [
            {
                **serialize_domain_gym(gym),
                "distance_m": haversine_meters(
                    origin.lat,
                    origin.lon,
                    gym.lat,
                    gym.lon,
                ),
            }
            for gym in limited_gyms
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
