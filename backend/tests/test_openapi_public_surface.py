import json
from pathlib import Path


def test_openapi_public_surface_is_clean(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"].keys()

    for path in paths:
        assert not path.startswith("/internal")
        assert not path.startswith("/debug")
        assert not path.startswith("/metrics")


def test_checked_in_openapi_snapshot_matches_live_app(client):
    live_spec = client.get("/openapi.json").json()
    snapshot_path = Path(__file__).resolve().parents[1] / "openapi.json"
    checked_in_spec = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert checked_in_spec == live_spec

