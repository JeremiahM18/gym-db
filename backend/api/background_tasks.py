from __future__ import annotations

import logging
from pathlib import Path

from gymdb.infrastructure.live_search_cache import write_cached_elements
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
        record_enrich_outcome(success=False)
        return
    except Exception:
        logger.exception("background_overpass_enrich: unexpected error")
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
        record_enrich_outcome(success=False, write_failed=True)
