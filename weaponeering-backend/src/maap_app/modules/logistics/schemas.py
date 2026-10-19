from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateOrganizationRequest:
    scenario_id: str
    name: str
    organization_type: str = "unit"
    location_label: str = ""
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class CreatePlatformTypeRequest:
    scenario_id: str
    label: str
    capability_band: str = "medium"
    resource_cost_score: int = 50
    support_need_score: int = 50


@dataclass(frozen=True)
class CreateSimulatedPlatformRequest:
    scenario_id: str
    label: str
    organization_id: str | None = None
    platform_type_id: str | None = None
    capability_band: str = "medium"
    availability_score: int = 3
    readiness_status: str = "unknown"


@dataclass(frozen=True)
class UpdatePlatformReadinessRequest:
    platform_id: str
    readiness_status: str
    readiness_score: int
    reason: str = ""


@dataclass(frozen=True)
class CreateDepotRequest:
    scenario_id: str
    name: str
    depot_type: str = "abstract_store"
    organization_id: str | None = None
    map_lat: float | None = None
    map_lng: float | None = None
    capacity_score: int = 50


@dataclass(frozen=True)
class CreateResourceTokenRequest:
    scenario_id: str
    token_type: str
    quantity: int
    availability_window: str = ""


@dataclass(frozen=True)
class CreateDepotInventoryRequest:
    depot_id: str
    option_label: str
    quantity: int
    inventory_category: str = "support_token"
    resource_token_id: str | None = None


@dataclass(frozen=True)
class CreateTransportAssetRequest:
    scenario_id: str
    label: str
    transport_type: str = "ground"
    organization_id: str | None = None
    capacity_score: int = 50
    readiness_status: str = "unknown"


@dataclass(frozen=True)
class CreateRouteSegmentRequest:
    scenario_id: str
    origin_entity_type: str
    origin_entity_id: str
    destination_entity_type: str
    destination_entity_id: str
    origin_lat: float | None = None
    origin_lng: float | None = None
    destination_lat: float | None = None
    destination_lng: float | None = None
    distance_score: int = 50
    fuel_stop_score: int = 50
    route_friction_score: int = 50


@dataclass(frozen=True)
class CalculateLogisticsRequest:
    scenario_id: str
    route_segment_id: str | None = None


@dataclass(frozen=True)
class UpdateOrganizationRequest:
    organization_id: str
    name: str
    organization_type: str
    location_label: str = ""
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class UpdateSimulatedPlatformRequest:
    platform_id: str
    label: str
    organization_id: str | None = None
    capability_band: str = "medium"
    availability_score: int = 3
    readiness_status: str = "unknown"


@dataclass(frozen=True)
class UpdateDepotRequest:
    depot_id: str
    name: str
    depot_type: str = "abstract_store"
    organization_id: str | None = None
    map_lat: float | None = None
    map_lng: float | None = None
    capacity_score: int = 50


@dataclass(frozen=True)
class UpdateRouteSegmentRequest:
    route_id: str
    route_friction_score: int = 50
    fuel_stop_score: int = 50
    distance_score: int = 50
