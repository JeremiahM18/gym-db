from __future__ import annotations

import logging

from gymdb.infrastructure.live_search_cache import write_cached_elements
from gymdb.infrastructure.overpass_client import OverpassUnavailableError, fetch_gyms

logger = logging.getLogger(__name__)


def background_overpass_enrich(
    *,
    lat: float,
    lon: float,
    radius_m: int,
    origin_name: str,
    cache_root,
    timeout_seconds: int,
    max_attempts: int,
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
        return
    except Exception as exc:
        logger.warning("background_overpass_enrich: unexpected error — %s", exc)
        return

    try:
        write_cached_elements(
            cache_root,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            origin={"name": origin_name, "address": origin_name, "lat": lat, "lon": lon},
            elements=elements,
        )
        logger.debug(
            "background_overpass_enrich: cached %d elements for %.3f,%.3f r=%d",
            len(elements),
            lat,
            lon,
            radius_m,
        )
    except Exception as exc:
        logger.warning("background_overpass_enrich: cache write failed — %s", exc)
