from api.auth import cognito
from api.settings import APISettings


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_get_jwks_uses_ttl_cache(monkeypatch):
    calls = []

    def fake_get(url: str, timeout: int):
        calls.append((url, timeout))
        return _FakeResponse({"keys": [{"kid": "one"}]})

    cognito.clear_jwks_cache()
    monkeypatch.setattr("api.auth.cognito.requests.get", fake_get)

    first = cognito.get_jwks(
        "https://issuer.example.com/.well-known/jwks.json",
        ttl_seconds=300,
    )
    second = cognito.get_jwks(
        "https://issuer.example.com/.well-known/jwks.json",
        ttl_seconds=300,
    )

    assert first == second
    assert len(calls) == 1


def test_verify_jwt_refreshes_jwks_when_kid_is_missing(monkeypatch):
    requests_calls = []
    jwks_payloads = [
        {"keys": [{"kid": "old-key", "kty": "RSA"}]},
        {"keys": [{"kid": "new-key", "kty": "RSA"}]},
    ]

    def fake_get(url: str, timeout: int):
        requests_calls.append((url, timeout))
        return _FakeResponse(jwks_payloads.pop(0))

    cognito.clear_jwks_cache()
    monkeypatch.setattr("api.auth.cognito.requests.get", fake_get)
    monkeypatch.setattr(
        "api.auth.cognito.jwt.get_unverified_header",
        lambda token: {"kid": "new-key"},
    )
    monkeypatch.setattr(
        "api.auth.cognito.jwt.decode",
        lambda token, key, algorithms, audience, issuer: {
            "sub": "user-1",
            "exp": 4_102_444_800,
        },
    )

    settings = APISettings(
        cognito_app_client_id="client-id",
        cognito_issuer="https://issuer.example.com",
        cognito_jwks_cache_ttl_seconds=300,
    )

    claims = cognito.verify_jwt("test-token", settings)

    assert claims["sub"] == "user-1"
    assert len(requests_calls) == 2


def test_verify_jwt_raises_when_rotated_key_is_still_missing(monkeypatch):
    def fake_get(url: str, timeout: int):
        return _FakeResponse({"keys": [{"kid": "old-key", "kty": "RSA"}]})

    cognito.clear_jwks_cache()
    monkeypatch.setattr("api.auth.cognito.requests.get", fake_get)
    monkeypatch.setattr(
        "api.auth.cognito.jwt.get_unverified_header",
        lambda token: {"kid": "missing-key"},
    )

    settings = APISettings(
        cognito_app_client_id="client-id",
        cognito_issuer="https://issuer.example.com",
        cognito_jwks_cache_ttl_seconds=300,
    )

    try:
        cognito.verify_jwt("test-token", settings)
    except ValueError as exc:
        assert str(exc) == "Invalid JWT"
    else:
        raise AssertionError("verify_jwt should reject an unknown signing key")
