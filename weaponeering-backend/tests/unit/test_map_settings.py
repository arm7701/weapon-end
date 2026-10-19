from pathlib import Path

from maap_app.config.map_settings import MapSettings


def test_map_settings_persist_stadia_api_key(tmp_path: Path) -> None:
    settings = MapSettings(stadia_api_key="stadia-test-key")
    settings.save(tmp_path)

    loaded = MapSettings.load(tmp_path)

    assert loaded.stadia_api_key == "stadia-test-key"
