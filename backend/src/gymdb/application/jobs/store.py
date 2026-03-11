from __future__ import annotations

import json
from pathlib import Path

from gymdb.application.jobs.models import IngestJob
from gymdb.infrastructure.storage import ensure_storage_tree


class JobStore:
    def __init__(self, root: Path):
        ensure_storage_tree()
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.root / f"{job_id}.json"

    def save(self, job: IngestJob) -> None:
        path = self._path(job.job_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(job.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def load(self, job_id: str) -> dict:
        path = self._path(job_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def list_recent(self, limit: int = 25) -> list[dict]:
        files = sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        out: list[dict] = []
        for p in files[:limit]:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        return out


