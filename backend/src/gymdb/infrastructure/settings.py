from pydantic_settings import BaseSettings

class GymDBSettings(BaseSettings):
    """
    Domain / infrastructure configuration.

    This module must remain HTTP-agnostic.
    """

    postgres_dsn: str

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }    

settings = GymDBSettings()
    


