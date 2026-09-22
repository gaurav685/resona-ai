"""Part A — current listening context, derived by comparing recent
listening windows against a user's historical baseline.

Only behavioral signals actually present in the data are used: artist
identity, session boundaries, and timestamps. energy_shift, valence_shift,
tempo_shift, and genre_shift are NOT computed — no audio-feature or genre
dataset is joined to Last.fm track identifiers in this MVP (see
DATASETS.md) — and are returned as null with an explicit reason rather
than approximated or fabricated.

Context labels are a simple, transparent rule-based read of behavioral
shift magnitude. They are explicitly non-clinical, non-psychological
descriptions of a listening session, not a mood/mental-state diagnosis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

LAST_30_MIN = pd.Timedelta(minutes=30)

UNAVAILABLE_SHIFTS = {
    "energy_shift": "no audio-feature dataset joined to Last.fm track identifiers",
    "valence_shift": "no audio-feature dataset joined to Last.fm track identifiers",
    "tempo_shift": "no audio-feature dataset joined to Last.fm track identifiers",
    "genre_shift": "no genre labels joined to Last.fm track identifiers",
}


def _window_stats(window: pd.DataFrame, baseline_top_artists: set[str]) -> dict:
    n = len(window)
    if n == 0:
        return {
            "n_events": 0, "artist_diversity": None, "repeat_rate": None,
            "artist_shift": None, "avg_gap_sec": None, "night_ratio": None,
        }
    artist_counts = window["artist_name"].value_counts()
    artist_diversity = float(len(artist_counts) / n)
    repeat_rate = float((artist_counts.reset_index(drop=True) > 1).sum() / len(artist_counts)) if len(artist_counts) else 0.0
    unfamiliar = window[~window["artist_name"].isin(baseline_top_artists)]
    artist_shift = float(len(unfamiliar) / n)

    ts = window["played_at"].sort_values()
    if len(ts) > 1:
        gaps = ts.diff().dropna().dt.total_seconds()
        avg_gap_sec = float(gaps.mean())
    else:
        avg_gap_sec = None

    hours = window["played_at"].dt.hour
    night_ratio = float(((hours >= 22) | (hours < 6)).mean())

    return {
        "n_events": n,
        "artist_diversity": artist_diversity,
        "repeat_rate": repeat_rate,
        "artist_shift": artist_shift,
        "avg_gap_sec": avg_gap_sec,
        "night_ratio": night_ratio,
    }


@dataclass
class ContextResult:
    user_id: str
    windows: dict
    baseline: dict
    shifts: dict
    context_label: str
    context_explanation: str

    def to_dict(self) -> dict:
        d = {
            "user_id": self.user_id,
            "windows": self.windows,
            "baseline": self.baseline,
            "shifts": self.shifts,
            "context_label": self.context_label,
            "context_explanation": self.context_explanation,
            "disclaimer": "Behavioral listening-session description only — not a psychological or medical state.",
        }
        for name, reason in UNAVAILABLE_SHIFTS.items():
            d["shifts"][name] = None
            d["shifts"][f"{name}_unavailable_reason"] = reason
        return d


def compute_current_context(events: pd.DataFrame, user_id: str) -> ContextResult:
    user_events = events[events["user_id"] == user_id].copy()
    user_events["played_at"] = pd.to_datetime(user_events["played_at"], utc=True)
    user_events = user_events.sort_values("played_at")

    if len(user_events) == 0:
        empty = {"n_events": 0}
        return ContextResult(
            user_id=user_id,
            windows={"last_5": empty, "last_10": empty, "current_session": empty, "last_30_min": empty},
            baseline={},
            shifts={},
            context_label="Unknown",
            context_explanation="No listening history available for this user.",
        )

    latest_session_id = user_events["session_id"].iloc[-1]

    # Baseline (and "familiar artist" set) is computed from history BEFORE
    # the current session, never the current session's own events —
    # otherwise a short history trivially counts brand-new artists as
    # "familiar" just because they're part of the same small event set.
    history = user_events[user_events["session_id"] != latest_session_id]
    if history.empty:
        history = user_events  # single-session user: no prior history to compare against

    baseline_top_artists = set(history["artist_name"].value_counts().head(10).index)
    baseline = _window_stats(history, baseline_top_artists)

    last_5 = _window_stats(user_events.tail(5), baseline_top_artists)
    last_10 = _window_stats(user_events.tail(10), baseline_top_artists)

    current_session = _window_stats(
        user_events[user_events["session_id"] == latest_session_id], baseline_top_artists
    )

    latest_ts = user_events["played_at"].iloc[-1]
    last_30_min = _window_stats(
        user_events[user_events["played_at"] >= latest_ts - LAST_30_MIN], baseline_top_artists
    )

    # Classify from whichever recent window has enough events to be
    # meaningful; prefer current_session, fall back to last_10.
    primary = current_session if current_session["n_events"] >= 3 else last_10

    def _shift(key):
        if primary[key] is None or baseline[key] is None:
            return None
        return float(primary[key] - baseline[key])

    shifts = {
        "artist_shift": primary["artist_shift"],
        "diversity_shift": _shift("artist_diversity"),
        "repeat_shift": _shift("repeat_rate"),
        "night_shift": _shift("night_ratio"),
        "pace_shift_sec": (
            None if primary["avg_gap_sec"] is None or baseline["avg_gap_sec"] is None
            else float(baseline["avg_gap_sec"] - primary["avg_gap_sec"])  # positive = faster-paced now
        ),
    }

    label, explanation = _classify(shifts, primary)

    return ContextResult(
        user_id=user_id,
        windows={"last_5": last_5, "last_10": last_10, "current_session": current_session, "last_30_min": last_30_min},
        baseline=baseline,
        shifts=shifts,
        context_label=label,
        context_explanation=explanation,
    )


def _classify(shifts: dict, primary: dict) -> tuple[str, str]:
    if primary["n_events"] == 0:
        return "Unknown", "No recent listening activity to classify."

    artist_shift = shifts["artist_shift"] or 0.0
    diversity_shift = shifts["diversity_shift"] or 0.0
    repeat_shift = shifts["repeat_shift"] or 0.0
    night_shift = shifts["night_shift"] or 0.0
    pace_shift = shifts["pace_shift_sec"] or 0.0

    if artist_shift > 0.5 and diversity_shift > 0:
        return (
            "Exploratory",
            f"{artist_shift:.0%} of recent plays are artists outside this user's usual top-10, "
            f"with higher-than-usual artist diversity (+{diversity_shift:.2f}).",
        )
    if repeat_shift > 0.15:
        return (
            "Focused",
            f"Repeat-listening rate is {repeat_shift:+.2f} above this user's baseline — "
            "sticking to fewer, familiar tracks right now.",
        )
    if night_shift > 0.3 and pace_shift < 0:
        return (
            "Reflective",
            f"Listening more at night than usual (+{night_shift:.2f}) at a slower pace "
            f"({-pace_shift:.0f}s longer between tracks than baseline).",
        )
    return (
        "Routine",
        "No strong shift from this user's historical listening pattern was detected.",
    )
