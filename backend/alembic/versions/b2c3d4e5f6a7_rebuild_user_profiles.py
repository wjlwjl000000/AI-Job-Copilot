"""rebuild_user_profiles

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("user_profiles")
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("contact", sa.JSON, nullable=True),
        sa.Column("basic", sa.JSON, nullable=True),
        sa.Column("education", sa.JSON, server_default="[]"),
        sa.Column("skills", sa.JSON, server_default="[]"),
        sa.Column("projects", sa.JSON, server_default="[]"),
        sa.Column("organization", sa.JSON, server_default="[]"),
        sa.Column("work_years", sa.Integer, server_default="0"),
        sa.Column("target", sa.JSON, nullable=True),
        sa.Column("scores", sa.JSON, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("skill_tags", sa.JSON, server_default="[]"),
        sa.Column("work_years", sa.Integer, server_default="0"),
        sa.Column("education", sa.JSON, server_default="{}"),
        sa.Column("projects", sa.JSON, server_default="[]"),
        sa.Column("target", sa.JSON, server_default="{}"),
        sa.Column("preference", sa.JSON, server_default="{}"),
        sa.Column("scores", sa.JSON, server_default="{}"),
        sa.Column("jd", sa.JSON, nullable=True),
    )
