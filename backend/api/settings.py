from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """
    API-specific configuration.

    Owns:
    - database connectivity
    - auth configuration
    - operational feature flags
    """

    # Filesystem / registry
    registry_path: Path = Path("data/registry.json")
    dataset_root: Path = Path("data")

    # Database
    postgres_dsn: str = "postgresql+psycopg://gymdb:gymdb_password@localhost:5432/gymdb"

    # Auth (Cognito)
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = "dev"
    cognito_app_client_id: str = "dev"
    cognito_issuer: str = "https://example.com"

    # Ops flags
    enable_internal: bool = False
    enable_dev_auth_bypass: bool = False

    # Browser clients
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> APISettings:
    """
    Cached API settings dependency.

    NOTE:
    In tests, override this dependency avoid leaking env state:
        app.dependency_overrides[get_settings] = lambda: APISettings(...)
    """
    return APISettings()
