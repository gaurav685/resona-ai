import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    listening_events: Mapped[list["ListeningEvent"]] = relationship(back_populates="user")
    personality_predictions: Mapped[list["PersonalityPrediction"]] = relationship(back_populates="user")
    persona: Mapped[list["Persona"]] = relationship(back_populates="user")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="user")
