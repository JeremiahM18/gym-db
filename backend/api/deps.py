from __future__ import annotations

from pathlib import Path
from fastapi import HTTPException, status, Depends

from typing import Generator
from sqlalchemy.engine import Connection

from src.gymdb.db.db_engine import get_connection
from src.gymdb.db.errors import DatabaseUnavailable, QueryFailed

from src.gymdb.datasets.registry import DatasetRegistry
#from src.gymdb.gyms.store_dataset import DatasetGymStore
from src.gymdb.gyms.store_postgres import PostgresGymStore


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
        conn: Connection = Depends(get_db),
) -> PostgresGymStore:
    """
    Application-level dependency for gym data access.

    This is the ONLY place where:
    - DatasetRegistry is constructed
    - Filesystem paths are referenced
    """
    return PostgresGymStore(conn)
    # registry = DatasetRegistry(
    #     Path("data/registry.json")
    # ).load()
    # return GymStore(registry)

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
    elif isinstance(exc, QueryFailed):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

