from __future__ import annotations

from gymdb.jobs.receipt import JobReceipt
from gymdb.jobs.receipt_store import JobReceiptStoreDB


def get_job_receipt(job_id: str, *, store: JobReceiptStoreDB) -> JobReceipt:
    """
    Read model: fetch a single job receipt by ID.

    Raises:
      KeyError: if not found
    """
    return store.get(job_id)


def list_job_receipts(limit: int, *, store: JobReceiptStoreDB) -> list[JobReceipt]:
    """
    Read model: list recent job receipts in descending created_at order.
    """
    return store.list_receipts(limit=limit)
