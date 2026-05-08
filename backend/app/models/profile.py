import uuid
from sqlalchemy import String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    contact: Mapped[dict] = mapped_column(JSON, nullable=True)
    basic: Mapped[dict] = mapped_column(JSON, nullable=True)
    education: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    projects: Mapped[list] = mapped_column(JSON, default=list)
    organization: Mapped[list] = mapped_column(JSON, default=list)
    work_years: Mapped[int] = mapped_column(Integer, default=0)
    target: Mapped[dict] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
