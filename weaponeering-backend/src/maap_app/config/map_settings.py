from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from maap_app.config.settings import APP_DIR_NAME


@dataclass
class MapSettings:
    stadia_api_key: str = ""

    terrain_enabled: bool = True

    @classmethod
    def load(cls, data_dir: Path | None = None) -> MapSettings:
        base = data_dir or Path.home() / ".local" / "share" / APP_DIR_NAME
        path = base / "map_settings.json"
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        return cls(
            stadia_api_key=str(payload.get("stadia_api_key", "")),
            terrain_enabled=bool(payload.get("terrain_enabled", True)),
        )

    def save(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path.home() / ".local" / "share" / APP_DIR_NAME
        base.mkdir(parents=True, exist_ok=True)
        path = base / "map_settings.json"
        path.write_text(
            json.dumps(
                {
                    "stadia_api_key": self.stadia_api_key,
                    "terrain_enabled": self.terrain_enabled,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
