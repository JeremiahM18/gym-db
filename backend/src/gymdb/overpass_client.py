import requests



OVERPASS_URL = "https://overpass-api.de/api/interpreter"


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

def fetch_gyms(radius_meters: float, lat: float, lon: float) -> list[dict]:
    query = build_query(radius_meters, lat, lon)
    resp = requests.post(OVERPASS_URL, data=query, timeout=60)
    resp.raise_for_status()
    return resp.json().get("elements", [])