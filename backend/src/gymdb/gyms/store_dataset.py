from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from gymdb.domain.constants import (
    INFERRED,
    IS_24_7,
    LIFTER_FRIENDLY,
    SPECIALTY,
    TIER,
)
from gymdb.domain.processing import haversine_meters
from gymdb.infrastructure.datasets.registry import DatasetRegistry

_EARTH_RADIUS_METERS = 6_371_000.0
_CACHE_RECHECK_NS = 1_000_000_000
_SQLITE_TIMEOUT_S = 30.0


@dataclass(frozen=True)
class DatasetSnapshot:
    dataset_path: Path
    dataset_mtime_ns: int
    index_path: Path
    checked_at_ns: int


class DatasetGymStore:
    def __init__(
        self,
        registry: DatasetRegistry,
        *,
        cache_recheck_ns: int = _CACHE_RECHECK_NS,
    ):
        self._registry = registry
        self._cache_recheck_ns = cache_recheck_ns
        self._snapshot_cache: dict[str, DatasetSnapshot] = {}
        self._snapshot_lock = threading.Lock()
        self._locals = threading.local()

    @property
    def default_region(self) -> str:
        return self._registry.default_region

    def _parse_dataset_payload(
        self,
        payload: Any,
        *,
        region: str,
        path: Path,
    ) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            results = payload.get("results")
            if isinstance(results, list):
                return results

        raise ValueError(
            "Dataset for region "
            f"`{region}` at {path} must be a list or an object "
            "with a results list"
        )

    def _index_path(self, dataset_path: Path, dataset_mtime_ns: int) -> Path:
        return dataset_path.with_name(f"{dataset_path.stem}.{dataset_mtime_ns}.sqlite3")

    def _extract_inferred_value(self, gym: dict[str, Any], key: str) -> Any:
        inferred = gym.get(INFERRED)
        if not isinstance(inferred, dict):
            inferred = gym.get("inference")
        if not isinstance(inferred, dict):
            return None

        item = inferred.get(key)
        if isinstance(item, dict):
            return item.get("value")
        if hasattr(item, "value"):
            return cast(Any, item).value
        return None

    def _as_optional_float(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        return None

    def _as_optional_bool(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return int(value)
        return None

    def _cleanup_old_indexes(self, dataset_path: Path, keep_path: Path) -> None:
        pattern = f"{dataset_path.stem}.*.sqlite3"
        for candidate in dataset_path.parent.glob(pattern):
            if candidate == keep_path:
                continue
            try:
                candidate.unlink()
            except OSError:
                continue

    def _build_index(
        self,
        *,
        region: str,
        dataset_path: Path,
        index_path: Path,
    ) -> None:
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        gyms = self._parse_dataset_payload(payload, region=region, path=dataset_path)

        temp_path = index_path.with_suffix(f"{index_path.suffix}.tmp")
        if temp_path.exists():
            temp_path.unlink()

        connection = sqlite3.connect(temp_path, timeout=_SQLITE_TIMEOUT_S)
        try:
            connection.execute("PRAGMA journal_mode = OFF")
            connection.execute("PRAGMA synchronous = OFF")
            connection.execute("PRAGMA temp_store = MEMORY")
            connection.execute(
                """
                CREATE TABLE gyms (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    tier TEXT,
                    specialty TEXT,
                    lifter_friendly INTEGER,
                    is_24_7 INTEGER,
                    lat REAL,
                    lon REAL
                )
                """
            )
            connection.execute(
                "CREATE INDEX idx_gyms_confidence "
                "ON gyms(confidence_score DESC, id)"
            )
            connection.execute(
                "CREATE INDEX idx_gyms_tier_conf "
                "ON gyms(tier, confidence_score DESC, id)"
            )
            connection.execute(
                "CREATE INDEX idx_gyms_specialty_conf "
                "ON gyms(specialty, confidence_score DESC, id)"
            )
            connection.execute(
                "CREATE INDEX idx_gyms_lifter_conf "
                "ON gyms(lifter_friendly, confidence_score DESC, id)"
            )
            connection.execute(
                "CREATE INDEX idx_gyms_247_conf "
                "ON gyms(is_24_7, confidence_score DESC, id)"
            )
            connection.execute(
                "CREATE INDEX idx_gyms_geo_filter "
                "ON gyms(lat, lon, specialty, tier, confidence_score DESC, id)"
            )

            rows: list[tuple[Any, ...]] = []
            for gym in gyms:
                gym_id = gym.get("id")
                if not isinstance(gym_id, str) or not gym_id:
                    continue
                rows.append(
                    (
                        gym_id,
                        json.dumps(gym, separators=(",", ":"), ensure_ascii=True),
                        float(gym.get("confidence_score", 0.0)),
                        self._extract_inferred_value(gym, TIER),
                        self._extract_inferred_value(gym, SPECIALTY),
                        self._as_optional_bool(
                            self._extract_inferred_value(gym, LIFTER_FRIENDLY)
                        ),
                        self._as_optional_bool(
                            self._extract_inferred_value(gym, IS_24_7)
                        ),
                        self._as_optional_float(gym.get("lat")),
                        self._as_optional_float(gym.get("lon")),
                    )
                )

            connection.executemany(
                """
                INSERT INTO gyms(
                    id,
                    payload,
                    confidence_score,
                    tier,
                    specialty,
                    lifter_friendly,
                    is_24_7,
                    lat,
                    lon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            connection.commit()
        finally:
            connection.close()

        temp_path.replace(index_path)
        self._cleanup_old_indexes(dataset_path, index_path)

    def _ensure_snapshot(self, region: str) -> DatasetSnapshot:
        dataset_path = self._registry.dataset_path(region)
        cached = self._snapshot_cache.get(region)
        now_ns = time.monotonic_ns()

        if cached is not None and cached.dataset_path == dataset_path:
            if now_ns - cached.checked_at_ns <= self._cache_recheck_ns:
                return cached

        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found for region `{region}`: {dataset_path}"
            )

        dataset_mtime_ns = dataset_path.stat().st_mtime_ns
        index_path = self._index_path(dataset_path, dataset_mtime_ns)

        with self._snapshot_lock:
            cached = self._snapshot_cache.get(region)
            if cached is not None and cached.dataset_path == dataset_path:
                if (
                    cached.dataset_mtime_ns == dataset_mtime_ns
                    and index_path.exists()
                    and now_ns - cached.checked_at_ns <= self._cache_recheck_ns
                ):
                    return cached

            if not index_path.exists():
                self._build_index(
                    region=region,
                    dataset_path=dataset_path,
                    index_path=index_path,
                )

            snapshot = DatasetSnapshot(
                dataset_path=dataset_path,
                dataset_mtime_ns=dataset_mtime_ns,
                index_path=index_path,
                checked_at_ns=now_ns,
            )
            self._snapshot_cache[region] = snapshot
            return snapshot

    def _connections(self) -> dict[str, tuple[Path, sqlite3.Connection]]:
        connections = getattr(self._locals, "connections", None)
        if connections is None:
            connections = {}
            self._locals.connections = connections
        return connections

    def _connection_for(self, region: str) -> sqlite3.Connection:
        snapshot = self._ensure_snapshot(region)
        connections = self._connections()
        existing = connections.get(region)
        if existing is not None:
            existing_path, connection = existing
            if existing_path == snapshot.index_path:
                return connection
            connection.close()

        connection = sqlite3.connect(
            f"file:{snapshot.index_path}?mode=ro",
            uri=True,
            timeout=_SQLITE_TIMEOUT_S,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connections[region] = (snapshot.index_path, connection)
        return connection

    def _build_filter_where(
        self,
        *,
        min_conf: float | None,
        tier: str | None,
        specialty: str | None,
        lifter_friendly: bool | None,
        is_24_7: bool | None,
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if min_conf is not None:
            clauses.append("confidence_score >= ?")
            params.append(min_conf)
        if tier is not None:
            clauses.append("tier = ?")
            params.append(tier)
        if specialty is not None:
            clauses.append("specialty = ?")
            params.append(specialty)
        if lifter_friendly is not None:
            clauses.append("lifter_friendly = ?")
            params.append(int(lifter_friendly))
        if is_24_7 is not None:
            clauses.append("is_24_7 = ?")
            params.append(int(is_24_7))

        if not clauses:
            return "", params
        return f" WHERE {' AND '.join(clauses)}", params

    def filter(
        self,
        *,
        region: str,
        min_conf: float | None = None,
        tier: str | None = None,
        specialty: str | None = None,
        lifter_friendly: bool | None = None,
        is_24_7: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        connection = self._connection_for(region)
        where_sql, params = self._build_filter_where(
            min_conf=min_conf,
            tier=tier,
            specialty=specialty,
            lifter_friendly=lifter_friendly,
            is_24_7=is_24_7,
        )
        rows = connection.execute(
            (
                "SELECT payload FROM gyms"
                f"{where_sql}"
                " ORDER BY confidence_score DESC, id"
                " LIMIT ? OFFSET ?"
            ),
            [*params, limit, offset],
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def nearby(
        self,
        *,
        region: str,
        lat: float,
        lon: float,
        radius_m: float,
        min_conf: float | None = None,
        tier: str | None = None,
        specialty: str | None = None,
        lifter_friendly: bool | None = None,
        is_24_7: bool | None = None,
    ) -> list[dict[str, Any]]:
        connection = self._connection_for(region)
        lat_delta = math.degrees(radius_m / _EARTH_RADIUS_METERS)
        cos_lat = math.cos(math.radians(lat))
        lon_delta = 180.0 if abs(cos_lat) < 1e-12 else lat_delta / abs(cos_lat)

        where_sql, params = self._build_filter_where(
            min_conf=min_conf,
            tier=tier,
            specialty=specialty,
            lifter_friendly=lifter_friendly,
            is_24_7=is_24_7,
        )
        bbox_sql = (
            "lat IS NOT NULL AND lon IS NOT NULL "
            "AND lat BETWEEN ? AND ? "
            "AND lon BETWEEN ? AND ?"
        )
        if where_sql:
            query = (
                "SELECT payload, lat, lon FROM gyms"
                f"{where_sql} AND {bbox_sql}"
                " ORDER BY confidence_score DESC, id"
            )
        else:
            query = (
                "SELECT payload, lat, lon FROM gyms"
                f" WHERE {bbox_sql}"
                " ORDER BY confidence_score DESC, id"
            )

        rows = connection.execute(
            query,
            [
                *params,
                lat - lat_delta,
                lat + lat_delta,
                lon - lon_delta,
                lon + lon_delta,
            ],
        ).fetchall()

        candidates: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            row_lat = float(row["lat"])
            row_lon = float(row["lon"])
            distance = haversine_meters(lat, lon, row_lat, row_lon)
            if distance <= radius_m:
                candidates.append((distance, json.loads(row["payload"])))

        candidates.sort(key=lambda item: item[0])
        return [gym for _, gym in candidates]

    def get_by_id(self, region: str, gym_id: str) -> dict[str, Any] | None:
        connection = self._connection_for(region)
        row = connection.execute(
            "SELECT payload FROM gyms WHERE id = ?",
            [gym_id],
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])


GymStore = DatasetGymStore
