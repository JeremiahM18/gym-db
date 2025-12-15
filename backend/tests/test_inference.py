from gymdb.models import Gym
from gymdb.inference import apply_inference
from gymdb.domain import IS_24_7, LIFTER_FRIENDLY, PREMIUM_SCORE

def make_gym(tags):
    return Gym(
        name = "Test Gym",
        norm_name=" test gym",
        lat=0.0,
        lon=0.0,
        osm_refs=[{"type": "node", "id": 1}],
        tags=tags
    )

def test_24_7_inference():
    gym = make_gym({"opening_hours": "24/7"})
    apply_inference(gym)

    assert gym.inferred[IS_24_7] is True
    assert "opening_hours" in gym.inference_reasons[IS_24_7][0]

def test_lifter_friendly_by_name():
    gym = make_gym({"name": "Iron Barbell Club"})
    apply_inference(gym)

    assert gym.inferred[LIFTER_FRIENDLY] is True

def test_premium_score_with_pool_and_website():
    gym = make_gym({"swimming_pool": "yes", "website": "http://example.com"})
    apply_inference(gym)

    assert gym.inferred[PREMIUM_SCORE] >= 3