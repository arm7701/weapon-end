from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.wing_data.models import (
    AirWing,
    WingAircraft,
    WingDepot,
    WingDepotInventory,
    WingDepotInventoryDetail,
    WingDepotTransferDetail,
    WingFlyingUnit,
    WingLogisticsVehicle,
    WingPilot,
    WingProduct,
)


class WingDataRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    # --- Air Wing ---
    def insert_wing(
        self, wing_id: str, scenario_id: str, wing_name: str,
        map_lat: float | None, map_lng: float | None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO air_wings (id, scenario_id, wing_name, map_lat, map_lng)
                VALUES (?, ?, ?, ?, ?)
                """,
                (wing_id, scenario_id, wing_name, map_lat, map_lng),
            )

    def list_wings(self, scenario_id: str) -> list[AirWing]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, wing_name, map_lat, map_lng, status, created_at
                FROM air_wings WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [AirWing(**dict(r)) for r in rows]

    def get_wing(self, wing_id: str) -> AirWing | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, wing_name, map_lat, map_lng, status, created_at
                FROM air_wings WHERE id = ?
                """,
                (wing_id,),
            ).fetchone()
        return AirWing(**dict(row)) if row else None

    def update_wing(
        self, wing_id: str, wing_name: str, map_lat: float | None, map_lng: float | None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE air_wings
                SET wing_name = ?, map_lat = ?, map_lng = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (wing_name, map_lat, map_lng, wing_id),
            )

    def archive_wing(self, wing_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE air_wings SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (wing_id,),
            )

    # --- Flying unit ---
    def insert_flying_unit(
        self,
        flying_unit_id: str,
        scenario_id: str,
        wing_id: str,
        unit_name: str,
        map_lat: float | None = None,
        map_lng: float | None = None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_flying_units (
                    id, scenario_id, wing_id, unit_name, map_lat, map_lng
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (flying_unit_id, scenario_id, wing_id, unit_name, map_lat, map_lng),
            )

    def list_flying_units(self, scenario_id: str) -> list[WingFlyingUnit]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, wing_id, unit_name, status,
                       map_lat, map_lng, created_at
                FROM wing_flying_units
                WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingFlyingUnit(**dict(r)) for r in rows]

    def get_flying_unit(self, flying_unit_id: str) -> WingFlyingUnit | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, wing_id, unit_name, status,
                       map_lat, map_lng, created_at
                FROM wing_flying_units WHERE id = ?
                """,
                (flying_unit_id,),
            ).fetchone()
        return WingFlyingUnit(**dict(row)) if row else None

    def update_flying_unit(
        self,
        flying_unit_id: str,
        wing_id: str,
        unit_name: str,
        map_lat: float | None = None,
        map_lng: float | None = None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_flying_units
                SET wing_id = ?, unit_name = ?, map_lat = ?, map_lng = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (wing_id, unit_name, map_lat, map_lng, flying_unit_id),
            )

    def archive_flying_unit(self, flying_unit_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_flying_units
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (flying_unit_id,),
            )

    # --- Aircraft ---
    def insert_aircraft(
        self, aircraft_id: str, scenario_id: str, wing_id: str,
        aircraft_type: str, flying_unit_id: str | None, mission_ready: str,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_aircraft (
                    id, scenario_id, wing_id, aircraft_type, flying_unit_id, mission_ready
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    aircraft_id,
                    scenario_id,
                    wing_id,
                    aircraft_type,
                    flying_unit_id,
                    mission_ready,
                ),
            )

    def list_aircraft(self, scenario_id: str) -> list[WingAircraft]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, wing_id, aircraft_type, flying_unit_id,
                       mission_ready, status, created_at
                FROM wing_aircraft WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingAircraft(**dict(r)) for r in rows]

    def get_aircraft(self, aircraft_id: str) -> WingAircraft | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, wing_id, aircraft_type, flying_unit_id,
                       mission_ready, status, created_at
                FROM wing_aircraft WHERE id = ?
                """,
                (aircraft_id,),
            ).fetchone()
        return WingAircraft(**dict(row)) if row else None

    def update_aircraft(
        self, aircraft_id: str, wing_id: str, aircraft_type: str,
        flying_unit_id: str | None, mission_ready: str,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_aircraft
                SET wing_id = ?, aircraft_type = ?, flying_unit_id = ?,
                    mission_ready = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (wing_id, aircraft_type, flying_unit_id, mission_ready, aircraft_id),
            )

    def archive_aircraft(self, aircraft_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE wing_aircraft SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (aircraft_id,),
            )

    # --- Pilots ---
    def insert_pilot(
        self, pilot_id: str, scenario_id: str, wing_id: str | None,
        flying_unit_id: str | None, pilot_name: str, callsign: str, cep_value: float,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_pilots (
                    id, scenario_id, wing_id, flying_unit_id,
                    pilot_name, callsign, cep_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pilot_id,
                    scenario_id,
                    wing_id,
                    flying_unit_id,
                    pilot_name,
                    callsign,
                    cep_value,
                ),
            )

    def list_pilots(self, scenario_id: str) -> list[WingPilot]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, wing_id, flying_unit_id, pilot_name, callsign,
                       cep_value, status, created_at
                FROM wing_pilots WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingPilot(**dict(r)) for r in rows]

    def get_pilot(self, pilot_id: str) -> WingPilot | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, wing_id, flying_unit_id, pilot_name, callsign,
                       cep_value, status, created_at
                FROM wing_pilots WHERE id = ?
                """,
                (pilot_id,),
            ).fetchone()
        return WingPilot(**dict(row)) if row else None

    def update_pilot(
        self, pilot_id: str, wing_id: str | None, flying_unit_id: str | None,
        pilot_name: str, callsign: str, cep_value: float,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_pilots
                SET wing_id = ?, flying_unit_id = ?, pilot_name = ?, callsign = ?,
                    cep_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    wing_id,
                    flying_unit_id,
                    pilot_name,
                    callsign,
                    cep_value,
                    pilot_id,
                ),
            )

    def archive_pilot(self, pilot_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE wing_pilots SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (pilot_id,),
            )

    # --- Depots ---
    def insert_depot(
        self, depot_id: str, scenario_id: str, wing_id: str, depot_name: str,
        map_lat: float | None, map_lng: float | None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_depots (id, scenario_id, wing_id, depot_name, map_lat, map_lng)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (depot_id, scenario_id, wing_id, depot_name, map_lat, map_lng),
            )

    def list_depots(self, scenario_id: str) -> list[WingDepot]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, wing_id, depot_name, map_lat, map_lng, status, created_at
                FROM wing_depots WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingDepot(**dict(r)) for r in rows]

    def get_depot(self, depot_id: str) -> WingDepot | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, wing_id, depot_name, map_lat, map_lng, status, created_at
                FROM wing_depots WHERE id = ?
                """,
                (depot_id,),
            ).fetchone()
        return WingDepot(**dict(row)) if row else None

    def update_depot(
        self, depot_id: str, wing_id: str, depot_name: str,
        map_lat: float | None, map_lng: float | None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_depots
                SET wing_id = ?, depot_name = ?, map_lat = ?, map_lng = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (wing_id, depot_name, map_lat, map_lng, depot_id),
            )

    def archive_depot(self, depot_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE wing_depots SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (depot_id,),
            )

    # --- Logistics vehicles ---
    def insert_vehicle(
        self, vehicle_id: str, scenario_id: str, wing_id: str,
        vehicle_name: str, fuel_consumption_rate: float, mission_ready: str,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_logistics_vehicles (
                    id, scenario_id, wing_id, vehicle_name,
                    fuel_consumption_rate, mission_ready
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (vehicle_id, scenario_id, wing_id, vehicle_name, fuel_consumption_rate, mission_ready),
            )

    def list_vehicles(self, scenario_id: str) -> list[WingLogisticsVehicle]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, wing_id, vehicle_name,
                       fuel_consumption_rate, mission_ready, status, created_at
                FROM wing_logistics_vehicles
                WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingLogisticsVehicle(**dict(r)) for r in rows]

    def get_vehicle(self, vehicle_id: str) -> WingLogisticsVehicle | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, wing_id, vehicle_name,
                       fuel_consumption_rate, mission_ready, status, created_at
                FROM wing_logistics_vehicles WHERE id = ?
                """,
                (vehicle_id,),
            ).fetchone()
        return WingLogisticsVehicle(**dict(row)) if row else None

    def update_vehicle(
        self, vehicle_id: str, wing_id: str, vehicle_name: str,
        fuel_consumption_rate: float, mission_ready: str,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_logistics_vehicles
                SET wing_id = ?, vehicle_name = ?, fuel_consumption_rate = ?,
                    mission_ready = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (wing_id, vehicle_name, fuel_consumption_rate, mission_ready, vehicle_id),
            )

    def archive_vehicle(self, vehicle_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_logistics_vehicles
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """,
                (vehicle_id,),
            )

    # --- Products ---
    def insert_product(
        self,
        product_id: str,
        scenario_id: str,
        product_name: str,
        weight_pounds: float,
        unit_cost: float,
        description: str = "",
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_products (
                    id, scenario_id, product_name, weight_pounds, unit_cost, description
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (product_id, scenario_id, product_name, weight_pounds, unit_cost, description),
            )

    def list_products(self, scenario_id: str) -> list[WingProduct]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, product_name, weight_pounds,
                       unit_cost, status, created_at, description
                FROM wing_products WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingProduct(**dict(r)) for r in rows]

    def get_product(self, product_id: str) -> WingProduct | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, product_name, weight_pounds,
                       unit_cost, status, created_at, description
                FROM wing_products WHERE id = ?
                """,
                (product_id,),
            ).fetchone()
        return WingProduct(**dict(row)) if row else None

    def update_product(
        self,
        product_id: str,
        product_name: str,
        weight_pounds: float,
        unit_cost: float,
        description: str = "",
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_products
                SET product_name = ?, weight_pounds = ?, unit_cost = ?,
                    description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (product_name, weight_pounds, unit_cost, description, product_id),
            )

    def archive_product(self, product_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_products
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """,
                (product_id,),
            )

    # --- Depot inventory ---
    def get_inventory_row(
        self, depot_id: str, product_id: str,
    ) -> WingDepotInventory | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, scenario_id, depot_id, product_id, quantity, status, created_at
                FROM wing_depot_inventory
                WHERE depot_id = ? AND product_id = ? AND status = 'active'
                """,
                (depot_id, product_id),
            ).fetchone()
        return WingDepotInventory(**dict(row)) if row else None

    def upsert_inventory(
        self, inventory_id: str, scenario_id: str,
        depot_id: str, product_id: str, quantity: int,
    ) -> None:
        with self.database.connect() as conn:
            existing = conn.execute(
                """
                SELECT id FROM wing_depot_inventory
                WHERE depot_id = ? AND product_id = ? AND status = 'active'
                """,
                (depot_id, product_id),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE wing_depot_inventory
                    SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (quantity, existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO wing_depot_inventory (
                        id, scenario_id, depot_id, product_id, quantity
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (inventory_id, scenario_id, depot_id, product_id, quantity),
                )

    def adjust_inventory_quantity(
        self, depot_id: str, product_id: str, delta: int,
    ) -> int:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, quantity FROM wing_depot_inventory
                WHERE depot_id = ? AND product_id = ? AND status = 'active'
                """,
                (depot_id, product_id),
            ).fetchone()
            if not row:
                return 0
            new_qty = row["quantity"] + delta
            if new_qty <= 0:
                conn.execute(
                    """
                    UPDATE wing_depot_inventory
                    SET status = 'archived', quantity = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (row["id"],),
                )
                return 0
            conn.execute(
                """
                UPDATE wing_depot_inventory
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_qty, row["id"]),
            )
            return new_qty

    def list_inventory(self, scenario_id: str) -> list[WingDepotInventoryDetail]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT i.id, i.scenario_id, i.depot_id, d.depot_name,
                       i.product_id, p.product_name, i.quantity
                FROM wing_depot_inventory i
                JOIN wing_depots d ON d.id = i.depot_id
                JOIN wing_products p ON p.id = i.product_id
                WHERE i.scenario_id = ? AND i.status = 'active' AND i.quantity > 0
                ORDER BY d.depot_name ASC, p.product_name ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingDepotInventoryDetail(**dict(r)) for r in rows]

    def archive_inventory(self, inventory_id: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE wing_depot_inventory
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (inventory_id,),
            )

    def insert_transfer(
        self, transfer_id: str, scenario_id: str, product_id: str,
        from_depot_id: str, to_depot_id: str, quantity: int,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO wing_depot_transfers (
                    id, scenario_id, product_id, from_depot_id, to_depot_id, quantity
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (transfer_id, scenario_id, product_id, from_depot_id, to_depot_id, quantity),
            )

    def list_transfers(self, scenario_id: str) -> list[WingDepotTransferDetail]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT t.id, t.scenario_id, t.from_depot_id, fd.depot_name AS from_depot_name,
                       t.to_depot_id, td.depot_name AS to_depot_name,
                       t.product_id, p.product_name, t.quantity, t.created_at
                FROM wing_depot_transfers t
                JOIN wing_depots fd ON fd.id = t.from_depot_id
                JOIN wing_depots td ON td.id = t.to_depot_id
                JOIN wing_products p ON p.id = t.product_id
                WHERE t.scenario_id = ?
                ORDER BY t.created_at DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [WingDepotTransferDetail(**dict(r)) for r in rows]
