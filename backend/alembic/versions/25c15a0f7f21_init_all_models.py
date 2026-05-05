"""init_all_models

Revision ID: 25c15a0f7f21
Revises: 
Create Date: 2026-05-05 16:36:27.216597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25c15a0f7f21'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(30), nullable=False, default="2026-01-01T00:00:00"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("jd_content", sa.Text, nullable=False),
        sa.Column("requirements", sa.JSON, default=list),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("salary_range", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), default="open"),
    )
    op.create_table(
        "experience_stories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tags", sa.JSON, default=dict),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("is_anonymous", sa.Boolean, default=True),
        sa.Column("approved", sa.Boolean, default=False),
    )
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("skill_tags", sa.JSON, default=list),
        sa.Column("work_years", sa.Integer, default=0),
        sa.Column("education", sa.JSON, default=dict),
        sa.Column("projects", sa.JSON, default=list),
        sa.Column("target", sa.JSON, default=dict),
        sa.Column("preference", sa.JSON, default=dict),
        sa.Column("scores", sa.JSON, default=dict),
    )
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("base_version", sa.Boolean, default=False),
        sa.Column("target_role", sa.String(255), nullable=True),
        sa.Column("content", sa.JSON, default=dict),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("match_scores", sa.JSON, default=dict),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", sa.String(36), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("status", sa.String(30), default="planned"),
        sa.Column("timeline", sa.JSON, default=list),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("applications")
    op.drop_table("resumes")
    op.drop_table("user_profiles")
    op.drop_table("experience_stories")
    op.drop_table("jobs")
    op.drop_table("users")
