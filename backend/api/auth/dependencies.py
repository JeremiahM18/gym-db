import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth.cognito import verify_jwt
from api.settings import APISettings, get_settings

security = HTTPBearer(auto_error=False)
audit_logger = logging.getLogger("gymdb.audit")


def require_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    settings: APISettings = Depends(get_settings),
) -> dict:
    """
    Require a valid authenticated user.

    Contract:
    - Missing Authorization header -> 401 (unless bypass)
    - Invalid/ expired token -> 401
    - Returns JWT claims dict on success
    """
    if not creds:
        if settings.enable_dev_auth_bypass:
            return {
                "sub": "dev-user",
                "email": "dev@gymdb.local",
                "cognito:groups": [],
                "dev": True,
            }

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    try:
        return verify_jwt(creds.credentials, settings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def require_admin(
    request: Request,
    claims: dict = Depends(require_user),
) -> dict:
    """
    Require an authenticated user with admin group membership.
    """
    groups = claims.get("cognito:groups", [])
    if "admin" not in groups:
        _log_admin_event("admin_route_denied", claims, request, level="warning")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    _log_admin_event("admin_route_access", claims, request, level="info")
    return claims


def _log_admin_event(
    event: str,
    claims: dict,
    request: Request | None,
    *,
    level: str,
) -> None:
    if request is None:
        return

    payload = {
        "request_id": getattr(request.state, "request_id", None),
        "sub": claims.get("sub"),
        "groups": list(claims.get("cognito:groups", [])),
        "method": request.method,
        "path": request.url.path,
        "query": str(request.url.query),
    }
    log = audit_logger.info if level == "info" else audit_logger.warning
    log(event, extra=payload)
