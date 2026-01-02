import os
import json
from pathlib import Path
from src.gymdb.jobs.receipt import JobReceipt

def maybe_write_fs_receipt(receipt: JobReceipt) -> None:
    """
    Optionally write a filesystem receipt artifact.
    This is NOT a source of truth. DB is authoritative.
    """
    if not os.getenv("WRITE_FS_RECEIPTS"):
        return
    
    root = Path("data/receipts")
    root.mkdir(parents=True, exist_ok=True)

    path = root / f"{receipt.job_id}.json"
    path.write_text(
        json.dumps(receipt.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )