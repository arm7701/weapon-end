"""phase 2 target tables

Revision ID: 0002_phase2_targets
Revises: 0001_phase0
Create Date: 2026-07-16

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2_targets"
down_revision: Union[str, Sequence[str], None] = "0001_phase0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("map_nodes", sa.Column("linked_entity_type", sa.String(length=64)))
    op.add_column("map_nodes", sa.Column("linked_entity_id", sa.String(length=64)))
    op.add_column(
        "map_nodes",
        sa.Column("is_synthetic_location", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "target_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("complexity_score", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("map_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("map_nodes.id", ondelete="SET NULL")),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("target_type", sa.String(length=64), nullable=False, server_default="BUILDING"),
        sa.Column("target_subtype", sa.String(length=128), nullable=False, server_default="UNKNOWN"),
        sa.Column("material_class", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
        sa.Column("target_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("floor_count", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("width_m", sa.Float()),
        sa.Column("length_m", sa.Float()),
        sa.Column("height_m", sa.Float()),
        sa.Column("desired_model_result", sa.String(length=128), nullable=False, server_default="STRUCTURAL FAILURE"),
        sa.Column("coordinate_error_m", sa.Float()),
        sa.Column("data_source", sa.String(length=64), nullable=False, server_default="manual"),
        sa.Column("cep", sa.Float()),
        sa.Column("target_pk", sa.Float()),
        sa.Column("reference_pk", sa.Float()),
        sa.Column("resistance", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("capacity", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("damage_fit", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("model_version", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("selected_product_id", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_target_cards_scenario_id", "target_cards", ["scenario_id"])

    op.create_table(
        "target_coordinates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("map_lat", sa.Float(), nullable=False),
        sa.Column("map_lng", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("selected_product_id", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_target_coordinates_target_card_id", "target_coordinates", ["target_card_id"])
    op.create_index(
        "ix_target_coordinates_card_sort",
        "target_coordinates",
        ["target_card_id", "sort_order"],
    )

    op.create_table(
        "target_recognition_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("target_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False, server_default="manual"),
        sa.Column("recognition_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("recognition_confidence_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column(
            "missing_data_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("generated_by", sa.String(length=64), nullable=False, server_default="user"),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="requires_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_target_recognition_results_target_card_id", "target_recognition_results", ["target_card_id"])

    op.create_table(
        "human_review_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_human_review_records_scenario_id", "human_review_records", ["scenario_id"])


def downgrade() -> None:
    op.drop_index("ix_human_review_records_scenario_id", table_name="human_review_records")
    op.drop_table("human_review_records")
    op.drop_index("ix_target_recognition_results_target_card_id", table_name="target_recognition_results")
    op.drop_table("target_recognition_results")
    op.drop_index("ix_target_coordinates_card_sort", table_name="target_coordinates")
    op.drop_index("ix_target_coordinates_target_card_id", table_name="target_coordinates")
    op.drop_table("target_coordinates")
    op.drop_index("ix_target_cards_scenario_id", table_name="target_cards")
    op.drop_table("target_cards")
    op.drop_column("map_nodes", "is_synthetic_location")
    op.drop_column("map_nodes", "linked_entity_id")
    op.drop_column("map_nodes", "linked_entity_type")
