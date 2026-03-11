from __future__ import annotations

from pathlib import Path


DATA_ROOT = Path("data")
ARTIFACTS_ROOT = DATA_ROOT / "artifacts"
JOBS_ROOT = ARTIFACTS_ROOT / "jobs"
RECEIPTS_ROOT = ARTIFACTS_ROOT / "receipts"


def ensure_storage_tree() -> None:
    for path in (DATA_ROOT, ARTIFACTS_ROOT, JOBS_ROOT, RECEIPTS_ROOT):
        path.mkdir(parents=True, exist_ok=True)


