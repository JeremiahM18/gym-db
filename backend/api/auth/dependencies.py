from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.auth.cognito import verify_jwt
from api.settings import  APISettings, get_settings

security = HTTPBearer(auto_error=False)

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
                "cognito:groups": ["admin"],
                "dev": True,
            }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    try:
        return verify_jwt(creds.credentials, settings)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

def require_admin(
    claims: dict = Depends(require_user),
) -> dict:
    """
    Require an authenticated user with admin group membership.
    """
    groups = claims.get("cognito:groups", [])
    if "admin" not in groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return claims

