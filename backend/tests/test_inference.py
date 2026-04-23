from gymdb.domain.constants import IS_24_7, LIFTER_FRIENDLY, PREMIUM_SCORE, SPECIALTY
from gymdb.domain.inference import apply_inference
from gymdb.domain.models import Gym
from gymdb.observe.metrics import snapshot_metrics


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
    assert result.confidence == 0.98


def test_lifter_friendly_by_name():
    gym = make_gym({"name": "Iron Barbell Club"})
    apply_inference(gym)

    result = gym.inferred[LIFTER_FRIENDLY]

    assert result.value is True
    assert result.reasons
    assert result.confidence is not None


def test_premium_score_with_pool_and_website():
    gym = make_gym({"swimming_pool": "yes", "website": "http://example.com"})
    apply_inference(gym)

    result = gym.inferred[PREMIUM_SCORE]

    assert result.value >= 3
    assert result.reasons
    assert result.confidence is not None


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
    assert result.confidence == 0.93


def test_inference_meta_includes_field_confidence():
    gym = make_gym({"opening_hours": "24/7", "sport": "powerlifting"})
    apply_inference(gym)

    field_confidence = gym.inference_meta["field_confidence"]

    assert set(field_confidence) >= {
        PREMIUM_SCORE,
        IS_24_7,
        LIFTER_FRIENDLY,
        SPECIALTY,
        "tier",
    }
    assert all(0.0 < value <= 1.0 for value in field_confidence.values())


def test_contradiction_detection_penalizes_name_only_strength_inference():
    gym = make_gym({"name": "Power Barbell Yoga", "sport": "yoga"})
    apply_inference(gym)

    contradictions = gym.inference_meta["contradictions"]

    assert LIFTER_FRIENDLY in contradictions
    assert SPECIALTY in contradictions
    assert gym.inferred[LIFTER_FRIENDLY].confidence < 0.6
    assert gym.inferred[SPECIALTY].confidence < 0.5


def test_contradiction_detection_flags_unconfirmed_24_hour_name():
    gym = make_gym({"name": "24 Hour Fitness Franklin"})
    apply_inference(gym)

    contradictions = gym.inference_meta["contradictions"]

    assert IS_24_7 in contradictions
    assert gym.inferred[IS_24_7].value is False
    assert gym.inferred[IS_24_7].confidence < 0.4


def test_apply_inference_records_inference_metrics():
    gym = make_gym({"opening_hours": "24/7"})

    apply_inference(gym)

    metrics = snapshot_metrics()

    assert metrics["premium_score"] == 1
    assert metrics[IS_24_7] == 1
    assert metrics[LIFTER_FRIENDLY] == 1
    assert metrics[SPECIALTY] == 1
