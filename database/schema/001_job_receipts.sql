BEGIN;

CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE ops.job_receipts (
    job_id TEXT  PRIMARY KEY,

    region TEXT NOT NULL,
    mode TEXT NOT NULL,

    status TEXT NOT NULL,
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL,
        CHECK (finished_at >= started_at),
    
    stats JSONB NOT NULL,
    deterministic_hash TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX job_receipts_status_idx 
    ON ops.job_receipts (status);

CREATE INDEX job_receipts_region_idx 
    ON ops.job_receipts (region);

CREATE INDEX job_receipts_hash_idx 
    ON ops.job_receipts (deterministic_hash);

COMMIT;