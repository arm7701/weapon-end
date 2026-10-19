from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


class SQLiteDatabase:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            applied = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, sql in self._load_migrations():
                if version in applied:
                    continue
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (version,),
                )

    def _load_migrations(self) -> Iterable[tuple[str, str]]:
        migrations_dir = Path(__file__).parent / "migrations"
        for path in sorted(migrations_dir.glob("*.sql")):
            yield path.stem, path.read_text(encoding="utf-8")

