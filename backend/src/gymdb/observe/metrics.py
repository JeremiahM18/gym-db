from collections import Counter

_inference_hits: Counter[str] = Counter()
_live_search: Counter[str] = Counter()


def record_inference_hits(inferred: dict[str, dict]) -> None:
    """
    Count which inference keys are produced.
    Expects normalized inference dicts (v2 contracts).
    """
    for key, result in inferred.items():
        if result.get("value") is not None:
            _inference_hits[key] += 1


def snapshot_metrics() -> dict[str, int]:
    """Snapshot current inference hit counts."""
    return dict(_inference_hits)


# ---------------------------------------------------------------------------
# Live search telemetry
# All functions are side-effect only — pure counter increments, no I/O.
# ---------------------------------------------------------------------------


def record_cache_probe(*, cache_exists: bool, is_fresh: bool) -> None:
    """Record the result of a live-search OSM cache probe."""
    if not cache_exists:
        _live_search["cache_miss"] += 1
    elif is_fresh:
        _live_search["cache_hit"] += 1
    else:
        _live_search["cache_stale"] += 1


def record_enrich_dispatched() -> None:
    """Record that a background Overpass enrichment task was scheduled."""
    _live_search["enrich_dispatched"] += 1


def record_enrich_outcome(*, success: bool, write_failed: bool = False) -> None:
    """
    Record the outcome of a background Overpass enrichment task.

    success=True  → Overpass fetch and cache write both succeeded.
    success=False, write_failed=True  → fetch succeeded but cache write failed.
    success=False, write_failed=False → Overpass fetch failed (unavailable or error).
    """
    if success:
        _live_search["enrich_success"] += 1
    elif write_failed:
        _live_search["enrich_write_failure"] += 1
    else:
        _live_search["enrich_failure"] += 1


def record_osm_confirmation_outcomes(
    *, osm_confirmed: int, osm_nearby: int, tomtom_only: int
) -> None:
    """Record per-request gym-level OSM confirmation tier distribution."""
    _live_search["osm_confirmed"] += osm_confirmed
    _live_search["osm_nearby"] += osm_nearby
    _live_search["tomtom_only"] += tomtom_only


def snapshot_live_search_metrics() -> dict[str, int]:
    """
    Snapshot current live-search event counts.

    Returns a fixed set of keys (zero-valued until first event) so consumers
    can rely on key presence without defensive checks.
    """
    return {
        "cache_hit": _live_search["cache_hit"],
        "cache_miss": _live_search["cache_miss"],
        "cache_stale": _live_search["cache_stale"],
        "enrich_dispatched": _live_search["enrich_dispatched"],
        "enrich_success": _live_search["enrich_success"],
        "enrich_failure": _live_search["enrich_failure"],
        "enrich_write_failure": _live_search["enrich_write_failure"],
        "osm_confirmed": _live_search["osm_confirmed"],
        "osm_nearby": _live_search["osm_nearby"],
        "tomtom_only": _live_search["tomtom_only"],
    }
