import requests
import time
from functools import lru_cache
from jose import jwt
from jose.exceptions import JWTError

from api.settings import settings

JWKS_URL = f"{settings.cognito_issuer}/.well-known/jwks.json"

@lru_cache()
def get_jwks():
    resp = requests.get(JWKS_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()["keys"]

def verify_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header["kid"]

        key = next(k for k in get_jwks() if k["kid"] == kid)

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=settings.cognito_issuer,
        )

        if claims["exp"] < time.time():
            raise JWTError("Token expired")

        return claims

    except Exception as e:
        raise ValueError("Invalid JWT") from e

