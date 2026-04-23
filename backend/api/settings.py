from __future__ import annotations

from functools import lru_cache
from pathlib import Path

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
    live_search_rate_limit: int = 8
    live_search_window_seconds: int = 60
    live_search_upstream_timeout_seconds: int = 20
    live_search_cache_root: Path = BACKEND_ROOT / "data/live_search_cache"
    live_search_cache_ttl_seconds: int = 86_400
    live_search_session_root: Path = BACKEND_ROOT / "data/live_search_sessions"
    live_search_session_ttl_seconds: int = 900
    live_search_poll_after_ms: int = 2_000
    live_search_overpass_timeout_seconds: int = 25
    live_search_overpass_max_attempts: int = 2

    # Browser clients
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> APISettings:
    """Return cached API settings."""
    return APISettings()
