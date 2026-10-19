from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from weaponeering_api.db import Base

# re-export target models so Alembic / imports see them
from weaponeering_api.models.target import (  # noqa: E402
    HumanReviewRecord,
    TargetCard,
    TargetCoordinate,
    TargetRecognitionResult,
)
from weaponeering_api.models.logistics import (  # noqa: E402
    Depot,
    DepotInventoryItem,
    Organization,
    PlanScore,
    PlatformReadinessEvent,
    PlatformType,
    ResourceToken,
    RouteSegment,
    SimulatedPlatform,
    TransportAsset,
)
from weaponeering_api.models.wing import (  # noqa: E402
    AirWing,
    WingAircraft,
    WingDepot,
    WingDepotInventory,
    WingDepotTransfer,
    WingFlyingUnit,
    WingLogisticsVehicle,
    WingPilot,
    WingProduct,
)
from weaponeering_api.models.weaponeering import (  # noqa: E402
    AbstractWeaponeeringOption,
    DeploymentAircraftLine,
    DeploymentWaypoint,
    PlanAssignment,
    PlanOption,
    RankingItem,
    RankingRun,
    ScoringProfile,
    TargetDeploymentPlan,
    TargetWeaponeeringAssessment,
    WeaponeeringImportBatch,
)
from weaponeering_api.models.detection import (  # noqa: E402
    ScenarioGroundTransport,
    ScenarioTeamMarker,
    TargetMapDetectionObject,
    TargetMapDetectionRun,
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    user_name: Mapped[str | None] = mapped_column(String(255))
    rank: Mapped[str | None] = mapped_column(String(64))
    rank_id: Mapped[str | None] = mapped_column(String(32))
    fname: Mapped[str | None] = mapped_column(String(128))
    lname: Mapped[str | None] = mapped_column(String(128))
    user_position: Mapped[str | None] = mapped_column(String(512))
    user_orgname: Mapped[str | None] = mapped_column(String(255))
    user_orgname_code: Mapped[str | None] = mapped_column(String(64))
    user_role: Mapped[str | None] = mapped_column(String(64))
    profile_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    sessions: Mapped[list[AuthSession]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    challenge: Mapped[str | None] = mapped_column(String(255))
    login_mode: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="sessions")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    ruleset_version: Mapped[str] = mapped_column(String(64), nullable=False, default="phase-0-web")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    learning_objectives: Mapped[list[LearningObjective]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
    )
    map_nodes: Mapped[list[MapNode]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
    )


class LearningObjective(Base):
    __tablename__ = "learning_objectives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    scenario: Mapped[Scenario] = relationship(back_populates="learning_objectives")


class MapNode(Base):
    __tablename__ = "map_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False, default="synthetic_node")
    map_lat: Mapped[float] = mapped_column(Float, nullable=False)
    map_lng: Mapped[float] = mapped_column(Float, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    linked_entity_type: Mapped[str | None] = mapped_column(String(64))
    linked_entity_id: Mapped[str | None] = mapped_column(String(64))
    is_synthetic_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    scenario: Mapped[Scenario] = relationship(back_populates="map_nodes")
    target_cards: Mapped[list[TargetCard]] = relationship(back_populates="map_node")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GuardrailEvent(Base):
    __tablename__ = "guardrail_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    sanitized_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
