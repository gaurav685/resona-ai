"""Phase 5 persistence for recommendation evidence + feedback.

Deliberately NOT built on the Phase 1 `Recommendation`/`Feedback` models:
those FK to `users.id`/`tracks.id` (uuid-shaped, populated only by a
future app-native signup flow) and were never exercised with real data —
the actual recommendation pipeline (Phase 4) operates on Last.fm string
ids ("user_000001", 16-hex item hashes) read from processed research
data, not the app DB. Retrofitting the Phase 1 FKs would mean fabricating
thousands of placeholder User/Track rows just to satisfy a constraint.
These tables store exactly what Phase 5 needs — recommendation evidence
and feedback keyed by the real string ids already in use — with no FK to
the unpopulated tables.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RecommendationLog(Base):
    """One persisted row per recommendation actually returned to a user —
    the source of truth an explanation is generated from."""

    __tablename__ = "recommendation_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    item_id: Mapped[str] = mapped_column(String(32), index=True)
    artist_name: Mapped[str] = mapped_column(String(255))
    track_title: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict] = mapped_column(JSON)
    context_label: Mapped[str] = mapped_column(String(50))
    reason_codes: Mapped[list] = mapped_column(JSON)
    evidence: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    feedback: Mapped[list["RecommendationFeedback"]] = relationship(back_populates="recommendation")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recommendation_log.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    feedback_type: Mapped[str] = mapped_column(String(20))  # like/dislike/skip/save/replay/hide
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    recommendation: Mapped["RecommendationLog"] = relationship(back_populates="feedback")
