from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Weaponeering options ---


class WeaponeeringOptionCreate(BaseModel):
    scenario_id: UUID
    option_label: str = Field(..., min_length=1, max_length=255)
    effect_category: str = "abstract_support"
    required_capability_band: str = "medium"
    resource_token_type: str = ""
    estimated_effect_score: int = Field(default=50, ge=0, le=100)
    risk_score: int = Field(default=50, ge=0, le=100)
    logistics_demand_score: int = Field(default=50, ge=0, le=100)
    source_module: str = "manual"
    review_status: str = "draft"
    status: str = "active"


class WeaponeeringOptionUpdate(BaseModel):
    option_label: str | None = Field(default=None, min_length=1, max_length=255)
    effect_category: str | None = None
    required_capability_band: str | None = None
    resource_token_type: str | None = None
    estimated_effect_score: int | None = Field(default=None, ge=0, le=100)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    logistics_demand_score: int | None = Field(default=None, ge=0, le=100)
    source_module: str | None = None
    review_status: str | None = None
    status: str | None = None


class WeaponeeringOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
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
    created_at: datetime
    updated_at: datetime


# --- Assessments ---


class AssessmentCreate(BaseModel):
    target_card_id: UUID
    abstract_weaponeering_option_id: UUID
    suitability_score: int = Field(default=50, ge=0, le=100)
    feasibility_score: int = Field(default=50, ge=0, le=100)
    risk_score: int = Field(default=50, ge=0, le=100)
    rationale: str = ""
    generated_by: str = "user"
    review_status: str = "requires_review"


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_card_id: UUID
    abstract_weaponeering_option_id: UUID
    suitability_score: int
    feasibility_score: int
    risk_score: int
    rationale: str
    generated_by: str
    review_status: str
    created_at: datetime
    updated_at: datetime


# --- Deployment plans ---


class DeploymentAircraftLineIn(BaseModel):
    aircraft_id: UUID
    aircraft_count: int = Field(default=1, ge=1)


class DeploymentAircraftLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    aircraft_id: UUID
    aircraft_count: int
    sort_order: int
    created_at: datetime


class DeploymentWaypointIn(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    label: str | None = None
    waypoint_type: str = "fly_through"
    altitude_ft: int | None = None


class DeploymentWaypointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    waypoint_type: str
    label: str | None = None
    lat: float
    lng: float
    sort_order: int
    altitude_ft: int | None = None
    created_at: datetime


class DeploymentPlanUpsert(BaseModel):
    scenario_id: UUID
    target_card_id: UUID
    wing_id: UUID
    flying_unit_id: UUID
    aircraft_lines: list[DeploymentAircraftLineIn] = Field(default_factory=list)
    takeoff_lat: float | None = Field(default=None, ge=-90, le=90)
    takeoff_lng: float | None = Field(default=None, ge=-180, le=180)
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
    waypoints: list[DeploymentWaypointIn] = Field(default_factory=list)


class DeploymentPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    target_card_id: UUID
    wing_id: UUID
    flying_unit_id: UUID
    takeoff_lat: float | None = None
    takeoff_lng: float | None = None
    ingress_bearing_deg: float | None = None
    ingress_offset_m: int
    cruise_altitude_ft: int
    ingress_altitude_ft: int
    target_altitude_ft: int
    climb_rate_ft_min: int
    descent_rate_ft_min: int
    return_enabled: bool
    cruise_speed_kt: float
    climb_speed_kt: float
    descent_speed_kt: float
    ingress_speed_kt: float
    bank_angle_deg: float
    turn_mode: str
    auto_toc_tod: bool
    aircraft_lines: list[DeploymentAircraftLineOut] = Field(default_factory=list)
    waypoints: list[DeploymentWaypointOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --- Scoring profiles ---


class ScoringProfileCreate(BaseModel):
    scenario_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    priority_weight: int = Field(default=20, ge=0, le=100)
    weaponeering_weight: int = Field(default=20, ge=0, le=100)
    logistics_weight: int = Field(default=20, ge=0, le=100)
    readiness_weight: int = Field(default=15, ge=0, le=100)
    risk_weight: int = Field(default=15, ge=0, le=100)
    resource_balance_weight: int = Field(default=10, ge=0, le=100)
    is_active: bool = False


class ScoringProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    priority_weight: int | None = Field(default=None, ge=0, le=100)
    weaponeering_weight: int | None = Field(default=None, ge=0, le=100)
    logistics_weight: int | None = Field(default=None, ge=0, le=100)
    readiness_weight: int | None = Field(default=None, ge=0, le=100)
    risk_weight: int | None = Field(default=None, ge=0, le=100)
    resource_balance_weight: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class ScoringProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    name: str
    ruleset_version: str
    priority_weight: int
    weaponeering_weight: int
    logistics_weight: int
    readiness_weight: int
    risk_weight: int
    resource_balance_weight: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Ranking runs / items ---


class RankingRunCreate(BaseModel):
    scenario_id: UUID
    scoring_profile_id: UUID | None = None
    ruleset_version: str = "phase-1-baseline"


class RankingRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    ruleset_version: str
    scoring_profile_id: UUID | None = None
    generated_by: str
    run_status: str
    summary: str
    created_at: datetime


class RankingItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ranking_run_id: UUID
    entity_type: str
    entity_id: str
    rank_order: int
    total_score: int
    confidence_score: int
    rationale: str
    breakdown_json: dict = Field(default_factory=dict)
    review_status: str
    override_rank_order: int | None = None
    override_notes: str
    created_at: datetime


class RankingItemOverride(BaseModel):
    new_rank_order: int = Field(..., ge=1)
    notes: str = ""


class RankingRunDetailOut(BaseModel):
    run: RankingRunOut
    items: list[RankingItemOut] = Field(default_factory=list)


# --- Plan options ---


class PlanOptionCreate(BaseModel):
    scenario_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    planning_horizon: str = ""
    generated_by: str = "user"
    review_status: str = "draft"
    rank_order: int | None = None


class PlanOptionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    planning_horizon: str | None = None
    review_status: str | None = None
    rank_order: int | None = None


class PlanOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scenario_id: UUID
    planning_horizon: str
    title: str
    generated_by: str
    review_status: str
    rank_order: int | None = None
    created_at: datetime


# --- Plan assignments ---


class PlanAssignmentCreate(BaseModel):
    plan_option_id: UUID
    target_card_id: UUID | None = None
    simulated_platform_id: UUID | None = None
    abstract_weaponeering_option_id: UUID | None = None
    depot_id: UUID | None = None
    route_segment_id: UUID | None = None
    assigned_resource_quantity: int = Field(default=0, ge=0)
    assignment_score: int = Field(default=50, ge=0, le=100)
    review_status: str = "draft"


class PlanAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_option_id: UUID
    target_card_id: UUID | None = None
    simulated_platform_id: UUID | None = None
    abstract_weaponeering_option_id: UUID | None = None
    depot_id: UUID | None = None
    route_segment_id: UUID | None = None
    assigned_resource_quantity: int
    assignment_score: int
    review_status: str
    created_at: datetime
