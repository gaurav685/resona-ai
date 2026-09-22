"""Canonical, dataset-agnostic schemas for the Resona AI data pipeline.

Every raw dataset processed by scripts/process_datasets.py is mapped into
these schemas before being written to data/processed/. This keeps
downstream ML code (ml/features, ml/personality, ...) independent of any
single dataset's raw format.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_validator


def normalize_id(value: str) -> str:
    return str(value).strip()


class Artist(BaseModel):
    artist_id: str
    name: str
    mbid: Optional[str] = None
    source_dataset: str

    @field_validator("artist_id", "name", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v) if v is not None else v


class Album(BaseModel):
    album_id: str
    title: str
    artist_id: Optional[str] = None
    source_dataset: str

    @field_validator("album_id", "title", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v) if v is not None else v


class Genre(BaseModel):
    genre_id: str
    name: str
    source_dataset: str

    @field_validator("genre_id", "name", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v) if v is not None else v


class Track(BaseModel):
    track_id: str
    title: str
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    album_id: Optional[str] = None
    duration_sec: Optional[float] = None
    source_dataset: str

    @field_validator("track_id", "title", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v) if v is not None else v


class User(BaseModel):
    user_id: str
    gender: Optional[str] = None
    age: Optional[int] = None
    country: Optional[str] = None
    registered_at: Optional[datetime] = None
    source_dataset: str

    @field_validator("user_id", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v)

    @field_validator("registered_at", mode="before")
    @classmethod
    def _parse_ts(cls, v):
        return parse_timestamp(v)


class ListeningEvent(BaseModel):
    event_id: str
    user_id: str
    track_id: Optional[str] = None
    artist_name: Optional[str] = None
    track_title: Optional[str] = None
    played_at: datetime
    session_id: Optional[int] = None
    source_dataset: str

    @field_validator("user_id", "event_id", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v) if v is not None else v

    @field_validator("played_at", mode="before")
    @classmethod
    def _parse_ts(cls, v):
        parsed = parse_timestamp(v)
        if parsed is None:
            raise ValueError(f"unparseable timestamp: {v!r}")
        return parsed


class PersonalityRecord(BaseModel):
    participant_id: str
    openness: Optional[float] = None
    conscientiousness: Optional[float] = None
    extraversion: Optional[float] = None
    agreeableness: Optional[float] = None
    neuroticism: Optional[float] = None
    raw_facets: Optional[dict] = None
    source_dataset: str

    @field_validator("participant_id", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v)


class EmotionAnnotation(BaseModel):
    track_id: str
    valence_mean: float
    arousal_mean: float
    valence_std: Optional[float] = None
    arousal_std: Optional[float] = None
    source_dataset: str

    @field_validator("track_id", mode="before")
    @classmethod
    def _strip(cls, v):
        return normalize_id(v)


def parse_timestamp(value) -> Optional[datetime]:
    """Best-effort timestamp parser used across raw dataset formats."""
    if value is None or (isinstance(value, float) and value != value):  # NaN
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    fmts = (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y",
        "%m/%d/%Y",
    )
    for fmt in fmts:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
