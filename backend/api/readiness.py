from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlalchemy import text
from sqlalchemy.engine import Connection

from api.resources import create_registry
from api.settings import APISettings
from gymdb.infrastructure.ops_state_store import OpsStateStore


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


def check_registry(settings: APISettings) -> bool:
    """Verify the dataset registry loads and its default dataset exists."""
    try:
        registry = create_registry(settings)
        default_region = registry.default_region
        return registry.dataset_path(default_region).exists()
    except Exception:
        return False


def check_dataset_root(settings: APISettings) -> bool:
    """Verify the dataset root directory exists."""
    return settings.dataset_root.exists() and settings.dataset_root.is_dir()


def check_live_search_storage(settings: APISettings) -> bool:
    """Verify cache and session roots are writable."""
    try:
        _assert_directory_writable(settings.live_search_cache_root)
        _assert_directory_writable(settings.live_search_session_root)
    except OSError:
        return False
    return True


def check_ops_state_store(settings: APISettings) -> bool:
    """Verify the shared local ops-state store is writable."""
    try:
        _assert_directory_writable(settings.ops_state_path.parent)
        OpsStateStore(settings.ops_state_path).snapshot_counters(namespace="healthcheck")
    except (OSError, sqlite3.Error):
        return False
    return True


def assert_startup_preflight(settings: APISettings) -> dict[str, bool]:
    """Run non-database startup checks and raise if any required check fails."""
    checks = {
        "registry": check_registry(settings),
        "dataset_root": check_dataset_root(settings),
        "live_search_storage": check_live_search_storage(settings),
        "ops_state": check_ops_state_store(settings),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        joined = ", ".join(failed)
        raise RuntimeError(f"Startup preflight failed: {joined}")
    return checks


def _assert_directory_writable(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path, prefix=".healthcheck.", delete=False) as handle:
        temp_path = Path(handle.name)
    temp_path.unlink(missing_ok=True)


