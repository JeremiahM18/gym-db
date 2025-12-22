from pydantic import BaseModel
from typing import Optional

class InferenceResult(BaseModel):
    value: bool | int | str
    reasons: list[str]
    confidence: float | None = None
    source: str = "rule"