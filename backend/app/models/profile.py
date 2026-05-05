import uuid
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False
    )
    skill_tags: Mapped[dict] = mapped_column(JSON, default=list)
    work_years: Mapped[int] = mapped_column(Integer, default=0)
    education: Mapped[dict] = mapped_column(JSON, default=dict)
    projects: Mapped[dict] = mapped_column(JSON, default=list)
    target: Mapped[dict] = mapped_column(JSON, default=dict)
    preference: Mapped[dict] = mapped_column(JSON, default=dict)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)

    user = relationship("User", back_populates="profile")
