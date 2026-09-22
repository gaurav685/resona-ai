import uuid

from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[str] = mapped_column(String(255))
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # audio features (research-standard, populated by ml/features)
    tempo: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)
    valence: Mapped[float | None] = mapped_column(Float, nullable=True)
    danceability: Mapped[float | None] = mapped_column(Float, nullable=True)
    acousticness: Mapped[float | None] = mapped_column(Float, nullable=True)
    instrumentalness: Mapped[float | None] = mapped_column(Float, nullable=True)
    loudness: Mapped[float | None] = mapped_column(Float, nullable=True)
    speechiness: Mapped[float | None] = mapped_column(Float, nullable=True)

    listening_events: Mapped[list["ListeningEvent"]] = relationship(back_populates="track")
