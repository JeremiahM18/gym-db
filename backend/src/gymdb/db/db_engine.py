from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from src.gymdb.settings import settings
from src.gymdb.db.errors import DatabaseUnavailable

_engine: Engine | None = None

def get_engine() -> Engine:
    """
    Process-wide singleton SQLAlchemy engine.


    - Uses connection pooling 
    - Detects stale connections
    - Fails fast if DB is unavailable
    """
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(
                settings.postgres_dsn,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,    # auto-detect dead connections
                echo=False,
                future=True,
            )
        except SQLAlchemyError as exc:
            raise DatabaseUnavailable("Failed to create database engine") from exc
    return _engine

def reset_engine() -> None:
    """
    Reset the process-wide engine.
    Intended for tests environment only.
    """
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None