import shutil
import uuid
from pathlib import Path

from gymdb.infrastructure.ops_state_store import OpsStateStore


def _workspace_temp_root(name: str) -> Path:
    root = Path(".tmp") / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_ops_state_store_persists_counter_updates_across_instances():
    root = _workspace_temp_root("ops_state_counters")
    try:
        db_path = root / "ops_state.sqlite3"

        writer = OpsStateStore(db_path)
        reader = OpsStateStore(db_path)

        writer.increment_counters(
            namespace="live_search",
            deltas={"cache_hit": 2, "cache_miss": 1},
        )

        snapshot = reader.snapshot_counters(
            namespace="live_search",
            expected_keys=("cache_hit", "cache_miss", "cache_stale"),
        )

        assert snapshot == {
            "cache_hit": 2,
            "cache_miss": 1,
            "cache_stale": 0,
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_ops_state_store_rate_limit_is_shared_across_instances():
    root = _workspace_temp_root("ops_state_rate_limit")
    try:
        db_path = root / "ops_state.sqlite3"

        first = OpsStateStore(db_path)
        second = OpsStateStore(db_path)

        allowed, retry_after = first.consume_rate_limit_token(
            scope="live-search",
            bucket_key="127.0.0.1",
            limit=1,
            window_seconds=60,
        )
        assert allowed is True
        assert retry_after is None

        allowed, retry_after = second.consume_rate_limit_token(
            scope="live-search",
            bucket_key="127.0.0.1",
            limit=1,
            window_seconds=60,
        )
        assert allowed is False
        assert retry_after is not None
        assert retry_after >= 1
    finally:
        shutil.rmtree(root, ignore_errors=True)
