"""phase 4 wing database

Revision ID: 0004_phase4_wing
Revises: 0003_phase3_logistics
Create Date: 2026-07-17

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase4_wing"
down_revision: Union[str, Sequence[str], None] = "0003_phase3_logistics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "air_wings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wing_name", sa.String(255), nullable=False),
        sa.Column("map_lat", sa.Float()),
        sa.Column("map_lng", sa.Float()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_air_wings_scenario_id", "air_wings", ["scenario_id"])

    op.create_table(
        "wing_flying_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_flying_units_scenario_id", "wing_flying_units", ["scenario_id"])
    op.create_index("ix_wing_flying_units_wing_id", "wing_flying_units", ["wing_id"])

    op.create_table(
        "wing_aircraft",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("flying_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_flying_units.id", ondelete="SET NULL")),
        sa.Column("aircraft_type", sa.String(128), nullable=False, server_default="F-16"),
        sa.Column("mission_ready", sa.String(32), nullable=False, server_default="not_ready"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_aircraft_scenario_id", "wing_aircraft", ["scenario_id"])
    op.create_index("ix_wing_aircraft_wing_id", "wing_aircraft", ["wing_id"])

    op.create_table(
        "wing_pilots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="SET NULL")),
        sa.Column("flying_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_flying_units.id", ondelete="SET NULL")),
        sa.Column("pilot_name", sa.String(255), nullable=False),
        sa.Column("callsign", sa.String(128), nullable=False, server_default=""),
        sa.Column("cep_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_pilots_scenario_id", "wing_pilots", ["scenario_id"])
    op.create_index("ix_wing_pilots_wing_id", "wing_pilots", ["wing_id"])

    op.create_table(
        "wing_depots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("depot_name", sa.String(255), nullable=False),
        sa.Column("map_lat", sa.Float()),
        sa.Column("map_lng", sa.Float()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_depots_scenario_id", "wing_depots", ["scenario_id"])
    op.create_index("ix_wing_depots_wing_id", "wing_depots", ["wing_id"])

    op.create_table(
        "wing_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("weight_pounds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_products_scenario_id", "wing_products", ["scenario_id"])

    op.create_table(
        "wing_depot_inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("depot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_depots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("depot_id", "product_id", name="uq_wing_depot_product"),
    )
    op.create_index("ix_wing_depot_inventory_scenario_id", "wing_depot_inventory", ["scenario_id"])
    op.create_index("ix_wing_depot_inventory_depot_id", "wing_depot_inventory", ["depot_id"])
    op.create_index("ix_wing_depot_inventory_product_id", "wing_depot_inventory", ["product_id"])

    op.create_table(
        "wing_depot_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_depot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_depots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_depot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wing_depots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_depot_transfers_scenario_id", "wing_depot_transfers", ["scenario_id"])

    op.create_table(
        "wing_logistics_vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("air_wings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_name", sa.String(255), nullable=False),
        sa.Column("fuel_consumption_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mission_ready", sa.String(32), nullable=False, server_default="not_ready"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wing_logistics_vehicles_scenario_id", "wing_logistics_vehicles", ["scenario_id"])
    op.create_index("ix_wing_logistics_vehicles_wing_id", "wing_logistics_vehicles", ["wing_id"])


def downgrade() -> None:
    op.drop_index("ix_wing_logistics_vehicles_wing_id", table_name="wing_logistics_vehicles")
    op.drop_index("ix_wing_logistics_vehicles_scenario_id", table_name="wing_logistics_vehicles")
    op.drop_table("wing_logistics_vehicles")
    op.drop_index("ix_wing_depot_transfers_scenario_id", table_name="wing_depot_transfers")
    op.drop_table("wing_depot_transfers")
    op.drop_index("ix_wing_depot_inventory_product_id", table_name="wing_depot_inventory")
    op.drop_index("ix_wing_depot_inventory_depot_id", table_name="wing_depot_inventory")
    op.drop_index("ix_wing_depot_inventory_scenario_id", table_name="wing_depot_inventory")
    op.drop_table("wing_depot_inventory")
    op.drop_index("ix_wing_products_scenario_id", table_name="wing_products")
    op.drop_table("wing_products")
    op.drop_index("ix_wing_depots_wing_id", table_name="wing_depots")
    op.drop_index("ix_wing_depots_scenario_id", table_name="wing_depots")
    op.drop_table("wing_depots")
    op.drop_index("ix_wing_pilots_wing_id", table_name="wing_pilots")
    op.drop_index("ix_wing_pilots_scenario_id", table_name="wing_pilots")
    op.drop_table("wing_pilots")
    op.drop_index("ix_wing_aircraft_wing_id", table_name="wing_aircraft")
    op.drop_index("ix_wing_aircraft_scenario_id", table_name="wing_aircraft")
    op.drop_table("wing_aircraft")
    op.drop_index("ix_wing_flying_units_wing_id", table_name="wing_flying_units")
    op.drop_index("ix_wing_flying_units_scenario_id", table_name="wing_flying_units")
    op.drop_table("wing_flying_units")
    op.drop_index("ix_air_wings_scenario_id", table_name="air_wings")
    op.drop_table("air_wings")
