from fastapi import Depends, HTTPException, status

from api.settings import APISettings, get_settings


def require_internal_enabled(
    settings: APISettings = Depends(get_settings),
) -> None:
    if not settings.enable_internal:
        # 404 on purpose: endpoint should appear nonexistent
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )
