from gymdb.observe.metrics import (
    record_http_exception,
    record_http_request,
    snapshot_http_metrics,
)


def test_http_metrics_snapshot_starts_with_fixed_zero_keys():
    snap = snapshot_http_metrics()
    assert snap == {
        "requests_total": 0,
        "requests_2xx": 0,
        "requests_4xx": 0,
        "requests_5xx": 0,
        "request_exceptions": 0,
        "latency_le_100ms": 0,
        "latency_le_300ms": 0,
        "latency_le_1000ms": 0,
        "latency_gt_1000ms": 0,
    }


def test_http_metrics_record_status_and_latency_buckets():
    record_http_request(status_code=204, elapsed_ms=45)
    record_http_request(status_code=404, elapsed_ms=240)
    record_http_request(status_code=503, elapsed_ms=900)
    record_http_exception()

    snap = snapshot_http_metrics()
    assert snap["requests_total"] == 3
    assert snap["requests_2xx"] == 1
    assert snap["requests_4xx"] == 1
    assert snap["requests_5xx"] == 1
    assert snap["request_exceptions"] == 1
    assert snap["latency_le_100ms"] == 1
    assert snap["latency_le_300ms"] == 1
    assert snap["latency_le_1000ms"] == 1
    assert snap["latency_gt_1000ms"] == 0


def test_request_middleware_records_http_metrics(client):
    ok = client.get("/healthz")
    missing = client.get("/does-not-exist")

    assert ok.status_code == 200
    assert missing.status_code == 404

    snap = snapshot_http_metrics()
    assert snap["requests_total"] == 2
    assert snap["requests_2xx"] == 1
    assert snap["requests_4xx"] == 1
