from sqlalchemy import text
from api.deps import get_db
from api.settings import settings
from src.gymdb.db.errors import DatabaseUnavailable, QueryFailed

def check_database(db):
    try:
        result = db.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception:
        return False

def check_postgis(db):
    try:
        result = db.execute(text("SELECT PostGIS_Version()"))
        return result.scalar() is not None
    except Exception:
        return False

def check_schema(db):
    try:
        result = db.execute(
            text("SELECT COUNT(*) FROM gyms")
        )
        return result.scalar() is not None
    except Exception:
        return False
