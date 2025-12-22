from pydantic import BaseModel
from typing import Optional, Union, Literal

InferenceValue = Union[bool, int, str]

class InferenceResult(BaseModel):
    value: InferenceValue
    reasons: list[str]
    confidence: Optional[float] = None
    source: Literal["rule"] = "rule"