from __future__ import annotations

from collections import deque
from collections.abc import Generator
from math import ceil
from threading import Lock
from time import monotonic

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.engine import Connection

from api.resources import create_store
from api.settings import APISettings, get_settings
from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infrastructure.db.db_engine import get_connection
from gymdb.infrastructure.db.errors import DatabaseUnavailable, QueryFailed
from gymdb.infrastructure.tomtom_client import TomTomClient

# Core application dependencies

_rate_limit_lock = Lock()
_live_search_buckets: dict[tuple[str, str], deque[float]] = {}


def reset_rate_limiter() -> None:
    with _rate_limit_lock:
        _live_search_buckets.clear()

def get_db() -> Generator[Connection]:
    """
    FastAPI dependency providing a DB connection.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_gym_store(
    settings: APISettings = Depends(get_settings),
) -> DatasetGymStore:
    """
    Application-level dependency for published gym dataset access.

    This is the ONLY place where:
    - DatasetRegistry is constructed
    - Filesystem paths are referenced
    """
    return create_store(settings)


def get_tomtom_client(
    settings: APISettings = Depends(get_settings),
) -> TomTomClient | None:
    """
    Application-level dependency for TomTom API access.
    """
    if not settings.tomtom_api_key:
        return None
    return TomTomClient(
        api_key=settings.tomtom_api_key,
        base_url=settings.tomtom_base_url,
    )


def enforce_live_search_rate_limit(
    request: Request,
    settings: APISettings = Depends(get_settings),
) -> None:
    if (
        settings.live_search_rate_limit <= 0
        or settings.live_search_window_seconds <= 0
    ):
        return

    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_host = (
        forwarded_for.split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    bucket_key = ("live-search", client_host)
    now = monotonic()
    window_start = now - settings.live_search_window_seconds

    with _rate_limit_lock:
        bucket = _live_search_buckets.setdefault(bucket_key, deque())
        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= settings.live_search_rate_limit:
            retry_after = max(
                1,
                ceil(settings.live_search_window_seconds - (now - bucket[0])),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Live search is temporarily rate limited. Please wait a moment "
                    "and try again."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)


# Error translation (DB -> HTTP)

def db_error_to_http(exc: Exception) -> HTTPException:
    """
    Translate DB errors into HTTP responses.
    """
    if isinstance(exc, DatabaseUnavailable):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )
    if isinstance(exc, QueryFailed):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database query failed",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


