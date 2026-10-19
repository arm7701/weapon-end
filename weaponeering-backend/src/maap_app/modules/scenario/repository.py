from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.scenario.models import MapNode, Scenario


class ScenarioRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_scenario(
        self,
        scenario_id: str,
        name: str,
        description: str,
        ruleset_version: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO scenarios (id, name, description, ruleset_version)
                VALUES (?, ?, ?, ?)
                """,
                (scenario_id, name, description, ruleset_version),
            )

    def get_scenario(self, scenario_id: str) -> Scenario | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, description, status, ruleset_version,
                       created_at, updated_at
                FROM scenarios
                WHERE id = ?
                """,
                (scenario_id,),
            ).fetchone()
        return Scenario(**dict(row)) if row else None

    def list_scenarios(self) -> list[Scenario]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, description, status, ruleset_version, created_at, updated_at
                FROM scenarios
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [Scenario(**dict(row)) for row in rows]

    def insert_map_node(
        self,
        node_id: str,
        scenario_id: str,
        label: str,
        node_type: str,
        map_lat: float,
        map_lng: float,
        linked_entity_type: str | None = None,
        linked_entity_id: str | None = None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO map_nodes (
                    id, scenario_id, label, node_type, map_lat, map_lng,
                    linked_entity_type, linked_entity_id, is_synthetic_location
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    node_id,
                    scenario_id,
                    label,
                    node_type,
                    map_lat,
                    map_lng,
                    linked_entity_type,
                    linked_entity_id,
                ),
            )

    def update_map_node_coords(
        self,
        node_id: str,
        map_lat: float,
        map_lng: float,
        label: str | None = None,
    ) -> None:
        with self.database.connect() as connection:
            if label is not None:
                connection.execute(
                    """
                    UPDATE map_nodes
                    SET map_lat = ?, map_lng = ?, label = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (map_lat, map_lng, label, node_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE map_nodes
                    SET map_lat = ?, map_lng = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (map_lat, map_lng, node_id),
                )

    def list_learning_objectives(self, scenario_id: str) -> list[tuple[str, str, int]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, label, priority
                FROM learning_objectives
                WHERE scenario_id = ?
                ORDER BY priority DESC, label
                """,
                (scenario_id,),
            ).fetchall()
        return [(row["id"], row["label"], row["priority"]) for row in rows]

    def list_map_nodes(self, scenario_id: str) -> list[MapNode]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, label, node_type, map_lat, map_lng, review_status
                FROM map_nodes
                WHERE scenario_id = ?
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [MapNode(**dict(row)) for row in rows]

