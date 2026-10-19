from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_DIR_NAME = "maap_wargame_simulation"


@dataclass(frozen=True)
class AppSettings:
    data_dir: Path
    database_path: Path
    ruleset_version: str = "phase-1-baseline"
    offline_mode: bool = True

    @classmethod
    def load(cls) -> "AppSettings":
        data_dir = Path.home() / ".local" / "share" / APP_DIR_NAME
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            data_dir=data_dir,
            database_path=data_dir / "maap_wargame.sqlite3",
        )

