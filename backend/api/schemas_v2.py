from pydantic import BaseModel, Field
from typing import Any, Literal

from gymdb.infer.result import InferenceResult
from gymdb.infer.meta import InferenceMeta


# Embedding Schemas (v2)
class InferenceEmbeddingV2(BaseModel):
    key: str
    value: str
    confidence: float
    source: str

class GymEmbeddingV2(BaseModel):
    """
    Embedding-ready representation of a gym.
    Safe for vector databases and LLM pipelines.
    """

    id: str
    name: str
    region: str

    # Primary text input for embedding
    embedding_text: str = Field(
        ...,
        description="Determininstic text used for vector embeddings"
    )

    # Structured inference preserved
    inference: list[InferenceEmbeddingV2]

    # Metadata (filterable, not embedded)
    confidence_score: float | None = None
    lat: float | None = None
    lon: float | None = None

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

    inference: dict[str, InferenceResult]
    inference_meta: InferenceMeta
    inference_summary: dict[str, str] | None = None


class GymNearbyOutV2(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    distance_m: float


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

class GymsNearbyResponseV2(BaseModel):
    api_version: str = Field(default="v2")
    count: int
    results: list[GymNearbyOutV2]

