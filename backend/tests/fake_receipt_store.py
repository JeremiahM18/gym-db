from __future__ import annotations

from gymdb.application.jobs.receipt import JobReceipt


class FakeReceiptStore:
    """
    In-memory fake store for JobReceipts for testing.
    """

    def __init__(self):
        self._receipts: dict[str, JobReceipt] = {}

    def create(self, receipt: JobReceipt) -> None:
        if receipt.job_id in self._receipts:
            raise KeyError(receipt.job_id)
        self._receipts[receipt.job_id] = receipt

    def save(self, receipt: JobReceipt) -> None:
        self._receipts[receipt.job_id] = receipt

    def update_status(
        self,
        *,
        job_id: str,
        new_status: str,
        finished_at=None,
        stats=None,
    ) -> None:
        if job_id not in self._receipts:
            raise KeyError(job_id)

        r = self._receipts[job_id]

        self._receipts[job_id] = JobReceipt.build(
            job_id=r.job_id,
            region=r.region,
            mode=r.mode,
            started_at=r.started_at,
            finished_at=finished_at or r.finished_at,
            status=new_status,
            stats=stats or r.stats,
            previous_status=r.status,
        )

    def get(self, job_id: str) -> JobReceipt:
        if job_id not in self._receipts:
            raise KeyError(job_id)
        return self._receipts[job_id]

    def list_recent(self, limit: int = 25) -> list[JobReceipt]:
        return list(self._receipts.values())[:limit]

    def list_receipts(self, limit: int) -> list[JobReceipt]:
        return self.list_recent(limit)


