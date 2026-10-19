from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase


class GuardrailRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def list_recent(self, limit: int = 100) -> list[dict]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, event_type, entity_type, entity_id, decision,
                       sanitized_summary, created_at
                FROM guardrail_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_event(
        self,
        event_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        decision: str,
        sanitized_summary: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO guardrail_events (
                    id, event_type, entity_type, entity_id, decision, sanitized_summary
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event_type,
                    entity_type,
                    entity_id,
                    decision,
                    sanitized_summary,
                ),
            )

