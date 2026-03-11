from __future__ import annotations

import time
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import requests
from jose import jwt
from jose.exceptions import JWTError

if TYPE_CHECKING:
    from api.settings import APISettings


@lru_cache(maxsize=8)
def get_jwks(jwks_url: str) -> list[dict[str, Any]]:
    """
    Fetch and cache JWKS keys.

    Cache is keyed by jwks_url so multiple environments remain isolated.
    """
    resp = requests.get(jwks_url, timeout=5)
    resp.raise_for_status()
    payload = resp.json()
    return payload["keys"]


def verify_jwt(token: str, settings: APISettings) -> dict[str, Any]:
    """
    Verify a JWT using Cognito configuration.

    This function is PURE:
    - no globals
    - no FastAPI imports
    - no env access
    """
    try:
        jwks_url = f"{settings.cognito_issuer}/.well-known/jwks.json"

        header = jwt.get_unverified_header(token)
        kid = header["kid"]

        key = next(k for k in get_jwks(jwks_url) if k["kid"] == kid)

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=settings.cognito_issuer,
        )

        if claims.get("exp", 0) < time.time():
            raise JWTError("Token expired")

        return claims

    except Exception as exc:
        raise ValueError("Invalid JWT") from exc
