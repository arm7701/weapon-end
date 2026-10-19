from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Organizations ---


class OrganizationCreate(BaseModel):
    scenario_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    organization_type: str = "unit"
    location_label: str = ""
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    is_synthetic_location: bool = True
    readiness_summary: str = "unknown"
    review_status: str = "draft"
    status: str = "active"


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    organization_type: str | None = None
    location_label: str | None = None
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    is_synthetic_location: bool | None = None
    readiness_summary: str | None = None
    review_status: str | None = None
    status: str | None = None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    name: str
    organization_type: str
    map_lat: float | None = None
    map_lng: float | None = None
    location_label: str
    is_synthetic_location: bool
    readiness_summary: str
    review_status: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Platform types ---


class PlatformTypeCreate(BaseModel):
    scenario_id: UUID
    label: str = Field(..., min_length=1, max_length=255)
    capability_band: str = "medium"
    resource_cost_score: int = Field(default=50, ge=0, le=100)
    support_need_score: int = Field(default=50, ge=0, le=100)
    status: str = "active"


class PlatformTypeUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    capability_band: str | None = None
    resource_cost_score: int | None = Field(default=None, ge=0, le=100)
    support_need_score: int | None = Field(default=None, ge=0, le=100)
    status: str | None = None


class PlatformTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    label: str
    capability_band: str
    resource_cost_score: int
    support_need_score: int
    status: str
    created_at: datetime
    updated_at: datetime


# --- Simulated platforms ---


class SimulatedPlatformCreate(BaseModel):
    scenario_id: UUID
    label: str = Field(..., min_length=1, max_length=255)
    organization_id: UUID | None = None
    platform_type_id: UUID | None = None
    capability_band: str = "medium"
    availability_score: int = Field(default=3, ge=1, le=5)
    readiness_status: str = "unknown"
    readiness_note: str = ""
    status: str = "active"


class SimulatedPlatformUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    organization_id: UUID | None = None
    platform_type_id: UUID | None = None
    capability_band: str | None = None
    availability_score: int | None = Field(default=None, ge=1, le=5)
    readiness_status: str | None = None
    readiness_note: str | None = None
    status: str | None = None


class SimulatedPlatformOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    organization_id: UUID | None = None
    platform_type_id: UUID | None = None
    label: str
    capability_band: str
    availability_score: int
    readiness_status: str
    readiness_note: str
    status: str
    created_at: datetime
    updated_at: datetime


class PlatformReadinessIn(BaseModel):
    status: str = Field(..., min_length=1, max_length=64)
    readiness_score: int = Field(default=50, ge=0, le=100)
    reason: str = ""


class PlatformReadinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    simulated_platform_id: UUID
    status: str
    readiness_score: int
    reason: str
    created_at: datetime


# --- Depots ---


class DepotCreate(BaseModel):
    scenario_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    depot_type: str = "abstract_store"
    organization_id: UUID | None = None
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    capacity_score: int = Field(default=50, ge=0, le=100)
    availability_status: str = "available"
    review_status: str = "draft"
    status: str = "active"


class DepotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    depot_type: str | None = None
    organization_id: UUID | None = None
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    capacity_score: int | None = Field(default=None, ge=0, le=100)
    availability_status: str | None = None
    review_status: str | None = None
    status: str | None = None


class DepotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    organization_id: UUID | None = None
    name: str
    depot_type: str
    map_lat: float | None = None
    map_lng: float | None = None
    capacity_score: int
    availability_status: str
    review_status: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Resource tokens ---


class ResourceTokenCreate(BaseModel):
    scenario_id: UUID
    token_type: str = Field(..., min_length=1, max_length=128)
    quantity: int = Field(default=0, ge=0)
    availability_window: str = ""
    status: str = "active"


class ResourceTokenUpdate(BaseModel):
    token_type: str | None = Field(default=None, min_length=1, max_length=128)
    quantity: int | None = Field(default=None, ge=0)
    availability_window: str | None = None
    status: str | None = None


class ResourceTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    token_type: str
    quantity: int
    availability_window: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Depot inventory ---


