"""add material_strength (f'c, fy, Fy, soil params ...) to target_cards

Revision ID: 0012_target_material_strength
Revises: 0011_target_heading
Create Date: 2026-10-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0012_target_material_strength"
down_revision: Union[str, Sequence[str], None] = "0011_target_heading"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("target_cards", "material_strength"):
        op.add_column(
            "target_cards",
            sa.Column("material_strength", JSONB(), nullable=False, server_default="{}"),
        )


def downgrade() -> None:
    if _has_column("target_cards", "material_strength"):
        op.drop_column("target_cards", "material_strength")
