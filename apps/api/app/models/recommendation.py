import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    track_id: Mapped[str] = mapped_column(String(36), ForeignKey("tracks.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="recommendations")
    track: Mapped["Track"] = relationship()
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="recommendation")
