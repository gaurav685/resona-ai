import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Persona(Base):
    """Discovered listener persona / cluster assignment for a user."""

    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    cluster_id: Mapped[int] = mapped_column()
    label: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_version: Mapped[str] = mapped_column(String(50))
    cluster_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="persona")
