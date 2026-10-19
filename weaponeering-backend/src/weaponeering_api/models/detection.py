from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from weaponeering_api.db import Base


class TargetMapDetectionRun(Base):
    __tablename__ = "target_map_detection_runs"
    __table_args__ = (
        UniqueConstraint("target_card_id", "target_coordinate_id", name="uq_detection_run_target_coord"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_coordinate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_coordinates.id", ondelete="CASCADE"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_file_name: Mapped[str | None] = mapped_column(String(255))
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    capture_radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    source_image_name: Mapped[str | None] = mapped_column(String(255))
    object_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detection_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    objects: Mapped[list[TargetMapDetectionObject]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class TargetMapDetectionObject(Base):
    __tablename__ = "target_map_detection_objects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("target_map_detection_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    map_object_id: Mapped[str] = mapped_column(String(128), nullable=False)
    object_label: Mapped[str] = mapped_column(String(255), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lng: Mapped[float] = mapped_column(Float, nullable=False)
    polygon_json: Mapped[list | dict] = mapped_column(JSONB, nullable=False, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    run: Mapped[TargetMapDetectionRun] = relationship(back_populates="objects")


class ScenarioTeamMarker(Base):
    __tablename__ = "scenario_team_markers"
    __table_args__ = (
        CheckConstraint("side IN ('blue', 'red')", name="ck_team_marker_side"),
        CheckConstraint(
            "unit_type IN ('generic', 'radar', 'tank', 'small_arms', 'artillery', 'anti_air')",
            name="ck_team_marker_unit_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(32), nullable=False, default="generic")
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    map_lat: Mapped[float] = mapped_column(Float, nullable=False)
    map_lng: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScenarioGroundTransport(Base):
    __tablename__ = "scenario_ground_transports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin_wing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False
    )
    destination_wing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wing_products.id", ondelete="SET NULL")
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wing_logistics_vehicles.id", ondelete="SET NULL")
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    duration_min: Mapped[float] = mapped_column(Float, nullable=False)
    route_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="direct")
    route_geometry_json: Mapped[list | dict | None] = mapped_column(JSONB)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
