import hashlib
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from gymdb.config import DEDUP_DISTANCE_METERS
from gymdb.domain.models import Gym

_NAME_SANITIZER_RE = re.compile(r"[^a-z0-9\s]")
_WHITESPACE_RE = re.compile(r"\s+")
_EARTH_RADIUS_METERS = 6_371_000.0
_BUCKET_SIZE_METERS = DEDUP_DISTANCE_METERS


@dataclass(frozen=True)
class SpatialPoint:
    x_m: float
    y_m: float


def normalize_name(name: str) -> str:
    name = name.lower()
    name = _NAME_SANITIZER_RE.sub(" ", name)
    name = _WHITESPACE_RE.sub("_", name).strip("_")
    return name


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_METERS * c


def extract_lat_lon(el: dict[str, Any]) -> tuple[float | None, float | None]:
    lat = el.get("lat")
    lon = el.get("lon")
    if lat is None or lon is None:
        center = el.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
    return lat, lon


def compute_gym_id(norm_name: str, lat: float, lon: float) -> str:
    raw = f"{norm_name}|{lat:.6f}|{lon:.6f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _project_to_meters(lat: float, lon: float) -> SpatialPoint:
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    return SpatialPoint(
        x_m=_EARTH_RADIUS_METERS * lon_rad * math.cos(lat_rad),
        y_m=_EARTH_RADIUS_METERS * lat_rad,
    )


def _bucket_key(point: SpatialPoint) -> tuple[int, int]:
    return (
        math.floor(point.x_m / _BUCKET_SIZE_METERS),
        math.floor(point.y_m / _BUCKET_SIZE_METERS),
    )


def _neighbor_keys(bucket: tuple[int, int]) -> list[tuple[int, int]]:
    x_bucket, y_bucket = bucket
    return [
        (x_bucket + dx, y_bucket + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
    ]


def deduplicate(elements: list[dict[str, Any]]) -> list[Gym]:
    gyms: list[Gym] = []
    by_name_bucket: dict[str, dict[tuple[int, int], list[Gym]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        lat, lon = extract_lat_lon(el)
        if lat is None or lon is None:
            continue

        norm = normalize_name(name)
        point = _project_to_meters(lat, lon)
        bucket = _bucket_key(point)
        buckets = by_name_bucket[norm]

        match: Gym | None = None
        for neighbor in _neighbor_keys(bucket):
            for gym in buckets.get(neighbor, []):
                dist = haversine_meters(lat, lon, gym.lat, gym.lon)
                if dist <= DEDUP_DISTANCE_METERS:
                    match = gym
                    break
            if match is not None:
                break

        if match is not None:
            match.osm_refs.append({"type": el["type"], "id": el["id"]})
            continue

        gym = Gym(
            name=name,
            norm_name=norm,
            lat=lat,
            lon=lon,
            osm_refs=[{"type": el["type"], "id": el["id"]}],
            tags=tags,
        )
        gyms.append(gym)
        buckets[bucket].append(gym)

    return gyms
