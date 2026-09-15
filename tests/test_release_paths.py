from app.utils.paths import app_data_path, resource_path


def test_resource_path_resolves_bundled_development_files() -> None:
    assert resource_path("theme", "dark.qss").is_file()
    assert resource_path("app", "config", "crunch.yaml").is_file()


def test_app_data_path_uses_configured_writable_location(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WORKOUT_TRACKER_DATA_DIR", str(tmp_path))
    path = app_data_path("data", "workouts.json")
    assert path == tmp_path / "data" / "workouts.json"
    assert path.parent.is_dir()
