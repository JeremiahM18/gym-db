from gymdb.processing import deduplicate, compute_gym_id

def test_dedup_same_name_close_distance():
    # Two gyms with the same name within dedup distance should deduplicate
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
        }
    ]

    gyms = deduplicate(elements)

    assert len(gyms) == 1
    assert len(gyms[0].osm_refs) == 2

    g = gyms[0]
    gym_id = compute_gym_id(g.norm_name, g.lat, g.lon)
    assert isinstance(gym_id, str)
    assert len(gym_id) > 0

def test_no_dedup_far_distance():
    # Two gyms with the same name but far apart should not deduplicate
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
