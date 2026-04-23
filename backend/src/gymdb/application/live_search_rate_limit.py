from __future__ import annotations

import logging
import sqlite3
from collections import deque
from math import ceil
from threading import Lock
from time import monotonic

from gymdb.infrastructure.ops_state_store import OpsStateStore
from gymdb.infrastructure.settings import settings

logger = logging.getLogger(__name__)

_rate_limit_lock = Lock()
_fallback_buckets: dict[tuple[str, str], deque[float]] = {}
_logged_store_failure = False


def _ops_store() -> OpsStateStore:
    return OpsStateStore(settings.ops_state_path)


def reset_live_search_rate_limiter() -> None:
    global _logged_store_failure
    with _rate_limit_lock:
        _fallback_buckets.clear()
        _logged_store_failure = False

    try:
        _ops_store().reset_rate_limit_events()
    except (OSError, sqlite3.Error):
        _log_fallback_once()


def _consume_fallback_token(
    *,
    scope: str,
    bucket_key: str,
    limit: int,
    window_seconds: int,
) -> int | None:
    now = monotonic()
    window_start = now - window_seconds
    key = (scope, bucket_key)

    with _rate_limit_lock:
        bucket = _fallback_buckets.setdefault(key, deque())
        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= limit:
            return max(1, ceil(window_seconds - (now - bucket[0])))

        bucket.append(now)
        return None


def consume_live_search_rate_limit_token(
    *,
    scope: str,
    bucket_key: str,
    limit: int,
    window_seconds: int,
) -> int | None:
    try:
        allowed, retry_after = _ops_store().consume_rate_limit_token(
            scope=scope,
            bucket_key=bucket_key,
            limit=limit,
            window_seconds=window_seconds,
        )
    except (OSError, sqlite3.Error):
        _log_fallback_once()
        return _consume_fallback_token(
            scope=scope,
            bucket_key=bucket_key,
            limit=limit,
            window_seconds=window_seconds,
        )

    if allowed:
        return None
    return retry_after


def _log_fallback_once() -> None:
    global _logged_store_failure
    if _logged_store_failure:
        return
    _logged_store_failure = True
    logger.exception("Falling back to in-memory live-search rate limiting")
