import os

from fastapi import HTTPException, status


def require_internal_enabled():
    enabled = os.getenv("ENABLE_INTERNAL", "false").lower() == "true"
    if not enabled:
        # 404 on purpose: endpoint should appear nonexistent
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )

