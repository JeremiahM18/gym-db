from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gymdb.application.jobs.status import ALLOWED_TRANSITIONS


@dataclass
class JobReceipt:
    job_id: str
    region: str
    mode: str

    started_at: datetime
    finished_at: datetime | None

    status: str  # queued, running, succeeded, failed
    stats: dict[str, int]

    deterministic_hash: str

    @staticmethod
    def compute_hash(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_transition(prev: str | None, new: str) -> None:
        """
        Validate a job status transition.

        prev=None indicates initial state.
        """
        if prev is None:
            return

        allowed = ALLOWED_TRANSITIONS.get(prev)
        if allowed is None:
            raise ValueError(f"Unknown previous status: {prev}")

        if new not in allowed:
            raise ValueError(f"Invalid status transition from {prev} to {new}")

    @classmethod
    def build(
        cls,
        *,
        job_id: str,
        region: str,
        mode: str,
        started_at: datetime,
        finished_at: datetime | None,
        status: str,
        stats: dict[str, int],
        previous_status: str | None = None,
    ) -> JobReceipt:
        cls.validate_transition(previous_status, status)

        payload = {
            "job_id": job_id,
            "region": region,
            "mode": mode,
            "status": status,
            "stats": stats,
        }

        return cls(
            job_id=job_id,
            region=region,
            mode=mode,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            stats=stats,
            deterministic_hash=cls.compute_hash(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "region": self.region,
            "mode": self.mode,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
            "stats": self.stats,
            "deterministic_hash": self.deterministic_hash,
        }
