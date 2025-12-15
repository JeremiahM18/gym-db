from gymdb.processing import deduplicate

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
        }
    ]

    gyms = deduplicate(elements)
    assert len(gyms) == 1
    assert len(gyms[0].osm_refs) == 2

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
        }
    ]

    gyms = deduplicate(elements)
    assert len(gyms) == 2