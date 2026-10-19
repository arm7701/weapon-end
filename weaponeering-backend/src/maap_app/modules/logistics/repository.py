from __future__ import annotations

from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.logistics.models import (
    Depot,
    DepotInventoryItem,
    Organization,
    PlanScore,
    PlatformType,
    ResourceToken,
    RouteSegment,
    SimulatedPlatform,
    TransportAsset,
)


class LogisticsRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def insert_organization(
        self,
        org_id: str,
        scenario_id: str,
        name: str,
        organization_type: str,
        location_label: str,
        map_lat: float | None,
        map_lng: float | None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO organizations (
                    id, scenario_id, name, organization_type,
                    location_label, map_lat, map_lng
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (org_id, scenario_id, name, organization_type, location_label, map_lat, map_lng),
            )

    def list_organizations(self, scenario_id: str) -> list[Organization]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, name, organization_type, map_lat, map_lng,
                       location_label, is_synthetic_location, readiness_summary,
                       review_status, status, created_at
                FROM organizations
                WHERE scenario_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (scenario_id,),
            ).fetchall()
        return [Organization(**dict(row)) for row in rows]

    def update_organization(
        self,
        org_id: str,
        name: str,
        organization_type: str,
        location_label: str,
        map_lat: float | None,
        map_lng: float | None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE organizations
                SET name = ?, organization_type = ?, location_label = ?,
                    map_lat = ?, map_lng = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, organization_type, location_label, map_lat, map_lng, org_id),
            )

    def archive_organization(self, org_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE organizations
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (org_id,),
            )

    def get_organization(self, org_id: str) -> Organization | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, name, organization_type, map_lat, map_lng,
                       location_label, is_synthetic_location, readiness_summary,
                       review_status, status, created_at
                FROM organizations WHERE id = ?
                """,
                (org_id,),
            ).fetchone()
        return Organization(**dict(row)) if row else None

    def insert_platform_type(
        self,
        type_id: str,
        scenario_id: str,
        label: str,
        capability_band: str,
        resource_cost_score: int,
        support_need_score: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_types (
                    id, scenario_id, label, capability_band,
                    resource_cost_score, support_need_score
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (type_id, scenario_id, label, capability_band, resource_cost_score, support_need_score),
            )

    def list_platform_types(self, scenario_id: str) -> list[PlatformType]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, label, capability_band,
                       resource_cost_score, support_need_score, status
                FROM platform_types
                WHERE scenario_id = ? AND status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [PlatformType(**dict(row)) for row in rows]

    def insert_simulated_platform(
        self,
        platform_id: str,
        scenario_id: str,
        label: str,
        organization_id: str | None,
        platform_type_id: str | None,
        capability_band: str,
        availability_score: int,
        readiness_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO simulated_platforms (
                    id, scenario_id, organization_id, platform_type_id,
                    label, capability_band, availability_score, readiness_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    platform_id,
                    scenario_id,
                    organization_id,
                    platform_type_id,
                    label,
                    capability_band,
                    availability_score,
                    readiness_status,
                ),
            )

    def get_simulated_platform(self, platform_id: str) -> SimulatedPlatform | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, organization_id, platform_type_id, label,
                       capability_band, availability_score, readiness_status,
                       readiness_note, status
                FROM simulated_platforms WHERE id = ?
                """,
                (platform_id,),
            ).fetchone()
        return SimulatedPlatform(**dict(row)) if row else None

    def update_simulated_platform(
        self,
        platform_id: str,
        label: str,
        organization_id: str | None,
        capability_band: str,
        availability_score: int,
        readiness_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE simulated_platforms
                SET label = ?, organization_id = ?, capability_band = ?,
                    availability_score = ?, readiness_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    label,
                    organization_id,
                    capability_band,
                    availability_score,
                    readiness_status,
                    platform_id,
                ),
            )

    def archive_simulated_platform(self, platform_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE simulated_platforms
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (platform_id,),
            )

    def list_simulated_platforms(self, scenario_id: str) -> list[SimulatedPlatform]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, organization_id, platform_type_id, label,
                       capability_band, availability_score, readiness_status,
                       readiness_note, status
                FROM simulated_platforms
                WHERE scenario_id = ? AND status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [SimulatedPlatform(**dict(row)) for row in rows]

    def update_platform_readiness(
        self,
        platform_id: str,
        readiness_status: str,
        readiness_note: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE simulated_platforms
                SET readiness_status = ?, readiness_note = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (readiness_status, readiness_note, platform_id),
            )

    def insert_readiness_event(
        self,
        event_id: str,
        platform_id: str,
        status: str,
        readiness_score: int,
        reason: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_readiness_events (
                    id, simulated_platform_id, status, readiness_score, reason
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, platform_id, status, readiness_score, reason),
            )

    def insert_depot(
        self,
        depot_id: str,
        scenario_id: str,
        name: str,
        depot_type: str,
        organization_id: str | None,
        map_lat: float | None,
        map_lng: float | None,
        capacity_score: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO depots (
                    id, scenario_id, organization_id, name, depot_type,
                    map_lat, map_lng, capacity_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    depot_id,
                    scenario_id,
                    organization_id,
                    name,
                    depot_type,
                    map_lat,
                    map_lng,
                    capacity_score,
                ),
            )

    def list_depots(self, scenario_id: str) -> list[Depot]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, organization_id, name, depot_type,
                       map_lat, map_lng, capacity_score, availability_status,
                       review_status, status
                FROM depots
                WHERE scenario_id = ? AND status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [Depot(**dict(row)) for row in rows]

    def update_depot(
        self,
        depot_id: str,
        name: str,
        depot_type: str,
        organization_id: str | None,
        map_lat: float | None,
        map_lng: float | None,
        capacity_score: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE depots
                SET name = ?, depot_type = ?, organization_id = ?,
                    map_lat = ?, map_lng = ?, capacity_score = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    name,
                    depot_type,
                    organization_id,
                    map_lat,
                    map_lng,
                    capacity_score,
                    depot_id,
                ),
            )

    def archive_depot(self, depot_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE depots
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (depot_id,),
            )

    def get_depot(self, depot_id: str) -> Depot | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, organization_id, name, depot_type,
                       map_lat, map_lng, capacity_score, availability_status,
                       review_status, status
                FROM depots WHERE id = ?
                """,
                (depot_id,),
            ).fetchone()
        return Depot(**dict(row)) if row else None

    def insert_resource_token(
        self,
        token_id: str,
        scenario_id: str,
        token_type: str,
        quantity: int,
        availability_window: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO resource_tokens (id, scenario_id, token_type, quantity, availability_window)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token_id, scenario_id, token_type, quantity, availability_window),
            )

    def list_resource_tokens(self, scenario_id: str) -> list[ResourceToken]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, token_type, quantity, availability_window, status
                FROM resource_tokens
                WHERE scenario_id = ? AND status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [ResourceToken(**dict(row)) for row in rows]

    def insert_depot_inventory(
        self,
        item_id: str,
        depot_id: str,
        option_label: str,
        quantity: int,
        inventory_category: str,
        resource_token_id: str | None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO depot_inventory (
                    id, depot_id, resource_token_id, inventory_category,
                    option_label, quantity
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (item_id, depot_id, resource_token_id, inventory_category, option_label, quantity),
            )

    def list_depot_inventory(self, depot_id: str) -> list[DepotInventoryItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, depot_id, resource_token_id, inventory_category,
                       option_label, quantity, availability_status, notes
                FROM depot_inventory
                WHERE depot_id = ?
                """,
                (depot_id,),
            ).fetchall()
        return [DepotInventoryItem(**dict(row)) for row in rows]

    def list_all_inventory_for_scenario(self, scenario_id: str) -> list[DepotInventoryItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT di.id, di.depot_id, di.resource_token_id, di.inventory_category,
                       di.option_label, di.quantity, di.availability_status, di.notes
                FROM depot_inventory di
                JOIN depots d ON d.id = di.depot_id
                WHERE d.scenario_id = ? AND d.status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [DepotInventoryItem(**dict(row)) for row in rows]

    def insert_transport_asset(
        self,
        asset_id: str,
        scenario_id: str,
        label: str,
        transport_type: str,
        organization_id: str | None,
        capacity_score: int,
        readiness_status: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO transport_assets (
                    id, scenario_id, organization_id, label,
                    transport_type, capacity_score, readiness_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    scenario_id,
                    organization_id,
                    label,
                    transport_type,
                    capacity_score,
                    readiness_status,
                ),
            )

    def list_transport_assets(self, scenario_id: str) -> list[TransportAsset]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, organization_id, label, transport_type,
                       capacity_score, readiness_status, status
                FROM transport_assets
                WHERE scenario_id = ? AND status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [TransportAsset(**dict(row)) for row in rows]

    def insert_route_segment(
        self,
        route_id: str,
        scenario_id: str,
        origin_entity_type: str,
        origin_entity_id: str,
        destination_entity_type: str,
        destination_entity_id: str,
        origin_lat: float | None,
        origin_lng: float | None,
        destination_lat: float | None,
        destination_lng: float | None,
        distance_score: int,
        fuel_stop_score: int,
        route_friction_score: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO route_segments (
                    id, scenario_id, origin_entity_type, origin_entity_id,
                    destination_entity_type, destination_entity_id,
                    origin_lat, origin_lng, destination_lat, destination_lng,
                    distance_score, fuel_stop_score, route_friction_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    route_id,
                    scenario_id,
                    origin_entity_type,
                    origin_entity_id,
                    destination_entity_type,
                    destination_entity_id,
                    origin_lat,
                    origin_lng,
                    destination_lat,
                    destination_lng,
                    distance_score,
                    fuel_stop_score,
                    route_friction_score,
                ),
            )

    def list_route_segments(self, scenario_id: str) -> list[RouteSegment]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, origin_entity_type, origin_entity_id,
                       destination_entity_type, destination_entity_id,
                       origin_lat, origin_lng, destination_lat, destination_lng,
                       distance_score, fuel_stop_score, route_friction_score,
                       availability_status, status
                FROM route_segments
                WHERE scenario_id = ? AND status = 'active'
                """,
                (scenario_id,),
            ).fetchall()
        return [RouteSegment(**dict(row)) for row in rows]

    def update_route_segment(
        self,
        route_id: str,
        distance_score: int,
        fuel_stop_score: int,
        route_friction_score: int,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE route_segments
                SET distance_score = ?, fuel_stop_score = ?, route_friction_score = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (distance_score, fuel_stop_score, route_friction_score, route_id),
            )

    def archive_route_segment(self, route_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE route_segments
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (route_id,),
            )

    def get_route_segment(self, route_id: str) -> RouteSegment | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, origin_entity_type, origin_entity_id,
                       destination_entity_type, destination_entity_id,
                       origin_lat, origin_lng, destination_lat, destination_lng,
                       distance_score, fuel_stop_score, route_friction_score,
                       availability_status, status
                FROM route_segments WHERE id = ?
                """,
                (route_id,),
            ).fetchone()
        return RouteSegment(**dict(row)) if row else None

    def insert_plan_score(
        self,
        score_id: str,
        scenario_id: str,
        route_segment_id: str | None,
        logistics_feasibility: int,
        rationale: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO plan_scores (
                    id, scenario_id, route_segment_id, logistics_feasibility, rationale
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (score_id, scenario_id, route_segment_id, logistics_feasibility, rationale),
            )

    def get_latest_plan_score(self, scenario_id: str) -> PlanScore | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, scenario_id, route_segment_id, logistics_feasibility,
                       rationale, created_at
                FROM plan_scores
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (scenario_id,),
            ).fetchone()
        return PlanScore(**dict(row)) if row else None
