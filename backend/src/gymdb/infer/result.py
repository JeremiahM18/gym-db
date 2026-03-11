from typing import Literal

from pydantic import BaseModel

InferenceValue = bool | int | str


class InferenceResult(BaseModel):
    value: InferenceValue
    reasons: list[str]
    confidence: float | None = None
    source: Literal["rule"] = "rule"
