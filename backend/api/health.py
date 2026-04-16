from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection

from api.deps import get_db
from api.readiness import check_database, check_postgis, check_schema
from gymdb.domain.inference import RULESET_VERSION

router = APIRouter()
logger = logging.getLogger("gymdb")


@router.get("/healthz", tags=["health"])
def healthz():
    """
    Liveness probe.

    Confirms the service process is running.
    Does NOT check external dependencies.
    """
    return {
        "status": "ok",
        "api_version": "v2",
    }


@router.get("/readyz", tags=["health"])
def readyz(db: Connection = Depends(get_db)):
    """
    Readiness probe.

    Confirms external dependencies (DB + extension + schema) are available.

    Returns 503 when NOT ready.

    503 responses are returned using the global error envelope:

    {
        "error": {
            "code": 503,
            "message": {
                "ready": false,
                "checks": {...}
            }
        }
    }
    """
    try:
        checks = {
            "database": check_database(db),
            "postgis": check_postgis(db),
            "schema": check_schema(db),
        }
    except Exception as exc:
        logger.exception("Readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "checks": {"database": False}},
        ) from exc

    ready = all(checks.values())

    payload = {
        "ready": ready,
        "checks": checks,
        "inference": {
            "engine": "rule_based",
            "version": RULESET_VERSION,
        },
    }

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=payload,
        )

    return payload
