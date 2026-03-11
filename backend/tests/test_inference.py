from gymdb.domain.constants import IS_24_7, LIFTER_FRIENDLY, PREMIUM_SCORE, SPECIALTY
from gymdb.domain.inference import apply_inference
from gymdb.domain.models import Gym


def make_gym(tags):
    return Gym(
        name="Test Gym",
        norm_name="test gym",
        lat=0.0,
        lon=0.0,
        osm_refs=[{"type": "node", "id": 1}],
        tags=tags,
    )


def test_24_7_inference():
    gym = make_gym({"opening_hours": "24/7"})
    apply_inference(gym)

    result = gym.inferred[IS_24_7]

    assert result.value is True
    assert result.reasons
    assert any("opening_hours" in reason for reason in result.reasons)


def test_lifter_friendly_by_name():
    gym = make_gym({"name": "Iron Barbell Club"})
    apply_inference(gym)

    result = gym.inferred[LIFTER_FRIENDLY]

    assert result.value is True
    assert result.reasons


def test_premium_score_with_pool_and_website():
    gym = make_gym({"swimming_pool": "yes", "website": "http://example.com"})
    apply_inference(gym)

    result = gym.inferred[PREMIUM_SCORE]

    assert result.value >= 3
    assert result.reasons


def test_specialty_inference_for_strength_gym():
    gym = make_gym(
        {
            "name": "Elite Power Barbell",
            "sport": "powerlifting;fitness",
            "website": "https://elite.example.com",
        }
    )
    apply_inference(gym)

    result = gym.inferred[SPECIALTY]

    assert result.value == "powerlifting"
    assert result.reasons
