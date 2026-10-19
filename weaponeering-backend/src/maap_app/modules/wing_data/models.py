from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AirWing:
    id: str
    scenario_id: str
    wing_name: str
    map_lat: float | None
    map_lng: float | None
    status: str
    created_at: str | None = None


@dataclass(frozen=True)
class WingDistanceResult:
    wing_id: str
    wing_name: str
    map_lat: float
    map_lng: float
    distance_km: float
    distance_nm: float
    rank: int = 0


@dataclass(frozen=True)
class WingFlyingUnit:
    id: str
    scenario_id: str
    wing_id: str
    unit_name: str
    status: str
    map_lat: float | None = None
    map_lng: float | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class WingAircraft:
    id: str
    scenario_id: str
    wing_id: str
    aircraft_type: str
    flying_unit_id: str | None
    mission_ready: str
    status: str
    created_at: str | None = None


@dataclass(frozen=True)
class WingPilot:
    id: str
    scenario_id: str
    wing_id: str | None
    flying_unit_id: str | None
    pilot_name: str
    callsign: str
    cep_value: float
    status: str
    created_at: str | None = None


@dataclass(frozen=True)
class WingDepot:
    id: str
    scenario_id: str
    wing_id: str
    depot_name: str
    map_lat: float | None
    map_lng: float | None
    status: str
    created_at: str | None = None


@dataclass(frozen=True)
class WingProduct:
    id: str
    scenario_id: str
    product_name: str
    weight_pounds: float
    unit_cost: float
    status: str
    created_at: str | None = None
    description: str = ""


@dataclass(frozen=True)
class WingDepotInventory:
    id: str
    scenario_id: str
    depot_id: str
    product_id: str
    quantity: int
    status: str
    created_at: str | None = None


@dataclass(frozen=True)
class WingDepotInventoryDetail:
    id: str
    scenario_id: str
    depot_id: str
    depot_name: str
    product_id: str
    product_name: str
    quantity: int


@dataclass(frozen=True)
class WingDepotTransferDetail:
    id: str
    scenario_id: str
    from_depot_id: str
    from_depot_name: str
    to_depot_id: str
    to_depot_name: str
    product_id: str
    product_name: str
    quantity: int
    created_at: str | None = None


@dataclass(frozen=True)
class WingTableSummary:
    flying_unit_count: int
    aircraft_count: int
    pilot_count: int
    depot_count: int
    product_stock: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class WingMapDetail:
    wing: AirWing
    flying_units: tuple[WingFlyingUnit, ...]
    aircraft: tuple[WingAircraft, ...]
    pilots: tuple[WingPilot, ...]
    inventory: tuple[WingDepotInventoryDetail, ...]

    @property
    def aircraft_ready_count(self) -> int:
        return sum(1 for row in self.aircraft if row.mission_ready == "ready")

    @property
    def aircraft_not_ready_count(self) -> int:
        return len(self.aircraft) - self.aircraft_ready_count


@dataclass(frozen=True)
class WingLogisticsVehicle:
    id: str
    scenario_id: str
    wing_id: str
    vehicle_name: str
    fuel_consumption_rate: float
    mission_ready: str
    status: str
    created_at: str | None = None
