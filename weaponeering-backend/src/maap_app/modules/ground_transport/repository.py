from __future__ import annotations

import json

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ground_transport.models import ScenarioGroundTransport


class GroundTransportRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_transport(
        self,
        transport_id: str,
        scenario_id: str,
        origin_wing_id: str,
        destination_wing_id: str,
        product_id: str | None,
        vehicle_id: str | None,
        quantity: int,
        distance_m: float,
        duration_min: float,
        route_mode: str,
        route_geometry_json: str | None,
        label: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO scenario_ground_transports (
                    id, scenario_id, origin_wing_id, destination_wing_id,
                    product_id, vehicle_id, quantity, distance_m, duration_min,
                    route_mode, route_geometry_json, label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transport_id,
                    scenario_id,
                    origin_wing_id,
                    destination_wing_id,
                    product_id,
                    vehicle_id,
                    quantity,
                    distance_m,
                    duration_min,
                    route_mode,
                    route_geometry_json,
                    label,
                ),
            )

    def list_transports(self, scenario_id: str) -> list[ScenarioGroundTransport]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, origin_wing_id, destination_wing_id,
                       product_id, vehicle_id, quantity, distance_m, duration_min,
                       route_mode, route_geometry_json, label, status, created_at, updated_at
                FROM scenario_ground_transports
                WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at DESC, label ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [ScenarioGroundTransport(**dict(row)) for row in rows]

    def get_transport(self, transport_id: str) -> ScenarioGroundTransport | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, origin_wing_id, destination_wing_id,
                       product_id, vehicle_id, quantity, distance_m, duration_min,
                       route_mode, route_geometry_json, label, status, created_at, updated_at
                FROM scenario_ground_transports
                WHERE id = ?
                """,
                (transport_id,),
            ).fetchone()
        return ScenarioGroundTransport(**dict(row)) if row else None

    def delete_transport(self, transport_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE scenario_ground_transports
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'active'
                """,
                (transport_id,),
            )
        return cursor.rowcount > 0

    def update_route_geometry(
        self,
        transport_id: str,
        distance_m: float,
        duration_min: float,
        route_mode: str,
        route_geometry_json: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE scenario_ground_transports
                SET distance_m = ?,
                    duration_min = ?,
                    route_mode = ?,
                    route_geometry_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'active'
                """,
                (
                    distance_m,
                    duration_min,
                    route_mode,
                    route_geometry_json,
                    transport_id,
                ),
            )
