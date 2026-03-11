from gymdb.config import DEDUP_DISTANCE_METERS
from gymdb.domain.processing import compute_gym_id, deduplicate, haversine_meters


def test_dedup_same_name_close_distance():
    elements = [
        {
            "type": "node",
            "id": 1,
            "lat": 36.0,
            "lon": -86.0,
            "tags": {"name": "Iron House"},
        },
        {
            "type": "node",
            "id": 2,
            "lat": 36.0001,
            "lon": -86.0001,
            "tags": {"name": "Iron House"},
        },
    ]

    gyms = deduplicate(elements)

    assert len(gyms) == 1
    assert len(gyms[0].osm_refs) == 2

    gym = gyms[0]
    gym_id = compute_gym_id(gym.norm_name, gym.lat, gym.lon)
    assert isinstance(gym_id, str)
    assert len(gym_id) > 0


def test_no_dedup_far_distance():
    elements = [
        {
            "type": "node",
            "id": 1,
            "lat": 36.0,
            "lon": -86.0,
            "tags": {"name": "Anytime Fitness"},
        },
        {
            "type": "node",
            "id": 2,
            "lat": 36.5,
            "lon": -86.5,
            "tags": {"name": "Anytime Fitness"},
        },
    ]

    gyms = deduplicate(elements)

    assert len(gyms) == 2
    assert gyms[0].osm_refs[0]["id"] != gyms[1].osm_refs[0]["id"]


def test_dedup_finds_matches_across_adjacent_spatial_buckets():
    base_lat = 36.0
    base_lon = -86.0
    nearby_lat = base_lat + 0.00042
    nearby_lon = base_lon

    distance = haversine_meters(base_lat, base_lon, nearby_lat, nearby_lon)
    assert distance <= DEDUP_DISTANCE_METERS

    elements = [
        {
            "type": "node",
            "id": 1,
            "lat": base_lat,
            "lon": base_lon,
            "tags": {"name": "Bucket Gym"},
        },
        {
            "type": "node",
            "id": 2,
            "lat": nearby_lat,
            "lon": nearby_lon,
            "tags": {"name": "Bucket Gym"},
        },
    ]

    gyms = deduplicate(elements)

    assert len(gyms) == 1
    assert [ref["id"] for ref in gyms[0].osm_refs] == [1, 2]
