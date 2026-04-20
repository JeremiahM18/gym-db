from api.settings import BACKEND_ROOT, APISettings


def test_api_settings_default_paths_resolve_from_backend_root():
    settings = APISettings()

    assert settings.registry_path == BACKEND_ROOT / "data/registry.json"
    assert settings.dataset_root == BACKEND_ROOT / "data"
    assert settings.registry_path.is_absolute()
    assert settings.dataset_root.is_absolute()
