from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


@dataclass(frozen=True)
class IngestJob:
    job_id: str
    kind: str               # "ingest"
    mode: str               # "manual" | "scheduled"
    region: str
    status: JobStatus
    created_at: str
    started_at: str | None
    finished_at: str | None
    metrics: dict[str, Any]
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
    
def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()

