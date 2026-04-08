from functools import lru_cache

from gymdb.settings import GymDBSettings


@lru_cache
def get_settings() -> GymDBSettings:
    """
    Cached infrastructure settings.

    Infrastructure code depends only on the shared, HTTP-agnostic base settings.
    """
    return GymDBSettings()


settings = get_settings()
