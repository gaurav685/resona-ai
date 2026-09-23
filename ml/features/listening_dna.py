"""Listening DNA: behavioral feature engineering from raw listening events.

Every feature computed here is derived from data that is actually present
in the processed dataset (data/processed/lastfm_1k/listening_events.csv).
Features that would require data this MVP does not have (track duration /
skip flags / genre / audio features not joined to Last.fm track identities
— see DATASETS.md) are represented explicitly as `None` with a reason,
never fabricated or approximated with made-up numbers.

Two real, documented approximations ARE used (not fabrications — computed
from actual timestamps, just without per-user timezone correction):
  - night_listening_ratio: computed from the UTC hour of each event, not
    the listener's local time (Last.fm 1K gives country, not UTC offset).
  - weekend_listening_ratio: computed from the UTC calendar weekday.
Both are labeled accordingly in the returned profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

SESSION_GAP_MINUTES = 30
NIGHT_START_HOUR = 22  # 22:00 UTC
NIGHT_END_HOUR = 6  # 06:00 UTC

# Audio/content features this MVP cannot compute for Last.fm events — no
# audio-feature dataset is joined to Last.fm track identifiers (documented
# in DATASETS.md). Reported as None with an explicit reason rather than
# silently omitted or guessed.
UNAVAILABLE_FEATURES = {
    "completion_rate": "no track-duration or ms_played field in the source data",
    "skip_rate": "no skip flag in the source data",
    "genre_diversity": "no genre labels joined to Last.fm track identifiers",
    "genre_concentration": "no genre labels joined to Last.fm track identifiers",
    "energy": "no audio-feature dataset joined to Last.fm track identifiers",
    "valence": "no audio-feature dataset joined to Last.fm track identifiers",
    "danceability": "no audio-feature dataset joined to Last.fm track identifiers",
    "tempo": "no audio-feature dataset joined to Last.fm track identifiers",
    "acousticness": "no audio-feature dataset joined to Last.fm track identifiers",
    "instrumentalness": "no audio-feature dataset joined to Last.fm track identifiers",
    "speechiness": "no audio-feature dataset joined to Last.fm track identifiers",
}


@dataclass
class ListeningDNA:
    user_id: str
    n_events: int
    n_sessions: int
    listening_frequency: float | None  # events per active day
    average_session_duration_min: float | None
    tracks_per_session: float | None
    replay_rate: float | None
    repeat_rate: float | None
    artist_diversity: float | None  # unique artists / total plays
    artist_concentration: float | None  # Herfindahl-Hirschman index over artist play share
    discovery_rate: float | None  # fraction of plays that are a first-time artist for this user
    night_listening_ratio_utc: float | None
    weekend_listening_ratio_utc: float | None
    top_artists: list = field(default_factory=list)  # [{"artist_name": str, "play_count": int}], real counts
    unavailable: dict = field(default_factory=lambda: dict(UNAVAILABLE_FEATURES))

    def to_dict(self) -> dict:
        d = {
            "user_id": self.user_id,
            "n_events": self.n_events,
            "n_sessions": self.n_sessions,
            "listening_frequency": self.listening_frequency,
            "average_session_duration_min": self.average_session_duration_min,
            "tracks_per_session": self.tracks_per_session,
            "replay_rate": self.replay_rate,
            "repeat_rate": self.repeat_rate,
            "artist_diversity": self.artist_diversity,
            "artist_concentration": self.artist_concentration,
            "discovery_rate": self.discovery_rate,
            "night_listening_ratio_utc": self.night_listening_ratio_utc,
            "weekend_listening_ratio_utc": self.weekend_listening_ratio_utc,
            "top_artists": self.top_artists,
        }
        for name, reason in self.unavailable.items():
            d[name] = None
            d[f"{name}_unavailable_reason"] = reason
        return d


NUMERIC_FEATURE_COLUMNS = [
    "listening_frequency",
    "average_session_duration_min",
    "tracks_per_session",
    "replay_rate",
    "repeat_rate",
    "artist_diversity",
    "artist_concentration",
    "discovery_rate",
    "night_listening_ratio_utc",
    "weekend_listening_ratio_utc",
]


def _herfindahl(shares: np.ndarray) -> float:
    return float(np.sum(shares**2))


def compute_listening_dna(events: pd.DataFrame, user_id: str) -> ListeningDNA:
    """Compute Listening DNA for a single user from their event rows.

    `events` must contain at least: user_id, artist_name, track_title,
    played_at (parseable to datetime), session_id.
    """
    user_events = events[events["user_id"] == user_id].copy()
    n_events = len(user_events)
    if n_events == 0:
        return ListeningDNA(
            user_id=user_id,
            n_events=0,
            n_sessions=0,
            listening_frequency=None,
            average_session_duration_min=None,
            tracks_per_session=None,
            replay_rate=None,
            repeat_rate=None,
            artist_diversity=None,
            artist_concentration=None,
            discovery_rate=None,
            night_listening_ratio_utc=None,
            weekend_listening_ratio_utc=None,
        )

    user_events["played_at"] = pd.to_datetime(user_events["played_at"], utc=True)
    user_events = user_events.sort_values("played_at")

    n_days = max((user_events["played_at"].max() - user_events["played_at"].min()).days, 1)
    listening_frequency = n_events / n_days

    sessions = user_events.groupby("session_id")
    n_sessions = sessions.ngroups
    session_durations = sessions["played_at"].apply(lambda s: (s.max() - s.min()).total_seconds() / 60.0)
    average_session_duration_min = float(session_durations.mean())
    tracks_per_session = float(sessions.size().mean())

    track_key = user_events["artist_name"].astype(str) + " — " + user_events["track_title"].astype(str)
    track_counts = track_key.value_counts()
    replay_rate = float((track_counts[track_counts > 1].sum() - (track_counts > 1).sum()) / n_events) if n_events else None
    repeat_rate = float((track_counts > 1).sum() / len(track_counts)) if len(track_counts) else None

    artist_counts = user_events["artist_name"].value_counts()
    top_artists = [
        {"artist_name": name, "play_count": int(count)}
        for name, count in artist_counts.head(10).items()
    ]
    artist_diversity = float(len(artist_counts) / n_events)
    artist_shares = (artist_counts / n_events).to_numpy()
    artist_concentration = _herfindahl(artist_shares)

    first_seen = user_events.drop_duplicates(subset=["artist_name"], keep="first")
    discovery_rate = float(len(first_seen) / n_events)

    hours = user_events["played_at"].dt.hour
    night_mask = (hours >= NIGHT_START_HOUR) | (hours < NIGHT_END_HOUR)
    night_listening_ratio_utc = float(night_mask.mean())

    weekday = user_events["played_at"].dt.weekday  # 5=Sat, 6=Sun
    weekend_listening_ratio_utc = float((weekday >= 5).mean())

    return ListeningDNA(
        user_id=user_id,
        n_events=n_events,
        n_sessions=n_sessions,
        listening_frequency=listening_frequency,
        average_session_duration_min=average_session_duration_min,
        tracks_per_session=tracks_per_session,
        replay_rate=replay_rate,
        repeat_rate=repeat_rate,
        artist_diversity=artist_diversity,
        artist_concentration=artist_concentration,
        discovery_rate=discovery_rate,
        night_listening_ratio_utc=night_listening_ratio_utc,
        weekend_listening_ratio_utc=weekend_listening_ratio_utc,
        top_artists=top_artists,
    )


def compute_all(events: pd.DataFrame) -> pd.DataFrame:
    """Compute Listening DNA for every user present in `events`.

    Returns a DataFrame with one row per user and NUMERIC_FEATURE_COLUMNS
    as columns (plus user_id, n_events, n_sessions) — the feature matrix
    consumed by ml/personas/cluster.py.
    """
    rows = [compute_listening_dna(events, uid).to_dict() for uid in events["user_id"].unique()]
    return pd.DataFrame(rows)
