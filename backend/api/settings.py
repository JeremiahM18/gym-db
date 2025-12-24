from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    aws_region: str
    cognito_user_pool_id: str
    cognito_app_client_id: str
    cognito_issuer: str
    enable_internal: bool = False

settings = Settings()

