from gymdb.application.coverage import apply_tomtom_coverage, best_osm_match, classify
from gymdb.domain.models import Gym
from gymdb.infrastructure.tomtom_client import TomTomPlace


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


def test_apply_tomtom_coverage_sets_confirmed_provenance():
    gym = Gym(
        name="Life Time",
        norm_name="life_time",
        lat=35.9236865,
        lon=-86.8145988,
        osm_refs=[{"type": "node", "id": 1}],
        tags={"name": "Life Time", "leisure": "fitness_centre"},
    )
    gym.id = "osm-1"
    place = TomTomPlace(
        id="tt-1",
        name="Life Time",
        lat=35.9237,
        lon=-86.8146,
        address="Franklin, TN",
        city="Franklin",
        country_code="US",
        url="https://www.lifetime.life/",
        raw={},
    )

    matches, summary = apply_tomtom_coverage([gym], [place])

    assert len(matches) == 1
    assert summary.matched == 1
    assert gym.source_provenance["match_status"] == "matched"
    assert gym.source_provenance["confirmed_by"] == ["tomtom"]
    assert gym.source_provenance["external_refs"]["tomtom"]["external_id"] == "tt-1"
