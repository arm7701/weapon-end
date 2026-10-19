"""phase 6 detection + map extras (team markers, ground transport)

Revision ID: 0006_phase6_detection
Revises: 0005_phase5_weaponeering
Create Date: 2026-07-26

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_phase6_detection"
down_revision: Union[str, Sequence[str], None] = "0005_phase5_weaponeering"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "target_map_detection_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_coordinate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_coordinates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_file_name", sa.String(255)),
        sa.Column("radius_m", sa.Integer(), nullable=False),
        sa.Column("capture_radius_m", sa.Integer(), nullable=False),
        sa.Column("source_image_name", sa.String(255)),
        sa.Column("object_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detection_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("target_card_id", "target_coordinate_id", name="uq_detection_run_target_coord"),
    )
    op.create_index("ix_target_map_detection_runs_scenario_id", "target_map_detection_runs", ["scenario_id"])
    op.create_index("ix_target_map_detection_runs_target_card_id", "target_map_detection_runs", ["target_card_id"])

    op.create_table(
        "target_map_detection_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_map_detection_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("map_object_id", sa.String(128), nullable=False),
        sa.Column("object_label", sa.String(255), nullable=False),
        sa.Column("object_type", sa.String(64), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("center_lat", sa.Float(), nullable=False),
        sa.Column("center_lng", sa.Float(), nullable=False),
        sa.Column("polygon_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_target_map_detection_objects_run_id", "target_map_detection_objects", ["run_id"])
    op.create_index("ix_target_map_detection_objects_target_card_id", "target_map_detection_objects", ["target_card_id"])

    op.create_table(
        "scenario_team_markers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("side", sa.String(16), nullable=False),
        sa.Column("unit_type", sa.String(32), nullable=False, server_default="generic"),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("map_lat", sa.Float(), nullable=False),
        sa.Column("map_lng", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("side IN ('blue', 'red')", name="ck_team_marker_side"),
        sa.CheckConstraint(
            "unit_type IN ('generic', 'radar', 'tank', 'small_arms', 'artillery', 'anti_air')",
            name="ck_team_marker_unit_type",
        ),
    )
    op.create_index("ix_scenario_team_markers_scenario_id", "scenario_team_markers", ["scenario_id"])

    op.create_table(
        "scenario_ground_transports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("origin_wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_products.id", ondelete="SET NULL")),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_logistics_vehicles.id", ondelete="SET NULL")),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("distance_m", sa.Float(), nullable=False),
        sa.Column("duration_min", sa.Float(), nullable=False),
        sa.Column("route_mode", sa.String(32), nullable=False, server_default="direct"),
        sa.Column("route_geometry_json", postgresql.JSONB()),
        sa.Column("label", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_scenario_ground_transports_scenario_id", "scenario_ground_transports", ["scenario_id"])


def downgrade() -> None:
    op.drop_index("ix_scenario_ground_transports_scenario_id", table_name="scenario_ground_transports")
    op.drop_table("scenario_ground_transports")
    op.drop_index("ix_scenario_team_markers_scenario_id", table_name="scenario_team_markers")
    op.drop_table("scenario_team_markers")
    op.drop_index("ix_target_map_detection_objects_target_card_id", table_name="target_map_detection_objects")
    op.drop_index("ix_target_map_detection_objects_run_id", table_name="target_map_detection_objects")
    op.drop_table("target_map_detection_objects")
    op.drop_index("ix_target_map_detection_runs_target_card_id", table_name="target_map_detection_runs")
    op.drop_index("ix_target_map_detection_runs_scenario_id", table_name="target_map_detection_runs")
    op.drop_table("target_map_detection_runs")
