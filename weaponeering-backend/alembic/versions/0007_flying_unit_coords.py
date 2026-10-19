"""add map_lat/map_lng to wing_flying_units

Revision ID: 0007_flying_unit_coords
Revises: 0006_phase6_detection
Create Date: 2026-07-27

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_flying_unit_coords"
down_revision: Union[str, Sequence[str], None] = "0006_phase6_detection"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    # Columns may already exist if added manually before this revision was applied.
    if not _has_column("wing_flying_units", "map_lat"):
        op.add_column("wing_flying_units", sa.Column("map_lat", sa.Float(), nullable=True))
    if not _has_column("wing_flying_units", "map_lng"):
        op.add_column("wing_flying_units", sa.Column("map_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    if _has_column("wing_flying_units", "map_lng"):
        op.drop_column("wing_flying_units", "map_lng")
    if _has_column("wing_flying_units", "map_lat"):
        op.drop_column("wing_flying_units", "map_lat")
