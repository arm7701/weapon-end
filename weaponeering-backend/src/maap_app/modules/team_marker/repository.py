from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.team_marker.models import ScenarioTeamMarker


class TeamMarkerRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_marker(
        self,
        marker_id: str,
        scenario_id: str,
        side: str,
        unit_type: str,
        label: str,
        map_lat: float,
        map_lng: float,
        radius_m: float | None = None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO scenario_team_markers (
                    id, scenario_id, side, unit_type, label, map_lat, map_lng, radius_m
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    marker_id,
                    scenario_id,
                    side,
                    unit_type,
                    label,
                    map_lat,
                    map_lng,
                    radius_m,
                ),
            )

    def list_markers(self, scenario_id: str) -> list[ScenarioTeamMarker]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, side, unit_type, label, map_lat, map_lng,
                       radius_m, created_at, updated_at
                FROM scenario_team_markers
                WHERE scenario_id = ?
                ORDER BY created_at ASC, label ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [ScenarioTeamMarker(**dict(row)) for row in rows]

    def delete_marker(self, marker_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM scenario_team_markers WHERE id = ?",
                (marker_id,),
            )
        return cursor.rowcount > 0
