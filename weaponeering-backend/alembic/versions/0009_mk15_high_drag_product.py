"""add product description and seed MK 15 high-drag bomb

Revision ID: 0009_mk15_high_drag_product
Revises: 0008_target_weapon_quantity
Create Date: 2026-10-05

"""

from __future__ import annotations

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

from maap_app.modules.weaponeering.product_catalog import KNOWN_PRODUCTS, normalize_product_key

revision: str = "0009_mk15_high_drag_product"
down_revision: Union[str, Sequence[str], None] = "0008_target_weapon_quantity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("wing_products", "description"):
        op.add_column(
            "wing_products",
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
        )

    mk15 = next(item for item in KNOWN_PRODUCTS if item.key == "mk-15-high-drag")
    conn = op.get_bind()
    scenarios = conn.execute(sa.text("SELECT id FROM scenarios")).fetchall()
    existing = conn.execute(
        sa.text("SELECT scenario_id, product_name, status FROM wing_products")
    ).fetchall()
    present: set[str] = set()
    for scenario_id, product_name, status in existing:
        if status != "active":
            continue
        if "mk15" in normalize_product_key(product_name or ""):
            present.add(str(scenario_id))

    for (scenario_id,) in scenarios:
        if str(scenario_id) in present:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO wing_products (
                    id, scenario_id, product_name, weight_pounds, unit_cost,
                    description, status
                ) VALUES (
                    :id, :scenario_id, :product_name, :weight_pounds, :unit_cost,
                    :description, 'active'
                )
                """
            ),
            {
                "id": str(uuid4()),
                "scenario_id": scenario_id,
                "product_name": mk15.product_name,
                "weight_pounds": mk15.weight_pounds,
                "unit_cost": mk15.unit_cost,
                "description": mk15.description,
            },
        )


def downgrade() -> None:
    if _has_column("wing_products", "description"):
        op.drop_column("wing_products", "description")
