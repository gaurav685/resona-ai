import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PersonalityPrediction(Base):
    """Model-estimated Big Five trait associations. NOT a psychological diagnosis."""

    __tablename__ = "personality_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(50))

    openness: Mapped[float] = mapped_column(Float)
    conscientiousness: Mapped[float] = mapped_column(Float)
    extraversion: Mapped[float] = mapped_column(Float)
    agreeableness: Mapped[float] = mapped_column(Float)
    neuroticism: Mapped[float] = mapped_column(Float)

    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="personality_predictions")
