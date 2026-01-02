from sqlalchemy import insert, select
from src.gymdb.db.db_engine import get_engine
from src.gymdb.db.models.job_receipt import job_receipts
from src.gymdb.jobs.receipt import JobReceipt


class JobReceiptStoreDB:
    def save(self, receipt: JobReceipt) -> None:
        assert isinstance(receipt.stats, dict)

        engine = get_engine()

        with engine.begin() as conn:
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

    def get(self, job_id: str) -> JobReceipt:
        engine = get_engine()

        with engine.begin() as conn:
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
        engine = get_engine()

        with engine.begin() as conn:
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
