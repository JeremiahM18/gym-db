from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

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
    LiveGymSearchResponseV2,
)
from api.settings import APISettings, get_settings
from gymdb.gyms.protocol import GymStoreProtocol
from gymdb.gyms.queries import get_gym_by_id, list_gyms
from gymdb.infrastructure.tomtom_client import TomTomClient

# v2 API contract is considered stable
# Changes require schema + test updates

router = APIRouter(prefix="/v2", tags=["gyms"], dependencies=[Depends(require_user)])


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_m = 6_371_000
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    origin_lat = radians(lat1)
    target_lat = radians(lat2)

    a = (
        sin(d_lat / 2) ** 2
        + cos(origin_lat) * cos(target_lat) * sin(d_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return earth_radius_m * c


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
    "/live/search",
    response_model=LiveGymSearchResponseV2,
    tags=["live-search"],
)
def live_search_gyms_v2(
    place: str = Query(..., min_length=2, description="City, neighborhood, or place"),
    q: str = Query(
        "gym",
        min_length=1,
        description="Gym name, brand, or search term. Defaults to gym.",
    ),
    radius_m: int = Query(25_000, ge=500, le=100_000),
    limit: int = Query(25, ge=1, le=50),
    settings: APISettings = Depends(get_settings),
):
    if not settings.tomtom_api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "TomTom live search is unavailable because TOMTOM_API_KEY is not "
                "configured."
            ),
        )

    client = TomTomClient(
        api_key=settings.tomtom_api_key,
        base_url=settings.tomtom_base_url,
    )

    try:
        origins = client.geocode(query=place, limit=1)
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
        places = client.search(
            query=search_query,
            lat=origin.lat,
            lon=origin.lon,
            radius_m=radius_m,
            geobias_lat=origin.lat,
            geobias_lon=origin.lon,
            limit=limit,
        )
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom live gym search is temporarily unavailable.",
        ) from exc

    return {
        "api_version": "v2",
        "query": search_query,
        "place_query": place,
        "count": len(places),
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
                "id": place_result.id,
                "name": place_result.name,
                "lat": place_result.lat,
                "lon": place_result.lon,
                "address": place_result.address,
                "city": place_result.city,
                "country_code": place_result.country_code,
                "distance_m": _haversine_meters(
                    origin.lat,
                    origin.lon,
                    place_result.lat,
                    place_result.lon,
                ),
                "url": place_result.url,
                "provider": "tomtom",
            }
            for place_result in places
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
