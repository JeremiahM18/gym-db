from __future__ import annotations

from pathlib import Path
import os

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.registry import DatasetRegistry
from api.store import GymStore
from src.gymdb.db.errors import DatabaseUnavailable, QueryFailed

# -- Registy / Store ---

REGISTRY_PATH = Path(os.getenv("GYMDB_REGISTRY", "data/registry.json"))

def get_registry() -> DatasetRegistry:
    """
    Load and return the dataset registry.
    Isolated for testability ad future hot-reload support.
    """
    return DatasetRegistry(REGISTRY_PATH).load()


def get_store(
        registry: DatasetRegistry = Depends(get_registry),
) -> GymStore:
    """
    Provide a GymStore bound to the active registry.
    """
    return GymStore(registry)

# --- Error Translation ---

def db_error_to_http(e: Exception) -> HTTPException:
    """
    Translate domain DB errors into HTTP responses.
    DB layer must never raise HTTP exceptions dierctly.
    """
    if isinstance(e, DatabaseUnavailable):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Database unavailable"
        )
    
    if isinstance(e, QueryFailed):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database query failed"
        )
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
        detail="Internal server error"
    )

def get_db(
        store: GymStore = Depends(get_store),
) -> Session:
    """
    Provide a raw database session for low-level/internal routes.

    This is intentionally separated from GymStore to:
    - preserve store encapsulation
    - support internal diagnostics
    - keep public routes store-driven
    """
    return store.db