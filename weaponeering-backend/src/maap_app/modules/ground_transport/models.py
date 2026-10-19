from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroundRouteResult:
    distance_m: float
    duration_min: float
    path: tuple[tuple[float, float], ...]
    route_mode: str


@dataclass(frozen=True)
class ScenarioGroundTransport:
    id: str
    scenario_id: str
    origin_wing_id: str
    destination_wing_id: str
    product_id: str | None
    vehicle_id: str | None
    quantity: int
    distance_m: float
    duration_min: float
    route_mode: str
    route_geometry_json: str | None
    label: str
    status: str
    created_at: str
    updated_at: str
