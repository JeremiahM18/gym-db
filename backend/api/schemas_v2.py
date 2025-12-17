from pydantic import BaseModel, Field
from typing import Any, Literal

# Shared Primitives

class InferenceResultV2(BaseModel):
    """
    Structured inference result.

    value:
        The inferred value.

    confidence:
        Optional confidence (0.0-1.0) if available.
        Rule-based engines may omit this.

    reasons:
        Explanations for the inference.
    """

    value: bool | int | str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reasons: list[str]


class InferenceMetaV2(BaseModel):
    """
    Metadata describing how inference was produced.
    """
    engine: str
    version: str
    generated_at: str | None = None


# Gym Output (v2)

class GymOutV2(BaseModel):
    """
    v2 Gym representation.

    Changes from v1:
    - inference is fully structured
    - norm_name is optional (internal detail)
    - tags can be omitted by clients
    """

    id: str
    name: str
    norm_name: str

    lat: float
    lon: float

    confidence_score: float | None = None

    osm_refs: list[dict[str, Any]]

    tags: dict[str, Any] | None = None

    inference: dict[str, InferenceResultV2]

    inference_summary: dict[str, str] | None = None
    inference_meta: InferenceMetaV2


# Collection Responses

class GymsListResponseV2(BaseModel):
    api_version: str = Field(default="v2")
    region: str
    count: int
    results: list[GymOutV2]

class GymResponseV2(BaseModel):
    api_version: str = Field(default="v2")
    gym: GymOutV2

class RegionsResponseV2(BaseModel):
    api_version: str = Field(default="v2")
    default: str
    regions: list[str]



