from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator

from gymdb.settings import GymDBSettings

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class APISettings(GymDBSettings):
    """API settings."""

    # Filesystem / registry
    registry_path: Path = BACKEND_ROOT / "data/registry.json"
    dataset_root: Path = BACKEND_ROOT / "data"

    # Auth (Cognito)
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = "dev"
    cognito_app_client_id: str = "dev"
    cognito_issuer: str = "https://example.com"

    # Ops flags
    enable_internal: bool = False
    enable_dev_auth_bypass: bool = False
    live_search_rate_limit: int = Field(default=8, ge=0)
    live_search_window_seconds: int = Field(default=60, ge=1)
    live_search_upstream_timeout_seconds: int = Field(default=20, ge=1)
    live_search_cache_root: Path = BACKEND_ROOT / "data/live_search_cache"
    live_search_cache_ttl_seconds: int = Field(default=86_400, ge=1)
    live_search_session_root: Path = BACKEND_ROOT / "data/live_search_sessions"
    live_search_session_ttl_seconds: int = Field(default=900, ge=1)
    live_search_poll_after_ms: int = Field(default=2_000, ge=250, le=60_000)
    live_search_overpass_timeout_seconds: int = Field(default=25, ge=1)
    live_search_overpass_max_attempts: int = Field(default=2, ge=1)

    # Browser clients
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @model_validator(mode="after")
    def validate_api_runtime_settings(self) -> APISettings:
        if not self.cors_allowed_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must not be empty.")
        if (
            self.live_search_session_ttl_seconds * 1000
            <= self.live_search_poll_after_ms
        ):
            raise ValueError(
                "LIVE_SEARCH_SESSION_TTL_SECONDS must exceed LIVE_SEARCH_POLL_AFTER_MS."
            )
        if self.is_production_like:
            if self.enable_dev_auth_bypass:
                raise ValueError(
                    "ENABLE_DEV_AUTH_BYPASS cannot be enabled in staging or production."
                )
            if (
                self.cognito_user_pool_id == "dev"
                or self.cognito_app_client_id == "dev"
                or self.cognito_issuer == "https://example.com"
            ):
                raise ValueError(
                    "Cognito settings must be configured in staging and production."
                )
            if any(
                "localhost" in origin or "127.0.0.1" in origin
                for origin in self.cors_allowed_origins
            ):
                raise ValueError(
                    "Localhost CORS origins are not allowed in staging or production."
                )
        return self


@lru_cache
def get_settings() -> APISettings:
    """Return cached API settings."""
    return APISettings()
