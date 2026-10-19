from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Organization:
    id: str
    scenario_id: str
    name: str
    organization_type: str
    map_lat: float | None
    map_lng: float | None
    location_label: str
    is_synthetic_location: int
    readiness_summary: str
    review_status: str
    status: str
    created_at: str | None = None


@dataclass(frozen=True)
class PlatformType:
    id: str
    scenario_id: str
    label: str
    capability_band: str
    resource_cost_score: int
    support_need_score: int
    status: str


@dataclass(frozen=True)
class SimulatedPlatform:
    id: str
    scenario_id: str
    organization_id: str | None
    platform_type_id: str | None
    label: str
    capability_band: str
    availability_score: int
    readiness_status: str
    readiness_note: str
    status: str


@dataclass(frozen=True)
class Depot:
    id: str
    scenario_id: str
    organization_id: str | None
    name: str
    depot_type: str
    map_lat: float | None
    map_lng: float | None
    capacity_score: int
    availability_status: str
    review_status: str
    status: str


@dataclass(frozen=True)
class ResourceToken:
    id: str
    scenario_id: str
    token_type: str
    quantity: int
    availability_window: str
    status: str


@dataclass(frozen=True)
class DepotInventoryItem:
    id: str
    depot_id: str
    resource_token_id: str | None
    inventory_category: str
    option_label: str
    quantity: int
    availability_status: str
    notes: str


@dataclass(frozen=True)
class TransportAsset:
    id: str
    scenario_id: str
    organization_id: str | None
    label: str
    transport_type: str
    capacity_score: int
    readiness_status: str
    status: str


@dataclass(frozen=True)
class RouteSegment:
    id: str
    scenario_id: str
    origin_entity_type: str
    origin_entity_id: str
    destination_entity_type: str
    destination_entity_id: str
    origin_lat: float | None
    origin_lng: float | None
    destination_lat: float | None
    destination_lng: float | None
    distance_score: int
    fuel_stop_score: int
    route_friction_score: int
    availability_status: str
    status: str


@dataclass(frozen=True)
class PlanScore:
    id: str
    scenario_id: str
    route_segment_id: str | None
    logistics_feasibility: int
    rationale: str
    created_at: str | None = None


@dataclass
class LogisticsFeasibilityResult:
    score: int
    rationale: str
    warnings: list[str] = field(default_factory=list)
    plan_score_id: str | None = None
