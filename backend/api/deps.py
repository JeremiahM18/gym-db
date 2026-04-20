from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.engine import Connection

from api.resources import create_store
from api.settings import APISettings, get_settings
from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infrastructure.db.db_engine import get_connection
from gymdb.infrastructure.db.errors import DatabaseUnavailable, QueryFailed
from gymdb.infrastructure.tomtom_client import TomTomClient

# Core application dependencies

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


