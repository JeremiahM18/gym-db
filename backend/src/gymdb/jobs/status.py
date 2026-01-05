from __future__ import annotations

from typing import Mapping, Set

# Canonical job satus values
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"

ALL_JOB_STATUSES: Set[str] = {
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    JOB_STATUS_FAILED,
}

# Allowed forward-only state transitions
ALLOWED_TRANSITIONS: Mapping[str, Set[str]] = {
    JOB_STATUS_QUEUED: {JOB_STATUS_RUNNING},
    JOB_STATUS_RUNNING: {JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED},
    JOB_STATUS_SUCCEEDED: set(),
    JOB_STATUS_FAILED: set(),
}