from __future__ import annotations

from dataclasses import dataclass


EFFECT_CATEGORIES = (
    "abstract_disrupt",
    "abstract_delay",
    "abstract_deny",
    "abstract_support",
)


@dataclass(frozen=True)
class CreateAbstractOptionRequest:
    scenario_id: str
    option_label: str
    effect_category: str = "abstract_support"
    required_capability_band: str = "medium"
    resource_token_type: str = ""
    estimated_effect_score: int = 50
    risk_score: int = 50
    logistics_demand_score: int = 50


@dataclass(frozen=True)
class CreateAssessmentRequest:
    target_card_id: str
    abstract_weaponeering_option_id: str
    suitability_score: int
    feasibility_score: int
    risk_score: int
    rationale: str = ""


@dataclass(frozen=True)
class DeploymentAircraftLineRequest:
    aircraft_id: str
    aircraft_count: int = 1


@dataclass(frozen=True)
class DeploymentWaypointRequest:
    lat: float
    lng: float
    label: str = ""
    waypoint_type: str = "fly_through"
    altitude_ft: int | None = None


@dataclass(frozen=True)
class UpsertDeploymentPlanRequest:
    scenario_id: str
    target_card_id: str
    wing_id: str
    flying_unit_id: str
    aircraft_lines: tuple[DeploymentAircraftLineRequest, ...]
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
    waypoints: tuple[DeploymentWaypointRequest, ...] = ()
