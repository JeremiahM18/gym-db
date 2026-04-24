import pytest
from pydantic import ValidationError

from api.settings import BACKEND_ROOT, APISettings
from gymdb.settings import BACKEND_ROOT as GYMDB_BACKEND_ROOT


def test_api_settings_default_paths_resolve_from_backend_root(monkeypatch):
    monkeypatch.delenv("OPS_STATE_PATH", raising=False)
    monkeypatch.delenv("LIVE_SEARCH_SESSION_ROOT", raising=False)
    monkeypatch.delenv("LIVE_SEARCH_CACHE_ROOT", raising=False)
    settings = APISettings()

    assert settings.registry_path == BACKEND_ROOT / "data/registry.json"
    assert settings.dataset_root == BACKEND_ROOT / "data"
    assert settings.ops_state_path == BACKEND_ROOT / "data/ops_state.sqlite3"
    assert settings.registry_path.is_absolute()
    assert settings.dataset_root.is_absolute()
    assert settings.ops_state_path.is_absolute()


def test_shared_settings_env_files_resolve_from_backend_root():
    env_files = APISettings.model_config["env_file"]

    assert env_files == (
        str(GYMDB_BACKEND_ROOT / ".env"),
        str(GYMDB_BACKEND_ROOT / ".env.local"),
    )


def test_staging_rejects_dev_auth_bypass():
    with pytest.raises(ValidationError):
        APISettings(
            app_env="staging",
            enable_dev_auth_bypass=True,
            cognito_user_pool_id="pool",
            cognito_app_client_id="client",
            cognito_issuer="https://issuer.example.com",
            cors_allowed_origins=["https://app.example.com"],
        )


def test_production_rejects_default_cognito_placeholders():
    with pytest.raises(ValidationError):
        APISettings(
            app_env="production",
            cognito_user_pool_id="dev",
            cognito_app_client_id="dev",
            cognito_issuer="https://example.com",
            cors_allowed_origins=["https://app.example.com"],
        )


def test_production_rejects_localhost_cors():
    with pytest.raises(ValidationError):
        APISettings(
            app_env="production",
            cognito_user_pool_id="pool",
            cognito_app_client_id="client",
            cognito_issuer="https://issuer.example.com",
            cors_allowed_origins=["http://localhost:5173"],
        )
