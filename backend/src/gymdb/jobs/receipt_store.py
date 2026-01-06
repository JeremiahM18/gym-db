from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from src.gymdb.db.models.job_receipt import job_receipts
from src.gymdb.jobs.receipt import JobReceipt
from src.gymdb.jobs.status import ALLOWED_TRANSITIONS


# Domain-level errors

class JobReceiptError(Exception):
    """Base class for job receipt store errors."""


class JobReceiptNotFound(JobReceiptError):
    """Raised when a job receipt cannot be found."""

    def __init__(self, job_id: str):
        super().__init__(f"JobReceipt not found: {job_id}")
        self.job_id = job_id


class InvalidJobStatusTransition(JobReceiptError):
    """Raised when an invalid lifecycle transition is attempted."""

    def __init__(self, prev_status: str, new_status: str):
        super().__init__(f"Invalid status transition from {prev_status} to {new_status}")
        self.prev_status = prev_status
        self.new_status = new_status


# Store implementation

@dataclass(frozen=True)
class JobReceiptStoreDB:
    """
    Persistent store for JobReceipts.

    Design guarantees:
    - connection is injected (no hidden global get_connection())
    - caller owns transaction boundaries (use `engine.begin()` outside)
    - errors are explicit and semantic (easy to map to HTTP)
    - update lifecycle rules enforced via ALLOWED_TRANSITIONS
    """

    conn: Connection

    # Writes

    def  save(self, receipt: JobReceipt) -> None:
        """
        Idempotent write:
        - insert if new
        - update if existing (upsert)

        Notes:
        - this is safe for retries
        - caller should wrap in a transaction if multiple writes must be atomic
        """
        if not isinstance(receipt.stats, dict):
            raise TypeError("receipt.stats must be a dict")

        stmt = (
            pg_insert(job_receipts)
            .values(
                job_id=receipt.job_id,
                region=receipt.region,
                mode=receipt.mode,
                status=receipt.status,
                started_at=receipt.started_at,
                finished_at=receipt.finished_at,
                stats=receipt.stats,
                deterministic_hash=receipt.deterministic_hash,
            )
            .on_conflict_do_update(
                index_elements=[job_receipts.c.job_id],
                set_={
                    "region": receipt.region,
                    "mode": receipt.mode,
                    "status": receipt.status,
                    "started_at": receipt.started_at,
                    "finished_at": receipt.finished_at,
                    "stats": receipt.stats,
                    "deterministic_hash": receipt.deterministic_hash,
                },
            )
        )

        self.conn.execute(stmt)

    def create(self, receipt: JobReceipt) -> None:
        """
        Strict insert:
        - intended when you expect it NOT to exit already
        - if it exits, the DB should raise integrity error
        """
        if not isinstance(receipt.stats, dict):
            raise TypeError("receipt.stats must be a dict")

        self.conn.execute(
            insert(job_receipts).values(
                job_id=receipt.job_id,
                region=receipt.region,
                mode=receipt.mode,
                status=receipt.status,
                started_at=receipt.started_at,
                finished_at=receipt.finished_at,
                stats=receipt.stats,
                deterministic_hash=receipt.deterministic_hash,
            )
        )

    def update_status(
            self,
            *,
            job_id: str,
            new_status: str,
            finished_at: datetime | None = None,
            stats: dict[str, int],
    ) -> None:
        """
        Update job status with lifecycle enforcement.

        Enterprise rules:
        - same-status updates are idempotent NO-OP
        - transition graph enforced only when status actually changes
        - finished_at / stats can be updated even if status doesn't change
        """

        row = self.conn.execute(
            select(job_receipts.c.status).where(
                job_receipts.c.job_id == job_id
            )
        ).first()
             
        if row is None:
            raise JobReceiptNotFound(job_id)
            
        prev_status: str = row[0]

        # Idempotent: if nothing changes, do nothing
        if prev_status == new_status:
            # Still allow setting finished_at even if status is same
            values: dict[str, Any] = {}
            if finished_at is not None:
                values["finished_at"] = finished_at
            if stats is not None:
                values["stats"] = stats

            if values:
                self.conn.execute(
                    update(job_receipts)
                    .where(job_receipts.c.job_id == job_id)
                    .values(**values)
                )
            return

        # Enforce lifecycle rules (only on actual change)
        allowed = ALLOWED_TRANSITIONS.get(prev_status, set())
        if new_status not in allowed:
                raise InvalidJobStatusTransition(prev_status, new_status)
            
        values: dict[str, Any] = {"status": new_status}

        # finished_at can be null for intermediate statuses
        values["finished_at"] = finished_at


        if stats is not None:
            values["stats"] = stats

        self.conn.execute(
            update(job_receipts)
            .where(job_receipts.c.job_id == job_id)
            .values(
                **values
            )
        )

    # Reads

    def get(self, job_id: str) -> JobReceipt:

        row = self.conn.execute(
            select(job_receipts).where(
                job_receipts.c.job_id == job_id
            )
        ).mappings().first()

        if row is None:
            raise JobReceiptNotFound(job_id)

        return JobReceipt(
            job_id=row["job_id"],
            region=row["region"],
            mode=row["mode"],
            status=row["status"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            stats=row["stats"],
            deterministic_hash=row["deterministic_hash"],
        )

    def list_recent(self, limit: int = 25) -> list[JobReceipt]:

        rows = self.conn.execute(
            select(job_receipts)
            .order_by(job_receipts.c.created_at.desc())
            .limit(limit)
        ).mappings().all()

        return [
            JobReceipt(
                job_id=r["job_id"],
                region=r["region"],
                mode=r["mode"],
                status=r["status"],
                started_at=r["started_at"],
                finished_at=r["finished_at"],
                stats=r["stats"],
                deterministic_hash=r["deterministic_hash"],
            )
            for r in rows
        ]
    
    # Backwards-compatibility
    def list_receipts(self, limit: int) -> list[JobReceipt]:
        return self.list_recent(limit=limit)
    