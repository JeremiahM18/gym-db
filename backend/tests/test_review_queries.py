from gymdb.gyms.review import list_review_gyms, summarize_review_gyms


def test_list_review_gyms_filters_on_match_status():
    class FakeStore:
        def filter(self, **kwargs):
            return [
                {
                    "name": "Matched Gym",
                    "confidence_score": 0.9,
                    "source_provenance": {"match_status": "matched"},
                    "inference_meta": {"contradictions": {}},
                },
                {
                    "name": "Mismatch Gym",
                    "confidence_score": 0.4,
                    "source_provenance": {"match_status": "name_mismatch"},
                    "inference_meta": {"contradictions": {"specialty": ["x"]}},
                },
            ]

    gyms = list_review_gyms(
        store=FakeStore(),
        region="test",
        status="name_mismatch",
        limit=10,
        offset=0,
    )

    assert len(gyms) == 1
    assert gyms[0]["name"] == "Mismatch Gym"


def test_summarize_review_gyms_counts_review_signals():
    class FakeStore:
        def filter(self, **kwargs):
            return [
                {
                    "name": "Matched Gym",
                    "confidence_score": 0.9,
                    "source_provenance": {"match_status": "matched"},
                    "inference_meta": {"contradictions": {}},
                },
                {
                    "name": "Mismatch Gym",
                    "confidence_score": 0.4,
                    "source_provenance": {"match_status": "name_mismatch"},
                    "inference_meta": {"contradictions": {"specialty": ["x"]}},
                },
                {
                    "name": "Unknown Gym",
                    "confidence_score": 0.2,
                    "source_provenance": {"match_status": "unconfirmed"},
                    "inference_meta": {"contradictions": {}},
                },
            ]

    summary = summarize_review_gyms(store=FakeStore(), region="test")

    assert summary["matched"] == 1
    assert summary["name_mismatch"] == 1
    assert summary["unconfirmed"] == 1
    assert summary["contradictions"] == 1
    assert summary["low_confidence"] == 2
