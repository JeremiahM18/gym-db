from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def check_database(db: Connection) -> bool:
    """
    Basic DB connectivity check.
    """
    try:
        result = db.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception:
        return False


def check_postgis(db: Connection) -> bool:
    """
    Verify PostGIS extension is available.
    """
    try:
        result = db.execute(text("SELECT PostGIS_Version()"))
        return result.scalar() is not None
    except Exception:
        return False


def check_schema(db: Connection) -> bool:
    """
    Verify required schema objects exist.
    """
    try:
        result = db.execute(text("SELECT COUNT(*) FROM gyms"))
        return result.scalar() is not None
    except Exception:
        return False

