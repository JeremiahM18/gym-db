import argparse
import json
import math
from pathlib import Path

import requests
import re


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def miles_to_meters(miles: float) -> float:
    return miles * 1609.344

def build_query(radius_meters: float, lat: float, lon: float) -> str:
    # Pull both common gym tags in OSM:
    # leisure=fitness_centre
    # amenity=gym
    return f"""
[out:json][timeout:25];
(
    node["leisure"="fitness_centre"](around:{radius_meters},{lat},{lon});
    way["leisure"="fitness_centre"](around:{radius_meters},{lat},{lon});
    relation["leisure"="fitness_centre"](around:{radius_meters},{lat},{lon});
    
    node["amenity"="gym"](around:{radius_meters},{lat},{lon});
    way["amenity"="gym"](around:{radius_meters},{lat},{lon});
    relation["amenity"="gym"](around:{radius_meters},{lat},{lon});
);
out center tags;
"""

def extract_lat_lon(element: dict) -> tuple[float | None, float | None]:
    # Nodes have lat/lon directly; ways/relations have a 'center' field
    lat = element.get("lat")
    lon = element.get("lon")
    if lat is None or lon is None:
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
    return lat, lon

def normalize_name(name: str) -> str:
    # Remove extra whitespace, newlines, etc.
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
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
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch gyms from OpenStreetMap via Overpass API within a radius of a location."
    )
    parser.add_argument("--lat", type=float, default=36.1627, help="Center latitude (default: Nashville).")
    parser.add_argument("--lon", type=float, default=-86.7816, help="Center longitude (default: Nashville).")
    parser.add_argument("--radius-miles", type=float, default=30.0, help="Search radius in miles (default: 30).")
    parser.add_argument(
        "--out",
        type=str,
        default=str(Path("data") / "gyms_raw.json"),
        help="Output JSON path (default: data/gyms_raw.json).",
    )
    args = parser.parse_args()

    radius_meters = miles_to_meters(args.radius_miles)
    query = build_query(radius_meters, args.lat, args.lon)

    print(f"Querying Overpass... center=({args.lat}, {args.lon}), radius={args.radius_miles} miles")
    resp = requests.post(OVERPASS_URL, data=query, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    elements = data.get("elements", [])
    gyms = []
    seen = []

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        
        lat, lon = extract_lat_lon(el)
        if lat is None or lon is None:
            continue

        norm = normalize_name(name)
        duplicate = None

        for existing in seen:
            dist = haversine_meters(
                lat, lon,
                existing["lat"], existing["lon"],
            )
            if dist <= 50 and norm == existing["norm_name"]:
                duplicate = existing
                break

        if duplicate:
            duplicate["osm_refs"].append(
                {"type": el.get("type"), "id": el.get("id")}
            )
        else:
            gym = {
                "name": name,
                "norm_name": norm,
                "lat": lat,
                "lon": lon,
                "osm_refs": [{"type": el.get("type"), "id": el.get("id")}],
                "tags": tags,
            }
            gyms.append(gym)
            seen.append(gym)
        
    # Clean up for output
    cleaned = []
    for g in gyms:
        cleaned.append(
            {
                "name": g["name"],
                "lat": g["lat"],
                "lon": g["lon"],
                "osm_refs": g["osm_refs"],
                "tags": g["tags"],
            }
        )

    # Save results
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")

    print(f"Found {len(gyms)} named gyms")
    print(f"Saved: {out_path.resolve()}")
    print("\nSample:")
    for i, g in enumerate(gyms[:10], start=1):
        print(f"{i:2d}. {g['name']} ({g['lat']:.5f}, {g['lon']:.5f})")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
