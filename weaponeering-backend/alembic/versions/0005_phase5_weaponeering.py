"""phase 5 weaponeering + ranking + deployment + plan options

Revision ID: 0005_phase5_weaponeering
Revises: 0004_phase4_wing
Create Date: 2026-07-17

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_phase5_weaponeering"
down_revision: Union[str, Sequence[str], None] = "0004_phase4_wing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "abstract_weaponeering_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_label", sa.String(255), nullable=False),
        sa.Column("effect_category", sa.String(64), nullable=False, server_default="abstract_support"),
        sa.Column("required_capability_band", sa.String(64), nullable=False, server_default="medium"),
        sa.Column("resource_token_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("estimated_effect_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("logistics_demand_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("source_module", sa.String(64), nullable=False, server_default="manual"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_abstract_weaponeering_options_scenario_id", "abstract_weaponeering_options", ["scenario_id"])

    op.create_table(
        "target_weaponeering_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("abstract_weaponeering_option_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("abstract_weaponeering_options.id", ondelete="CASCADE"), nullable=False),
        sa.Column("suitability_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("feasibility_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("generated_by", sa.String(64), nullable=False, server_default="user"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="requires_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_target_weaponeering_assessments_target", "target_weaponeering_assessments", ["target_card_id"])
    op.create_index("ix_target_weaponeering_assessments_option", "target_weaponeering_assessments", ["abstract_weaponeering_option_id"])

    op.create_table(
        "weaponeering_import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_reference", sa.String(255), nullable=False, server_default=""),
        sa.Column("import_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("validation_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(128), nullable=False, server_default="local_user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_weaponeering_import_batches_scenario_id", "weaponeering_import_batches", ["scenario_id"])

    op.create_table(
        "target_weaponeering_deployment_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("flying_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_flying_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("takeoff_lat", sa.Float()),
        sa.Column("takeoff_lng", sa.Float()),
        sa.Column("ingress_bearing_deg", sa.Float()),
        sa.Column("ingress_offset_m", sa.Integer(), nullable=False, server_default="30000"),
        sa.Column("cruise_altitude_ft", sa.Integer(), nullable=False, server_default="25000"),
        sa.Column("ingress_altitude_ft", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("target_altitude_ft", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("climb_rate_ft_min", sa.Integer(), nullable=False, server_default="3000"),
        sa.Column("descent_rate_ft_min", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("return_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("cruise_speed_kt", sa.Float(), nullable=False, server_default="420"),
        sa.Column("climb_speed_kt", sa.Float(), nullable=False, server_default="250"),
        sa.Column("descent_speed_kt", sa.Float(), nullable=False, server_default="300"),
        sa.Column("ingress_speed_kt", sa.Float(), nullable=False, server_default="250"),
        sa.Column("bank_angle_deg", sa.Float(), nullable=False, server_default="20"),
        sa.Column("turn_mode", sa.String(32), nullable=False, server_default="fly_by"),
        sa.Column("auto_toc_tod", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_deployment_plans_scenario_id", "target_weaponeering_deployment_plans", ["scenario_id"])

    op.create_table(
        "target_weaponeering_deployment_aircraft",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_weaponeering_deployment_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("aircraft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_aircraft.id", ondelete="CASCADE"), nullable=False),
        sa.Column("aircraft_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("plan_id", "aircraft_id", name="uq_deployment_plan_aircraft"),
    )
    op.create_index("ix_deployment_aircraft_plan_id", "target_weaponeering_deployment_aircraft", ["plan_id"])

    op.create_table(
        "target_weaponeering_deployment_waypoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_weaponeering_deployment_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("waypoint_type", sa.String(32), nullable=False, server_default="fly_through"),
        sa.Column("label", sa.String(128)),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("altitude_ft", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_deployment_waypoints_plan_id", "target_weaponeering_deployment_waypoints", ["plan_id"])

    op.create_table(
        "scoring_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("ruleset_version", sa.String(64), nullable=False, server_default="phase-1-baseline"),
        sa.Column("priority_weight", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("weaponeering_weight", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("logistics_weight", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("readiness_weight", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("risk_weight", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("resource_balance_weight", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_scoring_profiles_scenario_id", "scoring_profiles", ["scenario_id"])

    op.create_table(
        "ranking_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ruleset_version", sa.String(64), nullable=False, server_default="phase-1-baseline"),
        sa.Column("scoring_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scoring_profiles.id", ondelete="SET NULL")),
        sa.Column("generated_by", sa.String(128), nullable=False, server_default="local_user"),
        sa.Column("run_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ranking_runs_scenario_id", "ranking_runs", ["scenario_id"])

    op.create_table(
        "ranking_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ranking_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ranking_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False, server_default="target_card"),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("breakdown_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="requires_review"),
        sa.Column("override_rank_order", sa.Integer()),
        sa.Column("override_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ranking_items_run_id", "ranking_items", ["ranking_run_id"])

    op.create_table(
        "plan_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("planning_horizon", sa.String(64), nullable=False, server_default=""),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("generated_by", sa.String(64), nullable=False, server_default="user"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("rank_order", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_plan_options_scenario_id", "plan_options", ["scenario_id"])

    op.create_table(
        "plan_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("plan_option_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plan_options.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="SET NULL")),
        sa.Column("simulated_platform_id", postgresql.UUID(as_uuid=True)),
        sa.Column("abstract_weaponeering_option_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("abstract_weaponeering_options.id", ondelete="SET NULL")),
        sa.Column("depot_id", postgresql.UUID(as_uuid=True)),
        sa.Column("route_segment_id", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_resource_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assignment_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_plan_assignments_plan_option_id", "plan_assignments", ["plan_option_id"])


def downgrade() -> None:
    op.drop_index("ix_plan_assignments_plan_option_id", table_name="plan_assignments")
    op.drop_table("plan_assignments")
    op.drop_index("ix_plan_options_scenario_id", table_name="plan_options")
    op.drop_table("plan_options")
    op.drop_index("ix_ranking_items_run_id", table_name="ranking_items")
    op.drop_table("ranking_items")
    op.drop_index("ix_ranking_runs_scenario_id", table_name="ranking_runs")
    op.drop_table("ranking_runs")
    op.drop_index("ix_scoring_profiles_scenario_id", table_name="scoring_profiles")
    op.drop_table("scoring_profiles")
    op.drop_index("ix_deployment_waypoints_plan_id", table_name="target_weaponeering_deployment_waypoints")
    op.drop_table("target_weaponeering_deployment_waypoints")
    op.drop_index("ix_deployment_aircraft_plan_id", table_name="target_weaponeering_deployment_aircraft")
    op.drop_table("target_weaponeering_deployment_aircraft")
    op.drop_index("ix_deployment_plans_scenario_id", table_name="target_weaponeering_deployment_plans")
    op.drop_table("target_weaponeering_deployment_plans")
    op.drop_index("ix_weaponeering_import_batches_scenario_id", table_name="weaponeering_import_batches")
    op.drop_table("weaponeering_import_batches")
    op.drop_index("ix_target_weaponeering_assessments_option", table_name="target_weaponeering_assessments")
    op.drop_index("ix_target_weaponeering_assessments_target", table_name="target_weaponeering_assessments")
    op.drop_table("target_weaponeering_assessments")
    op.drop_index("ix_abstract_weaponeering_options_scenario_id", table_name="abstract_weaponeering_options")
    op.drop_table("abstract_weaponeering_options")
