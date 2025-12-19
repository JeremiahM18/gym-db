from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class GymNearby(BaseModel):
    """
    Read-only projection for nearby gym queries.
    Represents a computed view, not a persisted entity.
    """

    model_config = ConfigDict(
        frozen=True,            # immutable
        extra="ignore",         # DB can add columns without breaking
    )

    gym_id: str = Field(..., description="Stable gym identifier")
    name: str = Field(..., description="Gym display name")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Inference confidence score"
    )
    distance_m: float = Field(..., ge=0.0, description="Distance in meters")