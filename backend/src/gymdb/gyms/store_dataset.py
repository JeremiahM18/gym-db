from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gymdb.domain.processing import haversine_meters
from gymdb.infrastructure.datasets.registry import DatasetRegistry

_GRID_DEGREES = 0.05
_EARTH_RADIUS_METERS = 6_371_000.0
_MAX_INDEX_SCAN_CELLS = 256
_MIN_GEO_INDEX_GYMS = 100_000
_CACHE_RECHECK_NS = 1_000_000_000


@dataclass(frozen=True)
class DatasetSnapshot:
    path: Path
    mtime_ns: int
    checked_at_ns: int
    gyms: tuple[dict[str, Any], ...]
    by_id: dict[str, dict[str, Any]]
    by_conf_desc: tuple[dict[str, Any], ...]
    geo_cells: dict[tuple[int, int], tuple[dict[str, Any], ...]]
    min_lat: float | None
    max_lat: float | None
    min_lon: float | None
    max_lon: float | None


class DatasetGymStore:
    def __init__(
        self,
        registry: DatasetRegistry,
        *,
        cache_recheck_ns: int = _CACHE_RECHECK_NS,
    ):
        self._registry = registry
        self._cache_recheck_ns = cache_recheck_ns
        self._cache: dict[str, DatasetSnapshot] = {}

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

    def _cell_key(self, lat: float, lon: float) -> tuple[int, int]:
        return (math.floor(lat / _GRID_DEGREES), math.floor(lon / _GRID_DEGREES))

    def _bounding_box(
        self,
        lat: float,
        lon: float,
        radius_m: float,
    ) -> tuple[float, float, float, float]:
        lat_delta = math.degrees(radius_m / _EARTH_RADIUS_METERS)
        cos_lat = math.cos(math.radians(lat))
        lon_delta = 180.0 if abs(cos_lat) < 1e-12 else lat_delta / abs(cos_lat)
        return (
            lat - lat_delta,
            lat + lat_delta,
            lon - lon_delta,
            lon + lon_delta,
        )

    def _load_dataset(self, region: str) -> DatasetSnapshot:
        path = self._registry.dataset_path(region)
        cached = self._cache.get(region)
        now_ns = time.monotonic_ns()

        if cached is not None and cached.path == path:
            if now_ns - cached.checked_at_ns <= self._cache_recheck_ns:
                return cached

            if not path.exists():
                raise FileNotFoundError(
                    f"Dataset not found for region `{region}`: {path}"
                )

            mtime_ns = path.stat().st_mtime_ns
            if cached.mtime_ns == mtime_ns:
                refreshed = DatasetSnapshot(
                    path=cached.path,
                    mtime_ns=cached.mtime_ns,
                    checked_at_ns=now_ns,
                    gyms=cached.gyms,
                    by_id=cached.by_id,
                    by_conf_desc=cached.by_conf_desc,
                    geo_cells=cached.geo_cells,
                    min_lat=cached.min_lat,
                    max_lat=cached.max_lat,
                    min_lon=cached.min_lon,
                    max_lon=cached.max_lon,
                )
                self._cache[region] = refreshed
                return refreshed
        elif not path.exists():
            raise FileNotFoundError(
                f"Dataset not found for region `{region}`: {path}"
            )

        mtime_ns = path.stat().st_mtime_ns
        payload = json.loads(path.read_text(encoding="utf-8"))
        gyms = tuple(self._parse_dataset_payload(payload, region=region, path=path))

        geo_cells: dict[tuple[int, int], list[dict[str, Any]]] = {}
        latitudes: list[float] = []
        longitudes: list[float] = []
        for gym in gyms:
            gym_lat = gym.get("lat")
            gym_lon = gym.get("lon")
            if (
                not isinstance(gym_lat, int | float)
                or not isinstance(gym_lon, int | float)
            ):
                continue
            key = self._cell_key(gym_lat, gym_lon)
            geo_cells.setdefault(key, []).append(gym)
            latitudes.append(float(gym_lat))
            longitudes.append(float(gym_lon))

        snapshot = DatasetSnapshot(
            path=path,
            mtime_ns=mtime_ns,
            checked_at_ns=now_ns,
            gyms=gyms,
            by_id={gym["id"]: gym for gym in gyms if "id" in gym},
            by_conf_desc=tuple(
                sorted(
                    gyms,
                    key=lambda gym: gym.get("confidence_score", 0.0),
                    reverse=True,
                )
            ),
            geo_cells={key: tuple(value) for key, value in geo_cells.items()},
            min_lat=min(latitudes) if latitudes else None,
            max_lat=max(latitudes) if latitudes else None,
            min_lon=min(longitudes) if longitudes else None,
            max_lon=max(longitudes) if longitudes else None,
        )
        self._cache[region] = snapshot
        return snapshot

    def _filter_by_confidence(
        self,
        gyms: tuple[dict[str, Any], ...] | list[dict[str, Any]],
        min_conf: float | None,
        *,
        assume_descending: bool,
    ) -> list[dict[str, Any]]:
        if min_conf is None:
            return list(gyms)

        filtered: list[dict[str, Any]] = []
        for gym in gyms:
            if gym.get("confidence_score", 0.0) < min_conf:
                if assume_descending:
                    break
                continue
            filtered.append(gym)
        return filtered

    def _nearby_by_scan(
        self,
        gyms: tuple[dict[str, Any], ...] | list[dict[str, Any]],
        *,
        lat: float,
        lon: float,
        radius_m: float,
        min_conf: float | None,
        assume_descending: bool,
    ) -> list[dict[str, Any]]:
        candidates: list[tuple[float, dict[str, Any]]] = []

        for gym in gyms:
            if min_conf is not None and gym.get("confidence_score", 0.0) < min_conf:
                if assume_descending:
                    break
                continue

            gym_lat = gym.get("lat")
            gym_lon = gym.get("lon")
            if (
                not isinstance(gym_lat, int | float)
                or not isinstance(gym_lon, int | float)
            ):
                continue
            distance = haversine_meters(lat, lon, gym_lat, gym_lon)
            if distance <= radius_m:
                candidates.append((distance, gym))

        candidates.sort(key=lambda item: item[0])
        return [gym for _, gym in candidates]

    def filter(
        self,
        *,
        region: str,
        min_conf: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        snapshot = self._load_dataset(region)
        base = snapshot.by_conf_desc if min_conf is not None else snapshot.gyms
        gyms = self._filter_by_confidence(
            base,
            min_conf,
            assume_descending=min_conf is not None,
        )
        return gyms[offset : offset + limit]

    def nearby(
        self,
        *,
        region: str,
        lat: float,
        lon: float,
        radius_m: float,
        min_conf: float | None = None,
    ) -> list[dict[str, Any]]:
        snapshot = self._load_dataset(region)
        min_lat, max_lat, min_lon, max_lon = self._bounding_box(lat, lon, radius_m)
        min_cell = self._cell_key(min_lat, min_lon)
        max_cell = self._cell_key(max_lat, max_lon)
        lat_cells = max_cell[0] - min_cell[0] + 1
        lon_cells = max_cell[1] - min_cell[1] + 1
        cell_count = lat_cells * lon_cells
        covers_dataset_bounds = (
            snapshot.min_lat is not None
            and snapshot.max_lat is not None
            and snapshot.min_lon is not None
            and snapshot.max_lon is not None
            and min_lat <= snapshot.min_lat
            and max_lat >= snapshot.max_lat
            and min_lon <= snapshot.min_lon
            and max_lon >= snapshot.max_lon
        )
        should_use_geo_index = (
            len(snapshot.gyms) >= _MIN_GEO_INDEX_GYMS
            and not covers_dataset_bounds
            and cell_count <= _MAX_INDEX_SCAN_CELLS
        )

        if not should_use_geo_index:
            base = snapshot.by_conf_desc if min_conf is not None else snapshot.gyms
            return self._nearby_by_scan(
                base,
                lat=lat,
                lon=lon,
                radius_m=radius_m,
                min_conf=min_conf,
                assume_descending=min_conf is not None,
            )

        candidates: list[tuple[float, dict[str, Any]]] = []
        seen_ids: set[str] = set()
        for lat_cell in range(min_cell[0], max_cell[0] + 1):
            for lon_cell in range(min_cell[1], max_cell[1] + 1):
                for gym in snapshot.geo_cells.get((lat_cell, lon_cell), ()):
                    gym_id = gym.get("id")
                    if not isinstance(gym_id, str):
                        continue
                    if gym_id in seen_ids:
                        continue
                    seen_ids.add(gym_id)

                    gym_lat = gym.get("lat")
                    gym_lon = gym.get("lon")
                    if (
                        not isinstance(gym_lat, int | float)
                        or not isinstance(gym_lon, int | float)
                    ):
                        continue
                    if not (
                        min_lat <= gym_lat <= max_lat
                        and min_lon <= gym_lon <= max_lon
                    ):
                        continue
                    if (
                        min_conf is not None
                        and gym.get("confidence_score", 0.0) < min_conf
                    ):
                        continue

                    distance = haversine_meters(lat, lon, gym_lat, gym_lon)
                    if distance <= radius_m:
                        candidates.append((distance, gym))

        candidates.sort(key=lambda item: item[0])
        return [gym for _, gym in candidates]

    def get_by_id(self, region: str, gym_id: str) -> dict[str, Any] | None:
        snapshot = self._load_dataset(region)
        return snapshot.by_id.get(gym_id)


GymStore = DatasetGymStore

