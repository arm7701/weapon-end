from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from weaponeering_api.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[str] = mapped_column(String(64), nullable=False, default="unit")
    map_lat: Mapped[float | None] = mapped_column(Float)
    map_lng: Mapped[float | None] = mapped_column(Float)
    location_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_synthetic_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    readiness_summary: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlatformType(Base):
    __tablename__ = "platform_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    capability_band: Mapped[str] = mapped_column(String(64), nullable=False, default="medium")
    resource_cost_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    support_need_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SimulatedPlatform(Base):
    __tablename__ = "simulated_platforms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    platform_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_types.id", ondelete="SET NULL")
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    capability_band: Mapped[str] = mapped_column(String(64), nullable=False, default="medium")
    availability_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    readiness_status: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    readiness_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    readiness_events: Mapped[list[PlatformReadinessEvent]] = relationship(
        back_populates="platform", cascade="all, delete-orphan"
    )


class PlatformReadinessEvent(Base):
    __tablename__ = "platform_readiness_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulated_platform_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulated_platforms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    platform: Mapped[SimulatedPlatform] = relationship(back_populates="readiness_events")


class Depot(Base):
    __tablename__ = "depots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    depot_type: Mapped[str] = mapped_column(String(64), nullable=False, default="abstract_store")
    map_lat: Mapped[float | None] = mapped_column(Float)
    map_lng: Mapped[float | None] = mapped_column(Float)
    capacity_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    availability_status: Mapped[str] = mapped_column(String(64), nullable=False, default="available")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    inventory_items: Mapped[list[DepotInventoryItem]] = relationship(
        back_populates="depot", cascade="all, delete-orphan"
    )


class ResourceToken(Base):
    __tablename__ = "resource_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_type: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    availability_window: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DepotInventoryItem(Base):
    __tablename__ = "depot_inventory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    depot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("depots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_token_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resource_tokens.id", ondelete="SET NULL")
    )
    inventory_category: Mapped[str] = mapped_column(String(64), nullable=False, default="support_token")
    option_label: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    availability_status: Mapped[str] = mapped_column(String(64), nullable=False, default="available")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    depot: Mapped[Depot] = relationship(back_populates="inventory_items")


class TransportAsset(Base):
    __tablename__ = "transport_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    transport_type: Mapped[str] = mapped_column(String(64), nullable=False, default="ground")
    capacity_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    readiness_status: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RouteSegment(Base):
    __tablename__ = "route_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    destination_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    destination_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_lat: Mapped[float | None] = mapped_column(Float)
    origin_lng: Mapped[float | None] = mapped_column(Float)
    destination_lat: Mapped[float | None] = mapped_column(Float)
    destination_lng: Mapped[float | None] = mapped_column(Float)
    distance_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    fuel_stop_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    route_friction_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    availability_status: Mapped[str] = mapped_column(String(64), nullable=False, default="available")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlanScore(Base):
    __tablename__ = "plan_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    route_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_segments.id", ondelete="SET NULL")
    )
    # soft ref — plan_options มาใน Phase 4
    plan_option_id: Mapped[str | None] = mapped_column(String(64))
    priority_alignment: Mapped[int | None] = mapped_column(Integer)
    logistics_feasibility: Mapped[int] = mapped_column(Integer, nullable=False)
    resource_balance: Mapped[int | None] = mapped_column(Integer)
    risk_indicator: Mapped[int | None] = mapped_column(Integer)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
