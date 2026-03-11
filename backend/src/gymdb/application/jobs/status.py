from __future__ import annotations

from collections.abc import Mapping

# Canonical job satus values
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"

ALL_JOB_STATUSES: set[str] = {
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    JOB_STATUS_FAILED,
}

# Allowed forward-only state transitions
ALLOWED_TRANSITIONS: Mapping[str, set[str]] = {
    JOB_STATUS_QUEUED: {JOB_STATUS_RUNNING},
    JOB_STATUS_RUNNING: {JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED},
    JOB_STATUS_SUCCEEDED: set(),
    JOB_STATUS_FAILED: set(),
}

