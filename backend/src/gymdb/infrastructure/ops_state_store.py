from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterable
from math import ceil
from pathlib import Path


class OpsStateStore:
    """Durable host-local store for lightweight ops counters and rate limits."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                namespace TEXT NOT NULL,
                metric_key TEXT NOT NULL,
                metric_value INTEGER NOT NULL,
                updated_at_epoch_s REAL NOT NULL,
                PRIMARY KEY (namespace, metric_key)
            );

            CREATE TABLE IF NOT EXISTS rate_limit_events (
                scope TEXT NOT NULL,
                bucket_key TEXT NOT NULL,
                observed_at_epoch_s REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_rate_limit_events_scope_bucket_time
            ON rate_limit_events (scope, bucket_key, observed_at_epoch_s);
            """
        )

    def increment_counters(
        self,
        *,
        namespace: str,
        deltas: dict[str, int],
    ) -> None:
        if not deltas:
            return

        timestamp = time.time()
        rows = [
            (namespace, key, delta, timestamp)
            for key, delta in deltas.items()
            if delta > 0
        ]
        if not rows:
            return

        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.executemany(
                """
                INSERT INTO metrics (
                    namespace,
                    metric_key,
                    metric_value,
                    updated_at_epoch_s
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(namespace, metric_key) DO UPDATE SET
                    metric_value = metrics.metric_value + excluded.metric_value,
                    updated_at_epoch_s = excluded.updated_at_epoch_s
                """,
                rows,
            )

    def snapshot_counters(
        self,
        *,
        namespace: str,
        expected_keys: Iterable[str] = (),
    ) -> dict[str, int]:
        snapshot = {key: 0 for key in expected_keys}
        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                """
                SELECT metric_key, metric_value
                FROM metrics
                WHERE namespace = ?
                """,
                (namespace,),
            ).fetchall()

        for key, value in rows:
            snapshot[str(key)] = int(value)
        return snapshot

    def reset_counters(self, *, namespace: str | None = None) -> None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            if namespace is None:
                conn.execute("DELETE FROM metrics")
            else:
                conn.execute(
                    "DELETE FROM metrics WHERE namespace = ?",
                    (namespace,),
                )

    def consume_rate_limit_token(
        self,
        *,
        scope: str,
        bucket_key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int | None]:
        now_epoch_s = time.time()
        cutoff_epoch_s = now_epoch_s - window_seconds

        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """
                    DELETE FROM rate_limit_events
                    WHERE scope = ?
                      AND bucket_key = ?
                      AND observed_at_epoch_s <= ?
                    """,
                    (scope, bucket_key, cutoff_epoch_s),
                )
                active_count = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM rate_limit_events
                    WHERE scope = ?
                      AND bucket_key = ?
                    """,
                    (scope, bucket_key),
                ).fetchone()[0]

                if active_count >= limit:
                    oldest_epoch_s = conn.execute(
                        """
                        SELECT observed_at_epoch_s
                        FROM rate_limit_events
                        WHERE scope = ?
                          AND bucket_key = ?
                        ORDER BY observed_at_epoch_s ASC
                        LIMIT 1
                        """,
                        (scope, bucket_key),
                    ).fetchone()[0]
                    conn.commit()
                    retry_after = max(
                        1,
                        ceil(window_seconds - (now_epoch_s - float(oldest_epoch_s))),
                    )
                    return False, retry_after

                conn.execute(
                    """
                    INSERT INTO rate_limit_events (
                        scope,
                        bucket_key,
                        observed_at_epoch_s
                    ) VALUES (?, ?, ?)
                    """,
                    (scope, bucket_key, now_epoch_s),
                )
                conn.commit()
                return True, None
            except Exception:
                conn.rollback()
                raise

    def reset_rate_limit_events(self) -> None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("DELETE FROM rate_limit_events")
