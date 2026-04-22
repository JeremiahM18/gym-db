from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from requests import RequestException

from api.auth.dependencies import require_user
from api.background_tasks import background_overpass_enrich
from api.deps import enforce_live_search_rate_limit, get_gym_store, get_tomtom_client
from api.embeddings_views import serialize_gym_embedding_v2
from api.normalizers import serialize_domain_gym, serialize_gym, translate_store_error
from gymdb.application.coverage import apply_osm_confirmation
from api.schemas_v2 import (
    GeocodeResponseV2,
    GymEmbeddingV2,
    GymResponseV2,
    GymsListResponseV2,
    LiveGymSearchResponseV2,
)
from api.settings import APISettings, get_settings
from gymdb.domain.inference import apply_inference
from gymdb.domain.processing import (
    compute_gym_id,
    deduplicate,
    haversine_meters,
    normalize_name,
)
from gymdb.domain.provenance import MatchStatus
from gymdb.domain.scoring import compute_confidence
from gymdb.observe.metrics import (
    record_cache_probe,
    record_enrich_dispatched,
    record_osm_confirmation_outcomes,
)
from gymdb.gyms.protocol import GymStoreProtocol
from gymdb.gyms.queries import get_gym_by_id, list_gyms
from gymdb.infrastructure.live_search_cache import load_cached_elements
from gymdb.infrastructure.tomtom_client import TomTomClient, TomTomPlace

# v2 API contract is considered stable
# Changes require schema + test updates

router = APIRouter(prefix="/v2", tags=["gyms"], dependencies=[Depends(require_user)])


def _tomtom_place_to_element(place: TomTomPlace) -> dict[str, Any]:
    tags: dict[str, Any] = {"name": place.name, "leisure": "fitness_centre"}
    if place.address:
        tags["addr:full"] = place.address
    if place.city:
        tags["addr:city"] = place.city
    if place.url:
        tags["website"] = place.url
    return {
        "type": "tomtom",
        "id": place.id,
        "lat": place.lat,
        "lon": place.lon,
        "tags": tags,
    }


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
    settings: APISettings = Depends(get_settings),
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
        async with asyncio.timeout(settings.live_search_upstream_timeout_seconds):
            places = await asyncio.to_thread(
                tomtom_client.geocode,
                query=q,
                limit=limit,
            )
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom geocoding is temporarily unavailable.",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom geocoding timed out.",
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
    _: None = Depends(enforce_live_search_rate_limit),
    tomtom_client: TomTomClient | None = Depends(get_tomtom_client),
    settings: APISettings = Depends(get_settings),
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
        async with asyncio.timeout(settings.live_search_upstream_timeout_seconds):
            origins = await asyncio.to_thread(
                tomtom_client.geocode,
                query=place,
                limit=1,
            )
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom place resolution is temporarily unavailable.",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom place resolution timed out.",
        ) from exc

    if not origins:
        raise HTTPException(
            status_code=404,
            detail=f'No place match found for "{place}".',
        )

    origin = origins[0]
    search_query = q.strip() or "gym"

    # Check whether a fresh OSM cache entry already covers this search area.
    # The cached elements are not yet used for confirmation (Step 8); this probe
    # determines whether we need to schedule a background Overpass fetch.
    cached_osm = load_cached_elements(
        settings.live_search_cache_root,
        lat=origin.lat,
        lon=origin.lon,
        radius_m=radius_m,
    )
    cache_is_fresh = (
        cached_osm is not None
        and cached_osm.age_seconds < settings.live_search_cache_ttl_seconds
    )
    record_cache_probe(cache_exists=cached_osm is not None, is_fresh=cache_is_fresh)

    try:
        async with asyncio.timeout(settings.live_search_upstream_timeout_seconds):
            places = await asyncio.to_thread(
                tomtom_client.search_gyms,
                lat=origin.lat,
                lon=origin.lon,
                radius_m=radius_m,
                limit=100,
            )
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom gym search is temporarily unavailable.",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="TomTom gym search timed out.",
        ) from exc

    elements = [_tomtom_place_to_element(p) for p in places]
    gyms = deduplicate(elements)
    for gym in gyms:
        gym.id = compute_gym_id(gym.norm_name, gym.lat, gym.lon)
        gym.source_provenance = {
            "primary": "tomtom",
            "confirmed_by": [],
            "match_status": MatchStatus.TOMTOM_ONLY.value,
            "external_refs": {},
        }

    if cache_is_fresh and cached_osm is not None:
        apply_osm_confirmation(gyms, cached_osm.elements)

    _confirmed = sum(
        1 for g in gyms
        if (g.source_provenance or {}).get("match_status") == MatchStatus.OSM_CONFIRMED.value
    )
    _nearby = sum(
        1 for g in gyms
        if (g.source_provenance or {}).get("match_status") == MatchStatus.OSM_NEARBY.value
    )
    record_osm_confirmation_outcomes(
        osm_confirmed=_confirmed,
        osm_nearby=_nearby,
        tomtom_only=len(gyms) - _confirmed - _nearby,
    )

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

    # Schedule Overpass enrichment after the response is sent, unless the cache
    # is already fresh for this search area.
    if not cache_is_fresh:
        background_tasks.add_task(
            background_overpass_enrich,
            lat=origin.lat,
            lon=origin.lon,
            radius_m=radius_m,
            origin_name=origin.address or origin.name,
            cache_root=settings.live_search_cache_root,
            timeout_seconds=settings.live_search_overpass_timeout_seconds,
            max_attempts=settings.live_search_overpass_max_attempts,
        )
        record_enrich_dispatched()

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
