from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from api.normalizers import hydrate_domain_gym, serialize_domain_gym
from gymdb.application.coverage import apply_osm_confirmation
from gymdb.domain.inference import apply_inference
from gymdb.domain.processing import haversine_meters
from gymdb.domain.scoring import compute_confidence
from gymdb.infrastructure.live_search_cache import write_cached_elements
from gymdb.infrastructure.live_search_sessions import (
    load_live_search_session,
    replace_live_search_session,
)
from gymdb.infrastructure.overpass_client import OverpassUnavailableError, fetch_gyms
from gymdb.observe.metrics import record_enrich_outcome

logger = logging.getLogger(__name__)


def background_overpass_enrich(
    *,
    lat: float,
    lon: float,
    radius_m: int,
    origin_name: str,
    cache_root: Path,
    timeout_seconds: int,
    max_attempts: int,
    search_id: str | None = None,
    session_root: Path | None = None,
) -> None:
    """
    Fetch OSM gyms for the given search area and write them to the local cache.

    Called as a FastAPI BackgroundTask after the live-search response is sent.
    All failures are logged and swallowed — the hot path must never be blocked.
    """
    try:
        elements = fetch_gyms(
            radius_m,
            lat,
            lon,
            timeout_seconds=timeout_seconds,
            max_attempts=max_attempts,
        )
    except OverpassUnavailableError as exc:
        logger.warning("background_overpass_enrich: Overpass unavailable — %s", exc)
        if search_id and session_root:
            _mark_live_search_session_failed(
                session_root=session_root,
                search_id=search_id,
            )
        record_enrich_outcome(success=False)
        return
    except Exception:
        logger.exception("background_overpass_enrich: unexpected error")
        if search_id and session_root:
            _mark_live_search_session_failed(
                session_root=session_root,
                search_id=search_id,
            )
        record_enrich_outcome(success=False)
        return

    origin = {
        "name": origin_name,
        "address": origin_name,
        "lat": lat,
        "lon": lon,
    }
    try:
        write_cached_elements(
            cache_root,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            origin=origin,
            elements=elements,
        )
        logger.debug(
            "background_overpass_enrich: cached %d elements for %.3f,%.3f r=%d",
            len(elements),
            lat,
            lon,
            radius_m,
        )
        record_enrich_outcome(success=True)
    except Exception:
        logger.exception("background_overpass_enrich: cache write failed")
        if search_id and session_root:
            _mark_live_search_session_failed(
                session_root=session_root,
                search_id=search_id,
            )
        record_enrich_outcome(success=False, write_failed=True)
        return

    if search_id and session_root:
        try:
            _update_live_search_session(
                session_root=session_root,
                search_id=search_id,
                osm_elements=elements,
            )
        except Exception:
            logger.exception(
                "background_overpass_enrich: live-search session update failed"
            )
            _mark_live_search_session_failed(
                session_root=session_root,
                search_id=search_id,
            )


def _update_live_search_session(
    *,
    session_root: Path,
    search_id: str,
    osm_elements: list[dict[str, Any]],
) -> None:
    session = load_live_search_session(session_root, search_id)
    if session is None or session.status != "enriching":
        return

    origin = session.response.get("origin")
    origin_lat = origin.get("lat") if isinstance(origin, dict) else None
    origin_lon = origin.get("lon") if isinstance(origin, dict) else None
    if not isinstance(origin_lat, int | float) or not isinstance(
        origin_lon, int | float
    ):
        replace_live_search_session(
            session_root,
            session,
            status="ready",
            enrichment_status="failed",
        )
        return

    persisted_results = session.response.get("results")
    if not isinstance(persisted_results, list):
        replace_live_search_session(
            session_root,
            session,
            status="ready",
            enrichment_status="failed",
        )
        return

    gyms = [hydrate_domain_gym(result) for result in persisted_results]
    apply_osm_confirmation(gyms, osm_elements)

    enriched_results: list[dict] = []
    for gym in gyms:
        compute_confidence(gym)
        apply_inference(gym)
        enriched_results.append(
            {
                **serialize_domain_gym(gym),
                "distance_m": haversine_meters(
                    float(origin_lat),
                    float(origin_lon),
                    gym.lat,
                    gym.lon,
                ),
            }
        )

    replace_live_search_session(
        session_root,
        session,
        response={
            **session.response,
            "count": len(enriched_results),
            "results": enriched_results,
        },
        status="ready",
        enrichment_status="completed",
    )


def _mark_live_search_session_failed(
    *,
    session_root: Path,
    search_id: str,
) -> None:
    session = load_live_search_session(session_root, search_id)
    if session is None or session.status != "enriching":
        return
    replace_live_search_session(
        session_root,
        session,
        status="ready",
        enrichment_status="failed",
    )
