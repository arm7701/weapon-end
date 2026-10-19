from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Air wings ---


class AirWingCreate(BaseModel):
    scenario_id: UUID
    wing_name: str = Field(..., min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    status: str = "active"


class AirWingUpdate(BaseModel):
    wing_name: str | None = Field(default=None, min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = None


class AirWingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    wing_name: str
    map_lat: float | None = None
    map_lng: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class WingTableSummaryOut(BaseModel):
    wing_id: UUID
    flying_unit_count: int
    aircraft_count: int
    pilot_count: int
    depot_count: int
    product_stock: list[tuple[str, int]] = Field(default_factory=list)


# --- Flying units ---


class WingFlyingUnitCreate(BaseModel):
    scenario_id: UUID
    wing_id: UUID
    unit_name: str = Field(..., min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    status: str = "active"


class WingFlyingUnitUpdate(BaseModel):
    wing_id: UUID | None = None
    unit_name: str | None = Field(default=None, min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = None


class WingFlyingUnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    wing_id: UUID
    unit_name: str
    map_lat: float | None = None
    map_lng: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# --- Aircraft ---


class WingAircraftCreate(BaseModel):
    scenario_id: UUID
    wing_id: UUID
    aircraft_type: str = "F-16"
    flying_unit_id: UUID | None = None
    mission_ready: str = "not_ready"
    status: str = "active"


class WingAircraftUpdate(BaseModel):
    wing_id: UUID | None = None
    aircraft_type: str | None = None
    flying_unit_id: UUID | None = None
    mission_ready: str | None = None
    status: str | None = None


class WingAircraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    wing_id: UUID
    flying_unit_id: UUID | None = None
    aircraft_type: str
    mission_ready: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Pilots ---


class WingPilotCreate(BaseModel):
    scenario_id: UUID
    pilot_name: str = Field(..., min_length=1, max_length=255)
    callsign: str = ""
    cep_value: float = Field(default=0.0, ge=0)
    wing_id: UUID | None = None
    flying_unit_id: UUID | None = None
    status: str = "active"


class WingPilotUpdate(BaseModel):
    pilot_name: str | None = Field(default=None, min_length=1, max_length=255)
    callsign: str | None = None
    cep_value: float | None = Field(default=None, ge=0)
    wing_id: UUID | None = None
    flying_unit_id: UUID | None = None
    status: str | None = None


class WingPilotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    wing_id: UUID | None = None
    flying_unit_id: UUID | None = None
    pilot_name: str
    callsign: str
    cep_value: float
    status: str
    created_at: datetime
    updated_at: datetime


# --- Depots ---


class WingDepotCreate(BaseModel):
    scenario_id: UUID
    wing_id: UUID
    depot_name: str = Field(..., min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    status: str = "active"


class WingDepotUpdate(BaseModel):
    wing_id: UUID | None = None
    depot_name: str | None = Field(default=None, min_length=1, max_length=255)
    map_lat: float | None = Field(default=None, ge=-90, le=90)
    map_lng: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = None


class WingDepotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    wing_id: UUID
    depot_name: str
    map_lat: float | None = None
    map_lng: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# --- Products ---


class WingProductCreate(BaseModel):
    scenario_id: UUID
    product_name: str = Field(..., min_length=1, max_length=255)
    weight_pounds: float = Field(default=0.0, ge=0)
    unit_cost: float = Field(default=0.0, ge=0)
    description: str = Field(default="", max_length=2000)
    status: str = "active"


class WingProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    weight_pounds: float | None = Field(default=None, ge=0)
    unit_cost: float | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = None


class WingProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    product_name: str
    weight_pounds: float
    unit_cost: float
    description: str = ""
    status: str
    created_at: datetime
    updated_at: datetime


class KnownProductOut(BaseModel):
    key: str
    product_name: str
    weight_pounds: float
    unit_cost: float = 0.0
    description: str = ""
    delivery: str = "low_drag"
    guidance: str = "unguided"
    category: str = "gravity"
    category_label: str = ""


# --- Inventory ---


class WingDepotInventoryUpsert(BaseModel):
    scenario_id: UUID
    depot_id: UUID
    product_id: UUID
    quantity: int = Field(..., ge=0)


class WingDepotInventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    depot_id: UUID
    product_id: UUID
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime


class WingDepotInventoryDetailOut(BaseModel):
    id: UUID
    scenario_id: UUID
    depot_id: UUID
    depot_name: str
    product_id: UUID
    product_name: str
    quantity: int


class WingDepotTransferCreate(BaseModel):
    scenario_id: UUID
    from_depot_id: UUID
    to_depot_id: UUID
    product_id: UUID
    quantity: int = Field(..., gt=0)


class WingDepotTransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    product_id: UUID
    from_depot_id: UUID
    to_depot_id: UUID
    quantity: int
    created_at: datetime


class WingDepotTransferDetailOut(BaseModel):
    id: UUID
    scenario_id: UUID
    from_depot_id: UUID
    from_depot_name: str
    to_depot_id: UUID
    to_depot_name: str
    product_id: UUID
    product_name: str
    quantity: int
    created_at: datetime


# --- Logistics vehicles ---


class WingLogisticsVehicleCreate(BaseModel):
    scenario_id: UUID
    wing_id: UUID
    vehicle_name: str = Field(..., min_length=1, max_length=255)
    fuel_consumption_rate: float = Field(default=0.0, ge=0)
    mission_ready: str = "not_ready"
    status: str = "active"


class WingLogisticsVehicleUpdate(BaseModel):
    wing_id: UUID | None = None
    vehicle_name: str | None = Field(default=None, min_length=1, max_length=255)
    fuel_consumption_rate: float | None = Field(default=None, ge=0)
    mission_ready: str | None = None
    status: str | None = None


class WingLogisticsVehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    wing_id: UUID
    vehicle_name: str
    fuel_consumption_rate: float
    mission_ready: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Aggregate ---


class WingMapDetailOut(BaseModel):
    wing: AirWingOut
    flying_units: list[WingFlyingUnitOut]
    aircraft: list[WingAircraftOut]
    pilots: list[WingPilotOut]
    inventory: list[WingDepotInventoryDetailOut]
    aircraft_ready_count: int
    aircraft_not_ready_count: int
