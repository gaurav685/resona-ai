"""Part of Phase 6: real time-bucketed preference evolution from actual
listening events — monthly bins of artist diversity, discovery rate, and
listening frequency. No trend is invented; a user whose capped 300-event
sample falls in a short window will simply show few periods.
"""

from __future__ import annotations

import pandas as pd


def compute_taste_evolution(events: pd.DataFrame, user_id: str, freq: str = "M") -> list[dict]:
    user_events = events[events["user_id"] == user_id].copy()
    if user_events.empty:
        return []

    user_events["played_at"] = pd.to_datetime(user_events["played_at"], utc=True)
    user_events = user_events.sort_values("played_at")
    user_events["period"] = user_events["played_at"].dt.to_period(freq).astype(str)

    seen_artists: set[str] = set()
    rows = []
    for period, group in user_events.groupby("period", sort=True):
        n = len(group)
        artists_in_period = set(group["artist_name"])
        new_artists = artists_in_period - seen_artists
        discovery_rate = len(new_artists) / n if n else None
        artist_diversity = len(artists_in_period) / n if n else None
        seen_artists |= artists_in_period

        span_days = max((group["played_at"].max() - group["played_at"].min()).total_seconds() / 86400, 1)
        listening_frequency = n / span_days

        rows.append(
            {
                "period": period,
                "n_events": n,
                "unique_artists": len(artists_in_period),
                "artist_diversity": artist_diversity,
                "discovery_rate": discovery_rate,
                "listening_frequency": listening_frequency,
            }
        )
    return rows
