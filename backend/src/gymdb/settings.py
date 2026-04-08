from __future__ import annotations

from pydantic_settings import BaseSettings


class GymDBSettings(BaseSettings):
    """
    Shared env-backed configuration for GymDB.

    This base stays framework-agnostic so domain, infrastructure, and API
    modules can agree on common settings without duplicating them.
    """

    postgres_dsn: str = (
        "postgresql+psycopg://gymdb_app:gymdb_app_password@localhost:5432/gymdb"
    )
    tomtom_api_key: str | None = None
    tomtom_base_url: str = "https://api.tomtom.com"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }
