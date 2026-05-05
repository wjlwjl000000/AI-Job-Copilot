import uuid
from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    base_version: Mapped[bool] = mapped_column(Boolean, default=False)
    target_role: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    match_scores: Mapped[dict] = mapped_column(JSON, default=dict)

    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")
