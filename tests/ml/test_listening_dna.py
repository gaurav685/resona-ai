import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))

from features.listening_dna import compute_listening_dna, UNAVAILABLE_FEATURES  # noqa: E402


def _events(rows):
    return pd.DataFrame(
        rows, columns=["user_id", "artist_name", "track_title", "played_at", "session_id"]
    )


def test_unknown_user_returns_zero_events():
    dna = compute_listening_dna(_events([]), "nobody")
    assert dna.n_events == 0
    assert dna.listening_frequency is None


def test_artist_diversity_all_unique():
    rows = [
        ("u1", "Artist A", "Song 1", "2020-01-01T10:00:00Z", "u1-s1"),
        ("u1", "Artist B", "Song 2", "2020-01-01T10:05:00Z", "u1-s1"),
        ("u1", "Artist C", "Song 3", "2020-01-01T10:10:00Z", "u1-s1"),
    ]
    dna = compute_listening_dna(_events(rows), "u1")
    assert dna.n_events == 3
    assert dna.artist_diversity == pytest.approx(1.0)  # 3 unique / 3 plays
    assert dna.discovery_rate == pytest.approx(1.0)  # every artist is first-seen
    assert dna.replay_rate == pytest.approx(0.0)


def test_replay_rate_with_repeated_track():
    rows = [
        ("u1", "Artist A", "Song 1", "2020-01-01T10:00:00Z", "u1-s1"),
        ("u1", "Artist A", "Song 1", "2020-01-01T10:05:00Z", "u1-s1"),
        ("u1", "Artist B", "Song 2", "2020-01-01T10:10:00Z", "u1-s1"),
    ]
    dna = compute_listening_dna(_events(rows), "u1")
    # track_key "Artist A — Song 1" played twice: 1 replay out of 3 plays
    assert dna.replay_rate == pytest.approx(1 / 3)
    assert dna.repeat_rate == pytest.approx(1 / 2)  # 1 of 2 distinct tracks was replayed


def test_night_and_weekend_ratios():
    rows = [
        ("u1", "A", "S1", "2021-06-05T23:00:00Z", "u1-s1"),  # Sat night
        ("u1", "A", "S2", "2021-06-05T23:10:00Z", "u1-s1"),  # Sat night
        ("u1", "A", "S3", "2021-06-08T12:00:00Z", "u1-s2"),  # Tue midday
        ("u1", "A", "S4", "2021-06-08T12:10:00Z", "u1-s2"),  # Tue midday
    ]
    dna = compute_listening_dna(_events(rows), "u1")
    assert dna.night_listening_ratio_utc == pytest.approx(0.5)
    assert dna.weekend_listening_ratio_utc == pytest.approx(0.5)


def test_unavailable_features_reported_not_fabricated():
    rows = [("u1", "A", "S1", "2021-06-05T10:00:00Z", "u1-s1")]
    dna = compute_listening_dna(_events(rows), "u1").to_dict()
    for feat, reason in UNAVAILABLE_FEATURES.items():
        assert dna[feat] is None
        assert dna[f"{feat}_unavailable_reason"] == reason
