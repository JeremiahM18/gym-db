from datetime import datetime
from pydantic import BaseModel
from typing import Literal

class InferenceMeta(BaseModel):
    engine: Literal["rule_based"]
    version: str
    generated_at: datetime
    deterministic_hash: str