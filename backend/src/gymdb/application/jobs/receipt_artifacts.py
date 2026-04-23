import json
import os

from gymdb.application.jobs.receipt import JobReceipt
from gymdb.infrastructure.storage import RECEIPTS_ROOT, ensure_storage_tree


def maybe_write_fs_receipt(receipt: JobReceipt) -> None:
    """Optionally write a filesystem copy of a receipt."""
    if not os.getenv("WRITE_FS_RECEIPTS"):
        return

    ensure_storage_tree()

    path = RECEIPTS_ROOT / f"{receipt.job_id}.json"
    path.write_text(
        json.dumps(receipt.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


