from gymdb.gyms.queries import list_gyms


class StubStore:
    default_region = "test"

    def __init__(self, gyms: list[dict]):
        self._gyms = gyms

    def filter(self, **kwargs):
        return list(self._gyms)

    def nearby(self, **kwargs):
        lat = kwargs["lat"]
        radius_m = kwargs["radius_m"]
        if radius_m < 1_000:
            return [gym for gym in self._gyms if gym["lat"] == lat]
        return list(self._gyms)

    def get_by_id(self, region: str, gym_id: str):
        for gym in self._gyms:
            if gym["id"] == gym_id:
                return gym
        return None


def test_list_gyms_filters_by_tier_lifter_and_specialty():
    store = StubStore(
        [
            {
                "id": "premium-a",
                "lat": 36.16,
                "lon": -86.78,
                "inferred": {
                    "tier": {"value": "premium"},
                    "lifter_friendly": {"value": True},
                    "specialty": {"value": "powerlifting"},
                },
            },
            {
                "id": "basic-b",
                "lat": 36.17,
                "lon": -86.79,
                "inferred": {
                    "tier": {"value": "basic"},
                    "lifter_friendly": {"value": False},
                    "specialty": {"value": "general_fitness"},
                },
            },
        ]
    )

    results = list_gyms(
        store=store,
        region="test",
        tier="premium",
        specialty="powerlifting",
        lifter_friendly=True,
    )

    assert [gym["id"] for gym in results] == ["premium-a"]


def test_list_gyms_radius_filter_uses_store_nearby_candidates():
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
