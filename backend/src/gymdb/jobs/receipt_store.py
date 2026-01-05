from __future__ import annotations

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from datetime import datetime
from typing import Any

from src.gymdb.db.db_engine import get_connection
from src.gymdb.db.models.job_receipt import job_receipts
from src.gymdb.jobs.receipt import JobReceipt
from src.gymdb.jobs.status import ALLOWED_TRANSITIONS


class JobReceiptStoreDB:
    """
    Persistent store for JobReceipts.

    Public contract used by routes and tests:
    - create(): insert only (fail if exists)
    - save(): upsert-like behavior (legacy compatibility)
    - get(): fetch by job_id
    - list_recent(): list recent receipts
    - update_status(): update status with lifecycle enforcement
    """

    def  save(self, receipt: JobReceipt) -> None:
        """
        Idempotent write:
        - Insert if new
        - Update if existing
        """
        assert isinstance(receipt.stats, dict)

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

        conn = get_connection()
        conn.execute(stmt)

    def create(self, receipt: JobReceipt) -> None:
        """
        Strict insert. Use when you *expect* it not to exist already.
        """
        assert isinstance(receipt.stats, dict)


        conn = get_connection()
        conn.execute(
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
        - Same-status updates are idempotent NO-OP
        - Transition graph enforced only when status actually changes
        - Stats are optional, update only when provided
        """
        conn = get_connection()

        row = conn.execute(
            select(job_receipts.c.status).where(
                job_receipts.c.job_id == job_id
            )
        ).first()
             
        if row is None:
            raise KeyError(job_id)
            
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
                conn.execute(
                    update(job_receipts)
                    .where(job_receipts.c.job_id == job_id)
                    .values(**values)
                )
            return

        # Enforce lifecycle rules
        allowed = ALLOWED_TRANSITIONS.get(prev_status, set())
        if new_status not in allowed:
                raise ValueError(
                    f"Invalid status transition from {prev_status} to {new_status}"
                )
            
        values: dict[str, Any] = {
            "status": new_status,
            "finished_at": finished_at,
        }
        if stats is not None:
            values["stats"] = stats

        conn.execute(
            update(job_receipts)
            .where(job_receipts.c.job_id == job_id)
            .values(
                **values
            )
        )

    def get(self, job_id: str) -> JobReceipt:

        conn = get_connection()
        row = conn.execute(
            select(job_receipts).where(
                job_receipts.c.job_id == job_id
            )
        ).mappings().first()
        if row is None:
            raise KeyError(job_id)

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

        conn = get_connection()
        rows = conn.execute(
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
    
    def list_receipts(self, limit: int) -> list[JobReceipt]:
        return self.list_recent(limit=limit)
    