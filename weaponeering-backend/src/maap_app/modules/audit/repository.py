from __future__ import annotations

import json
from typing import Any

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.models import AuditEvent


class AuditRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert(
        self,
        event_id: str,
        actor: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any],
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    id, actor, event_type, entity_type, entity_id, details_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    actor,
                    event_type,
                    entity_type,
                    entity_id,
                    json.dumps(details, ensure_ascii=True),
                ),
            )

    def list_for_scenario(self, scenario_id: str, limit: int = 200) -> list[AuditEvent]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, actor, event_type, entity_type, entity_id,
                       details_json, created_at
                FROM audit_events
                WHERE details_json LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f'%{scenario_id}%', limit),
            ).fetchall()
        return [AuditEvent(**dict(row)) for row in rows]

    def list_recent(self, limit: int = 50) -> list[AuditEvent]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, actor, event_type, entity_type, entity_id, details_json, created_at
                FROM audit_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [AuditEvent(**dict(row)) for row in rows]

