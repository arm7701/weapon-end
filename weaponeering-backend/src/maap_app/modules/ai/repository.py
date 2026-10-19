from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.models import AiInteraction


class AiRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_interaction(
        self,
        interaction_id: str,
        scenario_id: str,
        entity_type: str,
        entity_id: str,
        request_type: str,
        sanitized_prompt: str,
        sanitized_output: str,
        classifier_result: str,
        validator_result: str,
        review_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_interactions (
                    id, scenario_id, entity_type, entity_id,
                    request_type, sanitized_prompt, sanitized_output,
                    classifier_result, validator_result, review_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interaction_id,
                    scenario_id,
                    entity_type,
                    entity_id,
                    request_type,
                    sanitized_prompt,
                    sanitized_output,
                    classifier_result,
                    validator_result,
                    review_status,
                ),
            )

    def update_review_status(self, interaction_id: str, review_status: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE ai_interactions
                SET review_status = ?
                WHERE id = ?
                """,
                (review_status, interaction_id),
            )

    def get_interaction(self, interaction_id: str) -> AiInteraction | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, entity_type, entity_id, request_type,
                       sanitized_prompt, sanitized_output, classifier_result,
                       validator_result, review_status, created_at
                FROM ai_interactions
                WHERE id = ?
                """,
                (interaction_id,),
            ).fetchone()
        return AiInteraction(**dict(row)) if row else None

    def list_interactions(
        self,
        scenario_id: str,
        *,
        review_status: str | None = None,
    ) -> list[AiInteraction]:
        query = """
            SELECT id, scenario_id, entity_type, entity_id, request_type,
                   sanitized_prompt, sanitized_output, classifier_result,
                   validator_result, review_status, created_at
            FROM ai_interactions
            WHERE scenario_id = ?
        """
        params: list[object] = [scenario_id]
        if review_status:
            query += " AND review_status = ?"
            params.append(review_status)
        query += " ORDER BY created_at DESC"
        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [AiInteraction(**dict(row)) for row in rows]

    def delete_by_scenario(self, scenario_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM ai_interactions WHERE scenario_id = ?",
                (scenario_id,),
            )

    def delete_by_entity(self, scenario_id: str, entity_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM ai_interactions WHERE scenario_id = ? AND entity_id = ?",
                (scenario_id, entity_id),
            )

    def list_all_interactions_for_scenario(self, scenario_id: str) -> list[AiInteraction]:
        """Return every interaction for a scenario across all threads, oldest first."""
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, entity_type, entity_id, request_type,
                       sanitized_prompt, sanitized_output, classifier_result,
                       validator_result, review_status, created_at
                FROM ai_interactions
                WHERE scenario_id = ?
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [AiInteraction(**dict(row)) for row in rows]

    def list_pending_review(self, scenario_id: str) -> list[AiInteraction]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, entity_type, entity_id, request_type,
                       sanitized_prompt, sanitized_output, classifier_result,
                       validator_result, review_status, created_at
                FROM ai_interactions
                WHERE scenario_id = ?
                  AND review_status IN ('requires_review', 'blocked_by_guardrail')
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [AiInteraction(**dict(row)) for row in rows]
