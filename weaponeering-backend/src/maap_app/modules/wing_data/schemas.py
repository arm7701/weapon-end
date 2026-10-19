from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateAirWingRequest:
    scenario_id: str
    wing_name: str
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class UpdateAirWingRequest:
    wing_id: str
    wing_name: str
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class CreateFlyingUnitRequest:
    scenario_id: str
    wing_id: str
    unit_name: str
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class UpdateFlyingUnitRequest:
    flying_unit_id: str
    wing_id: str
    unit_name: str
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class CreateAircraftRequest:
    scenario_id: str
    wing_id: str
    aircraft_type: str = "F-16"
    flying_unit_id: str | None = None
    mission_ready: str = "not_ready"


@dataclass(frozen=True)
class UpdateAircraftRequest:
    aircraft_id: str
    wing_id: str
    aircraft_type: str
    flying_unit_id: str | None
    mission_ready: str


@dataclass(frozen=True)
class CreatePilotRequest:
    scenario_id: str
    pilot_name: str
    callsign: str = ""
    cep_value: float = 0.0
    wing_id: str | None = None
    flying_unit_id: str | None = None


@dataclass(frozen=True)
class UpdatePilotRequest:
    pilot_id: str
    pilot_name: str
    callsign: str
    cep_value: float
    wing_id: str | None = None
    flying_unit_id: str | None = None


@dataclass(frozen=True)
class CreateWingDepotRequest:
    scenario_id: str
    wing_id: str
    depot_name: str
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class UpdateWingDepotRequest:
    depot_id: str
    wing_id: str
    depot_name: str
    map_lat: float | None = None
    map_lng: float | None = None


@dataclass(frozen=True)
class CreateWingProductRequest:
    scenario_id: str
    product_name: str
    weight_pounds: float = 0.0
    unit_cost: float = 0.0
    description: str = ""


@dataclass(frozen=True)
class UpdateWingProductRequest:
    product_id: str
    product_name: str
    weight_pounds: float
    unit_cost: float
    description: str = ""


@dataclass(frozen=True)
class UpsertDepotInventoryRequest:
    scenario_id: str
    depot_id: str
    product_id: str
    quantity: int


@dataclass(frozen=True)
class TransferDepotInventoryRequest:
    scenario_id: str
    from_depot_id: str
    to_depot_id: str
    product_id: str
    quantity: int


@dataclass(frozen=True)
class CreateLogisticsVehicleRequest:
    scenario_id: str
    wing_id: str
    vehicle_name: str
    fuel_consumption_rate: float = 0.0
    mission_ready: str = "not_ready"


@dataclass(frozen=True)
class UpdateLogisticsVehicleRequest:
    vehicle_id: str
    wing_id: str
    vehicle_name: str
    fuel_consumption_rate: float
    mission_ready: str
