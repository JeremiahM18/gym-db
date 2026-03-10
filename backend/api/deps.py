from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.engine import Connection

from api.resources import create_store
from api.settings import APISettings, get_settings
from gymdb.db.db_engine import get_connection
from gymdb.db.errors import DatabaseUnavailable, QueryFailed
from gymdb.gyms.store_dataset import DatasetGymStore


# Core application dependencies

def get_db() -> Generator[Connection, None, None]:
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
