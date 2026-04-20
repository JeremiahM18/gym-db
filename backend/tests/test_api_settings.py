from api.settings import BACKEND_ROOT, APISettings
from gymdb.settings import BACKEND_ROOT as GYMDB_BACKEND_ROOT


def test_api_settings_default_paths_resolve_from_backend_root():
    settings = APISettings()

    assert settings.registry_path == BACKEND_ROOT / "data/registry.json"
    assert settings.dataset_root == BACKEND_ROOT / "data"
    assert settings.registry_path.is_absolute()
    assert settings.dataset_root.is_absolute()


def test_shared_settings_env_files_resolve_from_backend_root():
    env_files = APISettings.model_config["env_file"]

    assert env_files == (
        str(GYMDB_BACKEND_ROOT / ".env"),
        str(GYMDB_BACKEND_ROOT / ".env.local"),
    )
