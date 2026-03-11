import math
import re
import hashlib
from gymdb.domain.models import Gym
from gymdb.config import DEDUP_DISTANCE_METERS

def normalize_name(name: str) -> str:
    # Remove extra whitespace, newlines, etc.
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    return name

def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    R = 6371000  # Radius of the Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2 
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def extract_lat_lon(el: dict):
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

def deduplicate(elements: list[dict]) -> list[Gym]:
    gyms: list[Gym] = []

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        lat, lon = extract_lat_lon(el)
        if lat is None or lon is None:
            continue

        norm = normalize_name(name)
        match = None

        for g in gyms:
            if g.norm_name == norm:
                dist = haversine_meters(lat, lon, g.lat, g.lon)
                if dist <= DEDUP_DISTANCE_METERS:
                    match = g
                    break

        if match:
            match.osm_refs.append({"type": el["type"], "id": el["id"]})
        else:
            gyms.append(
                Gym(
                    name=name,
                    norm_name=norm,
                    lat=lat,
                    lon=lon,
                    osm_refs=[{"type": el["type"], "id": el["id"]}],
                    tags=tags,
                )
            )

    return gyms

