from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from gymdb.settings import GymDBSettings

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class APISettings(GymDBSettings):
    """
    API-specific configuration.

    Owns:
    - auth configuration
    - operational feature flags
    - API-facing filesystem and browser configuration
    """

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

    # Browser clients
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

@lru_cache
def get_settings() -> APISettings:
    """
    Cached API settings dependency.

    NOTE:
    In tests, override this dependency avoid leaking env state:
        app.dependency_overrides[get_settings] = lambda: APISettings(...)
    """
    return APISettings()
