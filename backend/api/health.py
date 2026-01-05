from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.gymdb.db.db_engine import get_connection

from api.readiness import (
    check_database,
    check_postgis,
    check_schema,
)

router = APIRouter()

@router.get("/healthz", tags=["health"])
def healthz():
    """
    Liveness probe.
    Confirms the service process is running.
    """
    return {
        "status": "ok",
        "api_version": "v2",
    }

@router.get("/readyz", tags=["health"])
def readyz():
    """
    Readiness probe.
    Confirms external dependencies (DB) are available.
    Returns 503 when NOT ready.
    """
    try:
        with get_connection() as db:
            checks = {
                "database": check_database(db),
                "postgis": check_postgis(db),
                "schema": check_schema(db),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "checks": {"database": False}},
        )

    ready = all(checks.values())

    payload = {
        "ready": ready,
        "checks": checks,
        "inference": {
            "engine": "rule_based",
            "version": "1.0.0",
        },
    }

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=payload,
        )

    return payload