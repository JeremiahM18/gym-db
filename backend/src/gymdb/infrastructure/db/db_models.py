from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class GymNearby(BaseModel):
    """
    One row returned from a nearby geospatial query.
    Contains only physical facts and computer geometry.
    """

    model_config = ConfigDict(
        frozen=True,            # immutable
        extra="ignore",         # DB can add columns without breaking
    )

    id: str = Field(..., description="Stable gym identifier")
    name: str = Field(..., description="Gym display name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    distance_m: float = Field(..., ge=0.0, description="Distance in meters")
