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


def dataset_results_to_cache_elements(
    gyms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    for gym in gyms:
        lat = gym.get("lat")
        lon = gym.get("lon")
        tags = gym.get("tags")
        if not isinstance(lat, int | float) or not isinstance(lon, int | float):
            continue
        if not isinstance(tags, dict):
            continue

        osm_refs = gym.get("osm_refs")
        ref = osm_refs[0] if isinstance(osm_refs, list) and osm_refs else {}
        ref_type = ref.get("type") if isinstance(ref, dict) else None
        ref_id = ref.get("id") if isinstance(ref, dict) else None

        if not isinstance(ref_type, str) or not isinstance(ref_id, int):
            ref_type = "node"
            ref_id = int(
                hashlib.sha256(
                    f"{gym.get('id')}|{lat:.6f}|{lon:.6f}".encode()
                ).hexdigest()[:12],
                16,
            )

        elements.append(
            {
                "type": ref_type,
                "id": ref_id,
                "lat": float(lat),
                "lon": float(lon),
                "tags": tags,
            }
        )

    return elements


def prime_cache_from_dataset(
    cache_root: Path,
    *,
    dataset_path: Path,
    lat: float,
    lon: float,
    radius_m: int,
    place_label: str,
    force: bool = False,
) -> Path | None:
    if not dataset_path.exists():
        return None

    if not force:
        existing = load_cached_elements(
            cache_root,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
        )
        if existing is not None:
            return existing.cache_path

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    results = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(results, list) or not results:
        return None

    elements = dataset_results_to_cache_elements(results)
    if not elements:
        return None

    return write_cached_elements(
        cache_root,
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        origin={
            "name": place_label,
            "address": place_label,
            "lat": lat,
            "lon": lon,
        },
        elements=elements,
    )
