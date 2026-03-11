from functools import lru_cache

from pydantic_settings import BaseSettings


class GymDBSettings(BaseSettings):
    """
    Domain / infrastructure configuration.

    This module must remain HTTP-agnostic.
    """

    postgres_dsn: str = "postgresql+psycopg://gymdb:gymdb@localhost:5432/gymdb"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> GymDBSettings:
    return GymDBSettings()


settings = get_settings()
