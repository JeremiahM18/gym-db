from __future__ import annotations

import logging
import sqlite3
from collections import Counter
from collections.abc import Mapping
from threading import Lock

from gymdb.domain.constants import InferenceResultData
from gymdb.infer.result import InferenceResult
from gymdb.infrastructure.ops_state_store import OpsStateStore
from gymdb.infrastructure.settings import settings

logger = logging.getLogger(__name__)

_inference_hits_fallback: Counter[str] = Counter()
_live_search_fallback: Counter[str] = Counter()
_http_fallback: Counter[str] = Counter()
_fallback_lock = Lock()
_logged_fallback_contexts: set[str] = set()

_LIVE_SEARCH_KEYS = (
    "cache_hit",
    "cache_miss",
    "cache_stale",
    "enrich_dispatched",
    "enrich_success",
    "enrich_failure",
    "enrich_write_failure",
    "osm_confirmed",
    "osm_nearby",
    "tomtom_only",
)

_HTTP_KEYS = (
    "requests_total",
    "requests_2xx",
    "requests_4xx",
    "requests_5xx",
    "request_exceptions",
    "latency_le_100ms",
    "latency_le_300ms",
    "latency_le_1000ms",
    "latency_gt_1000ms",
)


def _ops_store() -> OpsStateStore:
    return OpsStateStore(settings.ops_state_path)


def _merge_counter_snapshot(
    persisted: dict[str, int],
    fallback: Counter[str],
) -> dict[str, int]:
    merged = dict(persisted)
    for key, value in fallback.items():
        merged[key] = merged.get(key, 0) + value
    return merged


def _record(namespace: str, deltas: dict[str, int], fallback: Counter[str]) -> None:
    if not deltas:
        return

    try:
        _ops_store().increment_counters(namespace=namespace, deltas=deltas)
    except (OSError, sqlite3.Error):
        _log_fallback_once(f"record:{namespace}")
        with _fallback_lock:
            fallback.update(deltas)


def _log_fallback_once(context: str) -> None:
    if context in _logged_fallback_contexts:
        return
    _logged_fallback_contexts.add(context)
    logger.exception("Using in-memory metrics fallback for %s", context)


def _inference_value(result: InferenceResult | InferenceResultData) -> object | None:
    if isinstance(result, InferenceResult):
        return result.value
    return result.get("value")


def record_inference_hits(
    inferred: Mapping[str, InferenceResult | InferenceResultData],
) -> None:
    """
    Count which inference keys are produced.
    Accepts normalized inference dicts or InferenceResult-like objects.
    """
    deltas: dict[str, int] = {}
    for key, result in inferred.items():
        value = _inference_value(result)
        if value is not None:
            deltas[key] = deltas.get(key, 0) + 1

    _record("inference_hits", deltas, _inference_hits_fallback)


def snapshot_metrics() -> dict[str, int]:
    """Snapshot current inference hit counts."""
    try:
        persisted = _ops_store().snapshot_counters(namespace="inference_hits")
    except (OSError, sqlite3.Error):
        _log_fallback_once("snapshot:inference_hits")
        persisted = {}

    with _fallback_lock:
        return _merge_counter_snapshot(persisted, _inference_hits_fallback)


def record_cache_probe(*, cache_exists: bool, is_fresh: bool) -> None:
    """Record the result of a live-search OSM cache probe."""
    if not cache_exists:
        _record("live_search", {"cache_miss": 1}, _live_search_fallback)
    elif is_fresh:
        _record("live_search", {"cache_hit": 1}, _live_search_fallback)
    else:
        _record("live_search", {"cache_stale": 1}, _live_search_fallback)


def record_enrich_dispatched() -> None:
    """Record that a background Overpass enrichment task was scheduled."""
    _record("live_search", {"enrich_dispatched": 1}, _live_search_fallback)


def record_enrich_outcome(*, success: bool, write_failed: bool = False) -> None:
    """
    Record the outcome of a background Overpass enrichment task.

    success=True  → Overpass fetch and cache write both succeeded.
    success=False, write_failed=True  → fetch succeeded but cache write failed.
    success=False, write_failed=False → Overpass fetch failed (unavailable or error).
    """
    if success:
        _record("live_search", {"enrich_success": 1}, _live_search_fallback)
    elif write_failed:
        _record("live_search", {"enrich_write_failure": 1}, _live_search_fallback)
    else:
        _record("live_search", {"enrich_failure": 1}, _live_search_fallback)


def record_osm_confirmation_outcomes(
    *, osm_confirmed: int, osm_nearby: int, tomtom_only: int
) -> None:
    """Record per-request gym-level OSM confirmation tier distribution."""
    _record(
        "live_search",
        {
            "osm_confirmed": osm_confirmed,
            "osm_nearby": osm_nearby,
            "tomtom_only": tomtom_only,
        },
        _live_search_fallback,
    )


def snapshot_live_search_metrics() -> dict[str, int]:
    """
    Snapshot current live-search event counts.

    Returns a fixed set of keys (zero-valued until first event) so consumers
    can rely on key presence without defensive checks.
    """
    try:
        persisted = _ops_store().snapshot_counters(
            namespace="live_search",
            expected_keys=_LIVE_SEARCH_KEYS,
        )
    except (OSError, sqlite3.Error):
        _log_fallback_once("snapshot:live_search")
        persisted = {key: 0 for key in _LIVE_SEARCH_KEYS}

    with _fallback_lock:
        return _merge_counter_snapshot(persisted, _live_search_fallback)


def record_http_request(*, status_code: int, elapsed_ms: float) -> None:
    """Record coarse HTTP volume, error, and latency buckets."""
    deltas = {"requests_total": 1}
    if 200 <= status_code < 300:
        deltas["requests_2xx"] = 1
    elif 400 <= status_code < 500:
        deltas["requests_4xx"] = 1
    elif status_code >= 500:
        deltas["requests_5xx"] = 1

    if elapsed_ms <= 100:
        deltas["latency_le_100ms"] = 1
    elif elapsed_ms <= 300:
        deltas["latency_le_300ms"] = 1
    elif elapsed_ms <= 1000:
        deltas["latency_le_1000ms"] = 1
    else:
        deltas["latency_gt_1000ms"] = 1

    _record("http", deltas, _http_fallback)


def record_http_exception() -> None:
    """Record an unhandled exception from the request pipeline."""
    _record("http", {"request_exceptions": 1}, _http_fallback)


def snapshot_http_metrics() -> dict[str, int]:
    """Snapshot current coarse HTTP service metrics."""
    try:
        persisted = _ops_store().snapshot_counters(
            namespace="http",
            expected_keys=_HTTP_KEYS,
        )
    except (OSError, sqlite3.Error):
        _log_fallback_once("snapshot:http")
        persisted = {key: 0 for key in _HTTP_KEYS}

    with _fallback_lock:
        return _merge_counter_snapshot(persisted, _http_fallback)


def reset_metrics() -> None:
    with _fallback_lock:
        _inference_hits_fallback.clear()
        _live_search_fallback.clear()
        _http_fallback.clear()
        _logged_fallback_contexts.clear()

    try:
        store = _ops_store()
        store.reset_counters(namespace="inference_hits")
        store.reset_counters(namespace="live_search")
        store.reset_counters(namespace="http")
    except (OSError, sqlite3.Error):
        _log_fallback_once("reset:metrics")
