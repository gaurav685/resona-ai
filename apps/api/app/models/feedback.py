import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id: Mapped[str] = mapped_column(String(36), ForeignKey("recommendations.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    liked: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    recommendation: Mapped["Recommendation"] = relationship(back_populates="feedback")
