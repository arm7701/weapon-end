"""add heading_deg to target_cards for map footprint polygon

Revision ID: 0011_target_heading
Revises: 0010_air_to_ground_catalog
Create Date: 2026-10-06

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_target_heading"
down_revision: Union[str, Sequence[str], None] = "0010_air_to_ground_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("target_cards", "heading_deg"):
        op.add_column("target_cards", sa.Column("heading_deg", sa.Float(), nullable=True))


def downgrade() -> None:
    if _has_column("target_cards", "heading_deg"):
        op.drop_column("target_cards", "heading_deg")
