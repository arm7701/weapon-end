from __future__ import annotations

from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.models import LogisticsFeasibilityResult
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.logistics.schemas import (
    CalculateLogisticsRequest,
    CreateDepotInventoryRequest,
    CreateDepotRequest,
    CreateOrganizationRequest,
    CreatePlatformTypeRequest,
    CreateResourceTokenRequest,
    CreateRouteSegmentRequest,
    CreateSimulatedPlatformRequest,
    CreateTransportAssetRequest,
    UpdateDepotRequest,
    UpdateOrganizationRequest,
    UpdatePlatformReadinessRequest,
    UpdateRouteSegmentRequest,
    UpdateSimulatedPlatformRequest,
)
from maap_app.modules.logistics.scoring import (
    AVAILABILITY_SCORES,
    READINESS_SCORES,
    LogisticsScoreInputs,
    calculate_logistics_feasibility,
)


class LogisticsService:
    def __init__(
        self,
        repository: LogisticsRepository,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service

    def create_organization(self, request: CreateOrganizationRequest) -> str:
        org_id = str(uuid4())
        text = f"{request.name}\n{request.location_label}"
        if not self.guardrail_service.validate_training_text(
            text=text, entity_type="organization", entity_id=org_id
        ):
            raise ValueError("Organization text was blocked by guardrail validation.")

        self.repository.insert_organization(
            org_id=org_id,
            scenario_id=request.scenario_id,
            name=request.name,
            organization_type=request.organization_type,
            location_label=request.location_label,
            map_lat=request.map_lat,
            map_lng=request.map_lng,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="organization_created",
            entity_type="organization",
            entity_id=org_id,
            details={"name": request.name},
        )
        return org_id

    def create_platform_type(self, request: CreatePlatformTypeRequest) -> str:
        type_id = str(uuid4())
        self.repository.insert_platform_type(
            type_id=type_id,
            scenario_id=request.scenario_id,
            label=request.label,
            capability_band=request.capability_band,
            resource_cost_score=request.resource_cost_score,
            support_need_score=request.support_need_score,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="platform_type_created",
            entity_type="platform_type",
            entity_id=type_id,
            details={"label": request.label},
        )
        return type_id

    def create_simulated_platform(self, request: CreateSimulatedPlatformRequest) -> str:
        platform_id = str(uuid4())
        if not self.guardrail_service.validate_training_text(
            text=request.label,
            entity_type="simulated_platform",
            entity_id=platform_id,
        ):
            raise ValueError("Platform text was blocked by guardrail validation.")

        self.repository.insert_simulated_platform(
            platform_id=platform_id,
            scenario_id=request.scenario_id,
            label=request.label,
            organization_id=request.organization_id,
            platform_type_id=request.platform_type_id,
            capability_band=request.capability_band,
            availability_score=request.availability_score,
            readiness_status=request.readiness_status,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="simulated_platform_created",
            entity_type="simulated_platform",
            entity_id=platform_id,
            details={"label": request.label},
        )
        return platform_id

    def update_platform_readiness(self, request: UpdatePlatformReadinessRequest) -> None:
        if not self.guardrail_service.validate_training_text(
            text=request.reason,
            entity_type="platform_readiness",
            entity_id=request.platform_id,
        ):
            raise ValueError("Readiness update was blocked by guardrail validation.")

        event_id = str(uuid4())
        self.repository.update_platform_readiness(
            platform_id=request.platform_id,
            readiness_status=request.readiness_status,
            readiness_note=request.reason,
        )
        self.repository.insert_readiness_event(
            event_id=event_id,
            platform_id=request.platform_id,
            status=request.readiness_status,
            readiness_score=request.readiness_score,
            reason=request.reason,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="platform_readiness_updated",
            entity_type="simulated_platform",
            entity_id=request.platform_id,
            details={"status": request.readiness_status},
        )

    def create_depot(self, request: CreateDepotRequest) -> str:
        depot_id = str(uuid4())
        if not self.guardrail_service.validate_training_text(
            text=request.name,
            entity_type="depot",
            entity_id=depot_id,
        ):
            raise ValueError("Depot text was blocked by guardrail validation.")

        self.repository.insert_depot(
            depot_id=depot_id,
            scenario_id=request.scenario_id,
            name=request.name,
            depot_type=request.depot_type,
            organization_id=request.organization_id,
            map_lat=request.map_lat,
            map_lng=request.map_lng,
            capacity_score=request.capacity_score,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="depot_created",
            entity_type="depot",
            entity_id=depot_id,
            details={"name": request.name},
        )
        return depot_id

    def create_resource_token(self, request: CreateResourceTokenRequest) -> str:
        token_id = str(uuid4())
        self.repository.insert_resource_token(
            token_id=token_id,
            scenario_id=request.scenario_id,
            token_type=request.token_type,
            quantity=request.quantity,
            availability_window=request.availability_window,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="resource_token_created",
            entity_type="resource_token",
            entity_id=token_id,
            details={"token_type": request.token_type},
        )
        return token_id

    def create_depot_inventory(self, request: CreateDepotInventoryRequest) -> str:
        item_id = str(uuid4())
        if not self.guardrail_service.validate_training_text(
            text=request.option_label,
            entity_type="depot_inventory",
            entity_id=item_id,
        ):
            raise ValueError("Inventory text was blocked by guardrail validation.")

        self.repository.insert_depot_inventory(
            item_id=item_id,
            depot_id=request.depot_id,
            option_label=request.option_label,
            quantity=request.quantity,
            inventory_category=request.inventory_category,
            resource_token_id=request.resource_token_id,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="depot_inventory_created",
            entity_type="depot_inventory",
            entity_id=item_id,
            details={"depot_id": request.depot_id},
        )
        return item_id

    def create_transport_asset(self, request: CreateTransportAssetRequest) -> str:
        asset_id = str(uuid4())
        self.repository.insert_transport_asset(
            asset_id=asset_id,
            scenario_id=request.scenario_id,
            label=request.label,
            transport_type=request.transport_type,
            organization_id=request.organization_id,
            capacity_score=request.capacity_score,
            readiness_status=request.readiness_status,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="transport_asset_created",
            entity_type="transport_asset",
            entity_id=asset_id,
            details={"label": request.label},
        )
        return asset_id

    def create_route_segment(self, request: CreateRouteSegmentRequest) -> str:
        route_id = str(uuid4())
        self.repository.insert_route_segment(
            route_id=route_id,
            scenario_id=request.scenario_id,
            origin_entity_type=request.origin_entity_type,
            origin_entity_id=request.origin_entity_id,
            destination_entity_type=request.destination_entity_type,
            destination_entity_id=request.destination_entity_id,
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
            destination_lat=request.destination_lat,
            destination_lng=request.destination_lng,
            distance_score=request.distance_score,
            fuel_stop_score=request.fuel_stop_score,
            route_friction_score=request.route_friction_score,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="route_segment_created",
            entity_type="route_segment",
            entity_id=route_id,
            details={"scenario_id": request.scenario_id},
        )
        return route_id

    def calculate_logistics_feasibility(
        self,
        request: CalculateLogisticsRequest,
    ) -> LogisticsFeasibilityResult:
        scenario_id = request.scenario_id
        depots = self.repository.list_depots(scenario_id)
        inventory = self.repository.list_all_inventory_for_scenario(scenario_id)
        tokens = self.repository.list_resource_tokens(scenario_id)
        transports = self.repository.list_transport_assets(scenario_id)
        platforms = self.repository.list_simulated_platforms(scenario_id)

        route = None
        if request.route_segment_id:
            route = self.repository.get_route_segment(request.route_segment_id)

        inputs = LogisticsScoreInputs(
            depot_availability_scores=[
                AVAILABILITY_SCORES.get(d.availability_status, 50) for d in depots
            ],
            inventory_availability_scores=[
                AVAILABILITY_SCORES.get(i.availability_status, 50) for i in inventory
            ],
            resource_token_quantities=[t.quantity for t in tokens],
            route_friction_score=route.route_friction_score if route else None,
            fuel_stop_score=route.fuel_stop_score if route else None,
            transport_readiness_scores=[
                READINESS_SCORES.get(t.readiness_status, 50) for t in transports
            ],
            platform_readiness_scores=[
                READINESS_SCORES.get(p.readiness_status, 50) for p in platforms
            ],
        )
        score, rationale, warnings = calculate_logistics_feasibility(inputs)
        score_id = str(uuid4())
        self.repository.insert_plan_score(
            score_id=score_id,
            scenario_id=scenario_id,
            route_segment_id=request.route_segment_id,
            logistics_feasibility=score,
            rationale=rationale,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="logistics_score_calculated",
            entity_type="plan_score",
            entity_id=score_id,
            details={"score": score, "route_segment_id": request.route_segment_id},
        )
        return LogisticsFeasibilityResult(
            score=score,
            rationale=rationale,
            warnings=warnings,
            plan_score_id=score_id,
        )

    def update_organization(self, request: UpdateOrganizationRequest) -> None:
        text = f"{request.name}\n{request.location_label}"
        if not self.guardrail_service.validate_training_text(
            text=text,
            entity_type="organization",
            entity_id=request.organization_id,
        ):
            raise ValueError("Organization text was blocked by guardrail validation.")
        self.repository.update_organization(
            org_id=request.organization_id,
            name=request.name,
            organization_type=request.organization_type,
            location_label=request.location_label,
            map_lat=request.map_lat,
            map_lng=request.map_lng,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="organization_updated",
            entity_type="organization",
            entity_id=request.organization_id,
            details={"name": request.name},
        )

    def delete_organization(self, organization_id: str) -> None:
        self.repository.archive_organization(organization_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="organization_archived",
            entity_type="organization",
            entity_id=organization_id,
            details={},
        )

    def update_simulated_platform(self, request: UpdateSimulatedPlatformRequest) -> None:
        if not self.guardrail_service.validate_training_text(
            text=request.label,
            entity_type="simulated_platform",
            entity_id=request.platform_id,
        ):
            raise ValueError("Platform text was blocked by guardrail validation.")
        self.repository.update_simulated_platform(
            platform_id=request.platform_id,
            label=request.label,
            organization_id=request.organization_id,
            capability_band=request.capability_band,
            availability_score=request.availability_score,
            readiness_status=request.readiness_status,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="simulated_platform_updated",
            entity_type="simulated_platform",
            entity_id=request.platform_id,
            details={"label": request.label},
        )

    def delete_simulated_platform(self, platform_id: str) -> None:
        self.repository.archive_simulated_platform(platform_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="simulated_platform_archived",
            entity_type="simulated_platform",
            entity_id=platform_id,
            details={},
        )

    def update_depot(self, request: UpdateDepotRequest) -> None:
        if not self.guardrail_service.validate_training_text(
            text=request.name,
            entity_type="depot",
            entity_id=request.depot_id,
        ):
            raise ValueError("Depot text was blocked by guardrail validation.")
        self.repository.update_depot(
            depot_id=request.depot_id,
            name=request.name,
            depot_type=request.depot_type,
            organization_id=request.organization_id,
            map_lat=request.map_lat,
            map_lng=request.map_lng,
            capacity_score=request.capacity_score,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="depot_updated",
            entity_type="depot",
            entity_id=request.depot_id,
            details={"name": request.name},
        )

    def delete_depot(self, depot_id: str) -> None:
        self.repository.archive_depot(depot_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="depot_archived",
            entity_type="depot",
            entity_id=depot_id,
            details={},
        )

    def update_route_segment(self, request: UpdateRouteSegmentRequest) -> None:
        self.repository.update_route_segment(
            route_id=request.route_id,
            distance_score=request.distance_score,
            fuel_stop_score=request.fuel_stop_score,
            route_friction_score=request.route_friction_score,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="route_segment_updated",
            entity_type="route_segment",
            entity_id=request.route_id,
            details={},
        )

    def delete_route_segment(self, route_id: str) -> None:
        self.repository.archive_route_segment(route_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="route_segment_archived",
            entity_type="route_segment",
            entity_id=route_id,
            details={},
        )

    def get_simulated_platform(self, platform_id: str):
        return self.repository.get_simulated_platform(platform_id)

    def list_organizations(self, scenario_id: str):
        return self.repository.list_organizations(scenario_id)

    def list_depots(self, scenario_id: str):
        return self.repository.list_depots(scenario_id)

    def list_route_segments(self, scenario_id: str):
        return self.repository.list_route_segments(scenario_id)

    def list_simulated_platforms(self, scenario_id: str):
        return self.repository.list_simulated_platforms(scenario_id)

    def get_organization(self, org_id: str):
        return self.repository.get_organization(org_id)

    def get_depot(self, depot_id: str):
        return self.repository.get_depot(depot_id)

    def get_route_segment(self, route_id: str):
        return self.repository.get_route_segment(route_id)

    def get_latest_plan_score(self, scenario_id: str):
        return self.repository.get_latest_plan_score(scenario_id)

    def list_map_layers(self, scenario_id: str) -> dict:
        org_markers = []
        for org in self.repository.list_organizations(scenario_id):
            if org.map_lat is None or org.map_lng is None:
                continue
            org_markers.append(
                {
                    "entityId": org.id,
                    "entityType": "organization",
                    "label": org.name,
                    "lat": org.map_lat,
                    "lng": org.map_lng,
                    "readiness": org.readiness_summary,
                }
            )

        depot_markers = []
        for depot in self.repository.list_depots(scenario_id):
            if depot.map_lat is None or depot.map_lng is None:
                continue
            depot_markers.append(
                {
                    "entityId": depot.id,
                    "entityType": "depot",
                    "label": depot.name,
                    "lat": depot.map_lat,
                    "lng": depot.map_lng,
                    "availability": depot.availability_status,
                }
            )

        routes = []
        for route in self.repository.list_route_segments(scenario_id):
            if (
                route.origin_lat is None
                or route.origin_lng is None
                or route.destination_lat is None
                or route.destination_lng is None
            ):
                continue
            routes.append(
                {
                    "routeId": route.id,
                    "origin": [route.origin_lat, route.origin_lng],
                    "destination": [route.destination_lat, route.destination_lng],
                    "friction": route.route_friction_score,
                }
            )

        return {
            "organizations": org_markers,
            "depots": depot_markers,
            "routes": routes,
        }
