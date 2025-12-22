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

    inference: dict[str, InferenceResultV2]

    inference_summary: dict[str, str] | None = None
    inference_meta: InferenceMetaV2


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