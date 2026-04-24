from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import TYPE_CHECKING, Any

import requests
from jose import jwt
from jose.exceptions import JWTError

if TYPE_CHECKING:
    from api.settings import APISettings


@dataclass(frozen=True)
class _JWKSCacheEntry:
    keys: tuple[dict[str, Any], ...]
    fetched_at_epoch_s: float


_jwks_cache: dict[str, _JWKSCacheEntry] = {}
_jwks_lock = Lock()


def clear_jwks_cache() -> None:
    with _jwks_lock:
        _jwks_cache.clear()


def _fetch_jwks(jwks_url: str) -> list[dict[str, Any]]:
    resp = requests.get(jwks_url, timeout=5)
    resp.raise_for_status()
    payload = resp.json()
    keys = payload.get("keys")
    if not isinstance(keys, list):
        raise ValueError("JWKS response did not contain a valid keys list")
    return keys


def get_jwks(
    jwks_url: str,
    *,
    ttl_seconds: int,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """Fetch and cache JWKS keys with TTL and optional forced refresh."""
    now_epoch_s = time.time()

    with _jwks_lock:
        cached = _jwks_cache.get(jwks_url)
        if (
            not force_refresh
            and cached is not None
            and now_epoch_s - cached.fetched_at_epoch_s < ttl_seconds
        ):
            return [dict(key) for key in cached.keys]

    keys = _fetch_jwks(jwks_url)

    with _jwks_lock:
        _jwks_cache[jwks_url] = _JWKSCacheEntry(
            keys=tuple(dict(key) for key in keys),
            fetched_at_epoch_s=now_epoch_s,
        )

    return keys


def _find_jwk(keys: list[dict[str, Any]], kid: str) -> dict[str, Any] | None:
    return next((key for key in keys if key.get("kid") == kid), None)


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
        kid = str(header["kid"])

        keys = get_jwks(
            jwks_url,
            ttl_seconds=settings.cognito_jwks_cache_ttl_seconds,
        )
        key = _find_jwk(keys, kid)
        if key is None:
            keys = get_jwks(
                jwks_url,
                ttl_seconds=settings.cognito_jwks_cache_ttl_seconds,
                force_refresh=True,
            )
            key = _find_jwk(keys, kid)
        if key is None:
            raise ValueError("Unknown signing key")

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

    except (
        JWTError,
        KeyError,
        TypeError,
        ValueError,
        requests.RequestException,
    ) as exc:
        raise ValueError("Invalid JWT") from exc
