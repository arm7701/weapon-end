from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from weaponeering_api.db import Base


class AbstractWeaponeeringOption(Base):
    __tablename__ = "abstract_weaponeering_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_label: Mapped[str] = mapped_column(String(255), nullable=False)
    effect_category: Mapped[str] = mapped_column(String(64), nullable=False, default="abstract_support")
    required_capability_band: Mapped[str] = mapped_column(String(64), nullable=False, default="medium")
    resource_token_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    estimated_effect_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    logistics_demand_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TargetWeaponeeringAssessment(Base):
    __tablename__ = "target_weaponeering_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    abstract_weaponeering_option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("abstract_weaponeering_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suitability_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    feasibility_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    generated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="user")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="requires_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WeaponeeringImportBatch(Base):
    __tablename__ = "weaponeering_import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    import_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    validation_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False, default="local_user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TargetDeploymentPlan(Base):
    __tablename__ = "target_weaponeering_deployment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    wing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False
    )
    flying_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wing_flying_units.id", ondelete="CASCADE"), nullable=False
    )
    takeoff_lat: Mapped[float | None] = mapped_column(Float)
    takeoff_lng: Mapped[float | None] = mapped_column(Float)
    ingress_bearing_deg: Mapped[float | None] = mapped_column(Float)
    ingress_offset_m: Mapped[int] = mapped_column(Integer, nullable=False, default=30000)
    cruise_altitude_ft: Mapped[int] = mapped_column(Integer, nullable=False, default=25000)
    ingress_altitude_ft: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    target_altitude_ft: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    climb_rate_ft_min: Mapped[int] = mapped_column(Integer, nullable=False, default=3000)
    descent_rate_ft_min: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    return_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cruise_speed_kt: Mapped[float] = mapped_column(Float, nullable=False, default=420.0)
    climb_speed_kt: Mapped[float] = mapped_column(Float, nullable=False, default=250.0)
    descent_speed_kt: Mapped[float] = mapped_column(Float, nullable=False, default=300.0)
    ingress_speed_kt: Mapped[float] = mapped_column(Float, nullable=False, default=250.0)
    bank_angle_deg: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)
    turn_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="fly_by")
    auto_toc_tod: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aircraft_lines: Mapped[list[DeploymentAircraftLine]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    waypoints: Mapped[list[DeploymentWaypoint]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class DeploymentAircraftLine(Base):
    __tablename__ = "target_weaponeering_deployment_aircraft"
    __table_args__ = (UniqueConstraint("plan_id", "aircraft_id", name="uq_deployment_plan_aircraft"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("target_weaponeering_deployment_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aircraft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wing_aircraft.id", ondelete="CASCADE"), nullable=False
    )
    aircraft_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped[TargetDeploymentPlan] = relationship(back_populates="aircraft_lines")


class DeploymentWaypoint(Base):
    __tablename__ = "target_weaponeering_deployment_waypoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("target_weaponeering_deployment_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    waypoint_type: Mapped[str] = mapped_column(String(32), nullable=False, default="fly_through")
    label: Mapped[str | None] = mapped_column(String(128))
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    altitude_ft: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped[TargetDeploymentPlan] = relationship(back_populates="waypoints")


# --- Ranking ---


class ScoringProfile(Base):
    __tablename__ = "scoring_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(64), nullable=False, default="phase-1-baseline")
    priority_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    weaponeering_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    logistics_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    readiness_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    risk_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    resource_balance_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RankingRun(Base):
    __tablename__ = "ranking_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ruleset_version: Mapped[str] = mapped_column(String(64), nullable=False, default="phase-1-baseline")
    scoring_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scoring_profiles.id", ondelete="SET NULL")
    )
    generated_by: Mapped[str] = mapped_column(String(128), nullable=False, default="local_user")
    run_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list[RankingItem]] = relationship(back_populates="ranking_run", cascade="all, delete-orphan")


class RankingItem(Base):
    __tablename__ = "ranking_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ranking_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ranking_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, default="target_card")
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="requires_review")
    override_rank_order: Mapped[int | None] = mapped_column(Integer)
    override_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ranking_run: Mapped[RankingRun] = relationship(back_populates="items")


# --- Plan options ---


class PlanOption(Base):
    __tablename__ = "plan_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    planning_horizon: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="user")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    rank_order: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanAssignment(Base):
    __tablename__ = "plan_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plan_options.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_card_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_cards.id", ondelete="SET NULL")
    )
    simulated_platform_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    abstract_weaponeering_option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("abstract_weaponeering_options.id", ondelete="SET NULL")
    )
    depot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    route_segment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    assigned_resource_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignment_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
