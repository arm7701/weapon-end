from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbstractWeaponeeringOption:
    id: str
    scenario_id: str
    option_label: str
    effect_category: str
    required_capability_band: str
    resource_token_type: str
    estimated_effect_score: int
    risk_score: int
    logistics_demand_score: int
    source_module: str
    review_status: str
    status: str


@dataclass(frozen=True)
class TargetWeaponeeringAssessment:
    id: str
    target_card_id: str
    abstract_weaponeering_option_id: str
    suitability_score: int
    feasibility_score: int
    risk_score: int
    rationale: str
    generated_by: str
    review_status: str


@dataclass(frozen=True)
class TargetDeploymentAircraftLine:
    id: str
    plan_id: str
    aircraft_id: str
    aircraft_count: int
    sort_order: int = 0


@dataclass(frozen=True)
class TargetDeploymentWaypoint:
    id: str
    plan_id: str
    waypoint_type: str
    label: str | None
    lat: float
    lng: float
    sort_order: int = 0
    altitude_ft: int | None = None


@dataclass(frozen=True)
class TargetDeploymentPlan:
    id: str
    scenario_id: str
    target_card_id: str
    wing_id: str
    flying_unit_id: str
    aircraft_lines: tuple[TargetDeploymentAircraftLine, ...]
    takeoff_lat: float | None = None
    takeoff_lng: float | None = None
    ingress_bearing_deg: float | None = None
    ingress_offset_m: int = 30000
    cruise_altitude_ft: int = 25000
    ingress_altitude_ft: int = 2000
    target_altitude_ft: int = 2000
    climb_rate_ft_min: int = 3000
    descent_rate_ft_min: int = 2000
    return_enabled: bool = True
    cruise_speed_kt: float = 420.0
    climb_speed_kt: float = 250.0
    descent_speed_kt: float = 300.0
    ingress_speed_kt: float = 250.0
    bank_angle_deg: float = 20.0
    turn_mode: str = "fly_by"
    auto_toc_tod: bool = True
    waypoints: tuple[TargetDeploymentWaypoint, ...] = ()
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def total_aircraft_count(self) -> int:
        return sum(line.aircraft_count for line in self.aircraft_lines)


@dataclass(frozen=True)
class ImportBatch:
    id: str
    scenario_id: str
    source_reference: str
    import_status: str
    validation_summary: str
    imported_count: int
    rejected_count: int
    created_by: str
    created_at: str | None = None
