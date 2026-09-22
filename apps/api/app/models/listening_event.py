import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ListeningEvent(Base):
    __tablename__ = "listening_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    track_id: Mapped[str] = mapped_column(String(36), ForeignKey("tracks.id"), index=True)
    played_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ms_played: Mapped[float | None] = mapped_column(Float, nullable=True)
    context: Mapped[str | None] = mapped_column(String(120), nullable=True)

    user: Mapped["User"] = relationship(back_populates="listening_events")
    track: Mapped["Track"] = relationship(back_populates="listening_events")
