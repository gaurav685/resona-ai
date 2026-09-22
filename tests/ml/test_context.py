import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))

from features.context import compute_current_context, UNAVAILABLE_SHIFTS  # noqa: E402


def _events(rows):
    return pd.DataFrame(rows, columns=["user_id", "artist_name", "track_title", "played_at", "session_id"])


def test_no_history_returns_unknown():
    result = compute_current_context(_events([]), "nobody")
    assert result.context_label == "Unknown"
    assert result.windows["last_5"]["n_events"] == 0


def test_exploratory_detected_from_new_artists():
    # baseline: 20 plays of "Familiar Artist"; recent session: 5 plays of
    # 5 different unfamiliar artists.
    rows = [("u1", "Familiar Artist", f"Song {i}", f"2020-01-{i+1:02d}T10:00:00Z", f"u1-s{i}") for i in range(20)]
    for i in range(5):
        rows.append(("u1", f"New Artist {i}", f"New Song {i}", "2020-02-01T10:0" + str(i) + ":00Z", "u1-latest"))
    result = compute_current_context(_events(rows), "u1")
    assert result.context_label == "Exploratory"


def test_focused_detected_from_repeated_artist():
    # baseline: 20 distinct artists, no repeats at all (repeat_rate=0).
    rows = [("u1", f"Artist {i}", f"Song {i}", f"2020-01-{i+1:02d}T10:00:00Z", f"u1-s{i}") for i in range(20)]
    # recent session: same 2 artists played repeatedly (high repeat_rate).
    for i in range(6):
        rows.append(("u1", f"Same Artist {i % 2}", f"Repeat Song {i}", f"2020-02-01T10:0{i}:00Z", "u1-latest"))
    result = compute_current_context(_events(rows), "u1")
    assert result.context_label == "Focused"
    assert result.shifts["repeat_shift"] > 0


def test_unavailable_shifts_never_fabricated():
    rows = [("u1", "A", "S1", "2020-01-01T10:00:00Z", "u1-s1")] * 5
    result = compute_current_context(_events(rows), "u1").to_dict()
    for name, reason in UNAVAILABLE_SHIFTS.items():
        assert result["shifts"][name] is None
        assert result["shifts"][f"{name}_unavailable_reason"] == reason
