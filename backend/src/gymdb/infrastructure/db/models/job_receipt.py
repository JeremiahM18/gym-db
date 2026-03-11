from sqlalchemy import (
    Table, Column, Text, TIMESTAMP, MetaData, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(schema="ops")

job_receipts = Table(
    "job_receipts",
    metadata,

    Column("job_id", Text, primary_key=True),

    Column("region", Text, nullable=False),
    Column("mode", Text, nullable=False),

    Column("status", Text, nullable=False),

    Column("started_at", TIMESTAMP(timezone=True), nullable=False),
    Column("finished_at", TIMESTAMP(timezone=True), nullable=True),

    Column("stats", JSONB, nullable=False),
    Column("deterministic_hash", Text, nullable=False),

    Column(
        "created_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),

    CheckConstraint(
        "status IN ('queued', 'running', 'succeeded', 'failed')",
        name="job_receipts_status_check",
    ),
    CheckConstraint(
        "finished_at >= started_at",
        name="job_receipts_time_order_check",
    ),
)

