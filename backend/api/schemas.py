from pydantic import BaseModel, Field
from typing import Any

InferenceValue = bool | int | str


class InferenceResultOut(BaseModel):
    value: InferenceValue
    reasons: list[str] | None = None


class GymOutV1(BaseModel):
    id: str
    name: str
    norm_name: str
    lat: float
    lon: float
    osm_refs: list[dict[str, Any]]
    tags: dict[str, Any]
    confidence_score: float | None = None

    # API-facing inference
    inference: dict[str, InferenceResultOut] = Field(default_factory=dict)

    # Optional, only when requested
    inference_summary: dict[str, str] | None = None
    inference_meta: dict[str, Any] | None = None


class RegionsResponseV1(BaseModel):
    default: str
    regions: list[str]


class GymsListResponseV1(BaseModel):
    api_version: str
    region: str
    count: int
    results: list[GymOutV1]
