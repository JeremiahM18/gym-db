from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InferenceMeta(BaseModel):
    engine: Literal["rule_based"]
    version: str
    generated_at: datetime
    deterministic_hash: str
    field_confidence: dict[str, float] = Field(default_factory=dict)
    contradictions: dict[str, list[str]] = Field(default_factory=dict)
