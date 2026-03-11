from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class InferenceMeta(BaseModel):
    engine: Literal["rule_based"]
    version: str
    generated_at: datetime
    deterministic_hash: str

