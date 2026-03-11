from gymdb.infrastructure.tomtom_client import TomTomPlace
from scripts.compare_osm_tomtom import best_osm_match, classify


def test_best_osm_match_matches_by_normalized_name_and_distance():
    place = TomTomPlace(
        id="tt-1",
        name="Life Time",
        lat=35.9237,
        lon=-86.8146,
        address="Franklin, TN",
        city="Franklin",
        country_code="US",
        url=None,
        raw={},
    )
    gyms = [
        {
            "id": "osm-1",
            "name": "Life Time",
            "norm_name": "life_time",
            "lat": 35.9236865,
            "lon": -86.8145988,
        }
    ]

    match, distance = best_osm_match(place, gyms)

    assert match is not None
    assert match["id"] == "osm-1"
    assert distance is not None and distance < 50


def test_classify_marks_missing_when_no_osm_match():
    place = TomTomPlace(
        id="tt-2",
        name="Missing Gym",
        lat=35.9,
        lon=-86.8,
        address=None,
        city="Franklin",
        country_code="US",
        url=None,
        raw={},
    )

    result = classify(place, None, None)

    assert result.status == "missing_from_osm"
    assert result.tomtom_name == "Missing Gym"
