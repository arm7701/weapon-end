"""phase 3 assets / logistics tables

Revision ID: 0003_phase3_logistics
Revises: 0002_phase2_targets
Create Date: 2026-07-17

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase3_logistics"
down_revision: Union[str, Sequence[str], None] = "0002_phase2_targets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organization_type", sa.String(64), nullable=False, server_default="unit"),
        sa.Column("map_lat", sa.Float()),
        sa.Column("map_lng", sa.Float()),
        sa.Column("location_label", sa.String(255), nullable=False, server_default=""),
        sa.Column("is_synthetic_location", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("readiness_summary", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_organizations_scenario_id", "organizations", ["scenario_id"])

    op.create_table(
        "platform_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("capability_band", sa.String(64), nullable=False, server_default="medium"),
        sa.Column("resource_cost_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("support_need_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_platform_types_scenario_id", "platform_types", ["scenario_id"])

    op.create_table(
        "simulated_platforms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("platform_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platform_types.id", ondelete="SET NULL")),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("capability_band", sa.String(64), nullable=False, server_default="medium"),
        sa.Column("availability_score", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("readiness_status", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("readiness_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_simulated_platforms_scenario_id", "simulated_platforms", ["scenario_id"])

    op.create_table(
        "platform_readiness_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("simulated_platform_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulated_platforms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("readiness_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_platform_readiness_events_platform_id", "platform_readiness_events", ["simulated_platform_id"])

    op.create_table(
        "depots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("depot_type", sa.String(64), nullable=False, server_default="abstract_store"),
        sa.Column("map_lat", sa.Float()),
        sa.Column("map_lng", sa.Float()),
        sa.Column("capacity_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("availability_status", sa.String(64), nullable=False, server_default="available"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_depots_scenario_id", "depots", ["scenario_id"])

    op.create_table(
        "resource_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_type", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("availability_window", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_resource_tokens_scenario_id", "resource_tokens", ["scenario_id"])

    op.create_table(
        "depot_inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("depot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("depots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_token_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resource_tokens.id", ondelete="SET NULL")),
        sa.Column("inventory_category", sa.String(64), nullable=False, server_default="support_token"),
        sa.Column("option_label", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("availability_status", sa.String(64), nullable=False, server_default="available"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_depot_inventory_depot_id", "depot_inventory", ["depot_id"])

    op.create_table(
        "transport_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("transport_type", sa.String(64), nullable=False, server_default="ground"),
        sa.Column("capacity_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("readiness_status", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_transport_assets_scenario_id", "transport_assets", ["scenario_id"])

    op.create_table(
        "route_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("origin_entity_type", sa.String(64), nullable=False),
        sa.Column("origin_entity_id", sa.String(64), nullable=False),
        sa.Column("destination_entity_type", sa.String(64), nullable=False),
        sa.Column("destination_entity_id", sa.String(64), nullable=False),
        sa.Column("origin_lat", sa.Float()),
        sa.Column("origin_lng", sa.Float()),
        sa.Column("destination_lat", sa.Float()),
        sa.Column("destination_lng", sa.Float()),
        sa.Column("distance_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("fuel_stop_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("route_friction_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("availability_status", sa.String(64), nullable=False, server_default="available"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_route_segments_scenario_id", "route_segments", ["scenario_id"])

    op.create_table(
        "plan_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("route_segments.id", ondelete="SET NULL")),
        sa.Column("plan_option_id", sa.String(64)),
        sa.Column("priority_alignment", sa.Integer()),
        sa.Column("logistics_feasibility", sa.Integer(), nullable=False),
        sa.Column("resource_balance", sa.Integer()),
        sa.Column("risk_indicator", sa.Integer()),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_plan_scores_scenario_id", "plan_scores", ["scenario_id"])


def downgrade() -> None:
    op.drop_index("ix_plan_scores_scenario_id", table_name="plan_scores")
    op.drop_table("plan_scores")
    op.drop_index("ix_route_segments_scenario_id", table_name="route_segments")
    op.drop_table("route_segments")
    op.drop_index("ix_transport_assets_scenario_id", table_name="transport_assets")
    op.drop_table("transport_assets")
    op.drop_index("ix_depot_inventory_depot_id", table_name="depot_inventory")
    op.drop_table("depot_inventory")
    op.drop_index("ix_resource_tokens_scenario_id", table_name="resource_tokens")
    op.drop_table("resource_tokens")
    op.drop_index("ix_depots_scenario_id", table_name="depots")
    op.drop_table("depots")
    op.drop_index("ix_platform_readiness_events_platform_id", table_name="platform_readiness_events")
    op.drop_table("platform_readiness_events")
    op.drop_index("ix_simulated_platforms_scenario_id", table_name="simulated_platforms")
    op.drop_table("simulated_platforms")
    op.drop_index("ix_platform_types_scenario_id", table_name="platform_types")
    op.drop_table("platform_types")
    op.drop_index("ix_organizations_scenario_id", table_name="organizations")
    op.drop_table("organizations")
