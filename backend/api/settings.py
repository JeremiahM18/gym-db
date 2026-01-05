
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

class APISettings(BaseSettings):
    """
    API-specific configuration.

    Owns: 
    - database connectivity
    - auth configuration
    - operational feature flags
    """

    registry_path: Path = Path("data/registry.json")

    # Auth
    aws_region: str
    cognito_user_pool_id: str
    cognito_app_client_id: str
    cognito_issuer: str

    # Ops
    enable_internal: bool = False

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

@lru_cache()
def get_settings() -> APISettings:
    """
    Cached API settings dependency.
    """
    return APISettings()


