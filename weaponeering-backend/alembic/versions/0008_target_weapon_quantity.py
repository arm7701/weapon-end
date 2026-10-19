"""add weapon_quantity to targets

Revision ID: 0008_target_weapon_quantity
Revises: 0007_flying_unit_coords
Create Date: 2026-09-02

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_target_weapon_quantity"
down_revision: Union[str, Sequence[str], None] = "0007_flying_unit_coords"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("target_cards", "weapon_quantity"):
        op.add_column("target_cards", sa.Column("weapon_quantity", sa.Integer(), nullable=True))
    if not _has_column("target_coordinates", "weapon_quantity"):
        op.add_column(
            "target_coordinates",
            sa.Column("weapon_quantity", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("target_coordinates", "weapon_quantity"):
        op.drop_column("target_coordinates", "weapon_quantity")
    if _has_column("target_cards", "weapon_quantity"):
        op.drop_column("target_cards", "weapon_quantity")
