from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gymdb.domain.processing import haversine_meters
from gymdb.infrastructure.datasets.read_model import (
    index_path_for_dataset,
    materialize_dataset_read_model,
)
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
        index_path = index_path_for_dataset(dataset_path, dataset_mtime_ns)

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
                materialize_dataset_read_model(
                    region=region,
                    dataset_path=dataset_path,
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
