"""remove_user_id_from_user_profiles

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-08 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("user_profiles_user_id_fkey", "user_profiles", type_="foreignkey")
    op.drop_constraint("user_profiles_user_id_key", "user_profiles", type_="unique")
    op.drop_column("user_profiles", "user_id")


def downgrade() -> None:
    op.add_column("user_profiles", sa.Column("user_id", sa.String(36), nullable=True))
    op.create_unique_constraint("user_profiles_user_id_key", "user_profiles", ["user_id"])
    op.create_foreign_key("user_profiles_user_id_fkey", "user_profiles", "users", ["user_id"], ["id"])
