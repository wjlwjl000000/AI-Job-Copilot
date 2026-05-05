import uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), nullable=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), default="planned")
    timeline: Mapped[dict] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
