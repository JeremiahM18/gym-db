from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class GymDBSettings(BaseSettings):
    """
    Shared env-backed configuration for GymDB.

    This base stays framework-agnostic so domain, infrastructure, and API
    modules can agree on common settings without duplicating them.
    """

    postgres_dsn: str = (
        "postgresql+psycopg://gymdb_app:gymdb_app_password@localhost:5432/gymdb"
    )
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    overpass_fallback_url: str | None = None
    overpass_timeout_seconds: int = 60
    overpass_max_attempts: int = 3
    overpass_backoff_seconds: float = 2.0
    tomtom_api_key: str | None = None
    tomtom_base_url: str = "https://api.tomtom.com"
    require_tomtom_publish_validation: bool = True

    model_config = {
        "env_file": (
            str(BACKEND_ROOT / ".env"),
            str(BACKEND_ROOT / ".env.local"),
        ),
        "extra": "ignore",
    }