class DepotInventoryCreate(BaseModel):
    depot_id: UUID
    option_label: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=0, ge=0)
    inventory_category: str = "support_token"
    resource_token_id: UUID | None = None
    availability_status: str = "available"
    notes: str = ""


class DepotInventoryUpdate(BaseModel):
    option_label: str | None = Field(default=None, min_length=1, max_length=255)
    quantity: int | None = Field(default=None, ge=0)
    inventory_category: str | None = None
    resource_token_id: UUID | None = None
    availability_status: str | None = None
    notes: str | None = None


class DepotInventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    depot_id: UUID
    resource_token_id: UUID | None = None
    inventory_category: str
    option_label: str
    quantity: int
    availability_status: str
    notes: str
    created_at: datetime
    updated_at: datetime


# --- Transport assets ---


class TransportAssetCreate(BaseModel):
    scenario_id: UUID
    label: str = Field(..., min_length=1, max_length=255)
    transport_type: str = "ground"
    organization_id: UUID | None = None
    capacity_score: int = Field(default=50, ge=0, le=100)
    readiness_status: str = "unknown"
    status: str = "active"


class TransportAssetUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    transport_type: str | None = None
    organization_id: UUID | None = None
    capacity_score: int | None = Field(default=None, ge=0, le=100)
    readiness_status: str | None = None
    status: str | None = None


class TransportAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    organization_id: UUID | None = None
    label: str
    transport_type: str
    capacity_score: int
    readiness_status: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Route segments ---


class RouteSegmentCreate(BaseModel):
    scenario_id: UUID
    origin_entity_type: str = Field(..., min_length=1, max_length=64)
    origin_entity_id: str = Field(..., min_length=1, max_length=64)
    destination_entity_type: str = Field(..., min_length=1, max_length=64)
    destination_entity_id: str = Field(..., min_length=1, max_length=64)
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    destination_lat: float | None = Field(default=None, ge=-90, le=90)
    destination_lng: float | None = Field(default=None, ge=-180, le=180)
    distance_score: int = Field(default=50, ge=0, le=100)
    fuel_stop_score: int = Field(default=50, ge=0, le=100)
    route_friction_score: int = Field(default=50, ge=0, le=100)
    availability_status: str = "available"
    status: str = "active"


class RouteSegmentUpdate(BaseModel):
    origin_entity_type: str | None = None
    origin_entity_id: str | None = None
    destination_entity_type: str | None = None
    destination_entity_id: str | None = None
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    destination_lat: float | None = Field(default=None, ge=-90, le=90)
    destination_lng: float | None = Field(default=None, ge=-180, le=180)
    distance_score: int | None = Field(default=None, ge=0, le=100)
    fuel_stop_score: int | None = Field(default=None, ge=0, le=100)
    route_friction_score: int | None = Field(default=None, ge=0, le=100)
    availability_status: str | None = None
    status: str | None = None


class RouteSegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    origin_entity_type: str
    origin_entity_id: str
    destination_entity_type: str
    destination_entity_id: str
    origin_lat: float | None = None
    origin_lng: float | None = None
    destination_lat: float | None = None
    destination_lng: float | None = None
    distance_score: int
    fuel_stop_score: int
    route_friction_score: int
    availability_status: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Plan scores ---


class PlanScoreCreate(BaseModel):
    scenario_id: UUID
    logistics_feasibility: int = Field(..., ge=0, le=100)
    route_segment_id: UUID | None = None
    plan_option_id: str | None = None
    priority_alignment: int | None = Field(default=None, ge=0, le=100)
    resource_balance: int | None = Field(default=None, ge=0, le=100)
    risk_indicator: int | None = Field(default=None, ge=0, le=100)
    rationale: str = ""


class PlanScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    route_segment_id: UUID | None = None
    plan_option_id: str | None = None
    priority_alignment: int | None = None
    logistics_feasibility: int
    resource_balance: int | None = None
    risk_indicator: int | None = None
    rationale: str
    created_at: datetime
