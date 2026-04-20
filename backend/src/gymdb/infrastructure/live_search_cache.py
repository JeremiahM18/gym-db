from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


@dataclass(frozen=True)
class LiveSearchCacheEntry:
    cache_path: Path
    cached_at_epoch_s: float
    elements: list[dict[str, Any]]

    @property
    def age_seconds(self) -> float:
        return max(0.0, time.time() - self.cached_at_epoch_s)


def build_live_search_cache_key(*, lat: float, lon: float, radius_m: int) -> str:
    rounded = f"{lat:.3f}|{lon:.3f}|{radius_m}"
    return hashlib.sha256(rounded.encode("utf-8")).hexdigest()[:16]


def cache_path_for_search(
    cache_root: Path,
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> Path:
    key = build_live_search_cache_key(lat=lat, lon=lon, radius_m=radius_m)
    return cache_root / f"{key}.json"


def load_cached_elements(
    cache_root: Path,
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> LiveSearchCacheEntry | None:
    cache_path = cache_path_for_search(
        cache_root,
        lat=lat,
        lon=lon,
        radius_m=radius_m,
    )
    if not cache_path.exists():
        return None

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    elements = payload.get("elements")
    cached_at_epoch_s = payload.get("cached_at_epoch_s")

    if not isinstance(elements, list):
        return None
    if not isinstance(cached_at_epoch_s, int | float):
        return None

    return LiveSearchCacheEntry(
        cache_path=cache_path,
        cached_at_epoch_s=float(cached_at_epoch_s),
        elements=elements,
    )


def write_cached_elements(
    cache_root: Path,
    *,
    lat: float,
    lon: float,
    radius_m: int,
    origin: dict[str, Any],
    elements: list[dict[str, Any]],
) -> Path:
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_path = cache_path_for_search(
        cache_root,
        lat=lat,
        lon=lon,
        radius_m=radius_m,
    )
    payload = {
        "cached_at_epoch_s": time.time(),
        "origin": origin,
        "radius_m": radius_m,
        "elements": elements,
    }
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=cache_root,
        prefix=f"{cache_path.stem}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        json.dump(payload, temp_file, separators=(",", ":"), ensure_ascii=True)
        temp_path = Path(temp_file.name)

    temp_path.replace(cache_path)
    return cache_path
