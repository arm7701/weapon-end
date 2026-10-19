"""seed remaining air-to-ground munitions into wing_products

Revision ID: 0010_air_to_ground_catalog
Revises: 0009_mk15_high_drag_product
Create Date: 2026-10-05

"""

from __future__ import annotations

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

from maap_app.modules.weaponeering.product_catalog import (
    catalog_description,
    missing_known_products,
)

revision: str = "0010_air_to_ground_catalog"
down_revision: Union[str, Sequence[str], None] = "0009_mk15_high_drag_product"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    scenarios = conn.execute(sa.text("SELECT id FROM scenarios")).fetchall()
    existing = conn.execute(
        sa.text(
            """
            SELECT id, scenario_id, product_name, description, status
            FROM wing_products
            """
        )
    ).fetchall()

    names_by_scenario: dict[str, list[str]] = {}
    for product_id, scenario_id, product_name, description, status in existing:
        sid = str(scenario_id)
        if status == "active":
            names_by_scenario.setdefault(sid, []).append(product_name or "")
        if status != "active":
            continue
        stored = (description or "").strip()
        if stored:
            continue
        filled = catalog_description(product_name or "")
        if not filled:
            continue
        conn.execute(
            sa.text("UPDATE wing_products SET description = :description WHERE id = :id"),
            {"description": filled, "id": product_id},
        )

    for (scenario_id,) in scenarios:
        sid = str(scenario_id)
        for item in missing_known_products(names_by_scenario.get(sid, [])):
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
                    "product_name": item.product_name,
                    "weight_pounds": item.weight_pounds,
                    "unit_cost": item.unit_cost,
                    "description": item.description,
                },
            )
            names_by_scenario.setdefault(sid, []).append(item.product_name)


def downgrade() -> None:
    return
