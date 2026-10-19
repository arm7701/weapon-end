from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from weaponeering_api.db import Base


class TargetCard(Base):
    __tablename__ = "target_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    complexity_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    map_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("map_nodes.id", ondelete="SET NULL"),
    )
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    # profile fields (desktop phase 12+)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False, default="BUILDING")
    target_subtype: Mapped[str] = mapped_column(String(128), nullable=False, default="UNKNOWN")
    material_class: Mapped[str] = mapped_column(String(64), nullable=False, default="UNKNOWN")
    material_strength: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    target_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    floor_count: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    width_m: Mapped[float | None] = mapped_column(Float)
    length_m: Mapped[float | None] = mapped_column(Float)
    height_m: Mapped[float | None] = mapped_column(Float)
    heading_deg: Mapped[float | None] = mapped_column(Float)
    desired_model_result: Mapped[str] = mapped_column(String(128), nullable=False, default="STRUCTURAL FAILURE")
    coordinate_error_m: Mapped[float | None] = mapped_column(Float)
    data_source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    cep: Mapped[float | None] = mapped_column(Float)
    target_pk: Mapped[float | None] = mapped_column(Float)
    reference_pk: Mapped[float | None] = mapped_column(Float)
    resistance: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    capacity: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    damage_fit: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    selected_product_id: Mapped[str | None] = mapped_column(String(64))
    weapon_quantity: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    map_node: Mapped[object | None] = relationship("MapNode", back_populates="target_cards")
    coordinates: Mapped[list[TargetCoordinate]] = relationship(
        back_populates="target_card",
        cascade="all, delete-orphan",
        order_by="TargetCoordinate.sort_order",
    )
    recognition_results: Mapped[list[TargetRecognitionResult]] = relationship(
        back_populates="target_card",
        cascade="all, delete-orphan",
    )


class TargetCoordinate(Base):
    __tablename__ = "target_coordinates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("target_cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    map_lat: Mapped[float] = mapped_column(Float, nullable=False)
    map_lng: Mapped[float] = mapped_column(Float, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selected_product_id: Mapped[str | None] = mapped_column(String(64))
    weapon_quantity: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    target_card: Mapped[TargetCard] = relationship(back_populates="coordinates")


class TargetRecognitionResult(Base):
    __tablename__ = "target_recognition_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("target_cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    recognition_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recognition_confidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    missing_data_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    generated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="user")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="requires_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    target_card: Mapped[TargetCard] = relationship(back_populates="recognition_results")


class HumanReviewRecord(Base):
    __tablename__ = "human_review_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
