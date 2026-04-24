from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class GymDBSettings(BaseSettings):
    """
    Shared env-backed configuration for GymDB.

    This base stays framework-agnostic so domain, infrastructure, and API
    modules can agree on common settings without duplicating them.
    """

    app_env: Literal["development", "test", "staging", "production"] = "development"
    postgres_dsn: str = (
        "postgresql+psycopg://gymdb_app:gymdb_app_password@localhost:5432/gymdb"
    )
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    overpass_fallback_url: str | None = None
    overpass_timeout_seconds: int = Field(default=60, ge=1)
    overpass_max_attempts: int = Field(default=3, ge=1)
    overpass_backoff_seconds: float = Field(default=2.0, ge=0)
    ops_state_path: Path = BACKEND_ROOT / "data/ops_state.sqlite3"
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

    @property
    def is_production_like(self) -> bool:
        return self.app_env in {"staging", "production"}

    @model_validator(mode="after")
    def validate_shared_runtime_settings(self) -> GymDBSettings:
        if self.is_production_like and not self.tomtom_base_url.startswith(
            "https://"
        ):
            raise ValueError(
                "TOMTOM_BASE_URL must use HTTPS in staging and production."
            )
        return self
