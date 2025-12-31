from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Dict, Any


@dataclass
class JobReceipt:
    job_id: str
    region: str
    mode: str

    started_at: datetime
    finished_at: datetime | None

    status: str # queued, running, completed, failed

    stats: Dict[str, int]

    deterministic_hash: str

    # helpers

    @staticmethod
    def compute_hash(payload: Dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    @classmethod
    def build(
        cls,
        *,
        job_id: str,
        region: str,
        mode: str,
        started_at: datetime,
        finished_at: datetime,
        status: str,
        stats: Dict[str, int],
    ) -> "JobReceipt":
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "region": self.region,
            "mode": self.mode,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "status": self.status,
            "stats": self.stats,
            "deterministic_hash": self.deterministic_hash,
        }