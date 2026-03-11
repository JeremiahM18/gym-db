from gymdb.gyms.queries import list_gyms


class StubStore:
    default_region = "test"

    def __init__(self, gyms: list[dict]):
        self._gyms = gyms

    def filter(self, **kwargs):
        return list(self._gyms)

    def get_by_id(self, region: str, gym_id: str):
        for gym in self._gyms:
            if gym["id"] == gym_id:
                return gym
        return None


def test_list_gyms_filters_by_tier_and_lifter_friendly():
    store = StubStore(
        [
            {
                "id": "premium-a",
                "lat": 36.16,
                "lon": -86.78,
                "inferred": {
                    "tier": {"value": "premium"},
                    "lifter_friendly": {"value": True},
                },
            },
            {
                "id": "basic-b",
                "lat": 36.17,
                "lon": -86.79,
                "inferred": {
                    "tier": {"value": "basic"},
                    "lifter_friendly": {"value": False},
                },
            },
        ]
    )

    results = list_gyms(
        store=store,
        region="test",
        tier="premium",
        lifter_friendly=True,
    )

    assert [gym["id"] for gym in results] == ["premium-a"]


def test_list_gyms_radius_filter_keeps_only_nearby_results():
    store = StubStore(
        [
            {
                "id": "nearby",
                "lat": 36.1627,
                "lon": -86.7816,
                "inferred": {},
            },
            {
                "id": "far-away",
                "lat": 36.2627,
                "lon": -86.7816,
                "inferred": {},
            },
        ]
    )

    results = list_gyms(
        store=store,
        region="test",
        lat=36.1627,
        lon=-86.7816,
        radius_m=500,
    )

    assert [gym["id"] for gym in results] == ["nearby"]


