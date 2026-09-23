import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml" / "recommendation"))

from hybrid import RecommenderArtifacts, RecommenderUnavailable, diversify, score_candidates  # noqa: E402


def _synthetic_artifacts():
    # 3 users, 6 items across 3 artists (2 each). u1 has played item0/item1
    # (Artist A) heavily; the rest are unplayed candidates.
    # u1 has played item0 (Artist A, x2) and item2 (Artist B, x1). item1
    # (also Artist A, never played by u1) is an unplayed candidate that
    # should score high on artist_preference. item4 (Artist C) / item5
    # (Artist D) are candidates by artists u1 has never played.
    events = pd.DataFrame(
        [
            ("u1", "item0", "Artist A", "Song A1", "2020-01-01T10:00:00Z", "u1-s1"),
            ("u1", "item0", "Artist A", "Song A1", "2020-01-02T10:00:00Z", "u1-s2"),
            ("u1", "item2", "Artist B", "Song B1", "2020-01-04T10:00:00Z", "u1-s3"),
            ("u2", "item2", "Artist B", "Song B1", "2020-01-01T10:00:00Z", "u2-s1"),
            ("u2", "item3", "Artist B", "Song B2", "2020-01-02T10:00:00Z", "u2-s2"),
            ("u3", "item4", "Artist C", "Song C1", "2020-01-01T10:00:00Z", "u3-s1"),
        ],
        columns=["user_id", "item_id", "artist_name", "track_title", "played_at", "session_id"],
    )
    catalog = pd.DataFrame(
        {
            "item_id": ["item0", "item1", "item2", "item3", "item4", "item5"],
            "artist_name": ["Artist A", "Artist A", "Artist B", "Artist B", "Artist C", "Artist D"],
            "track_title": ["Song A1", "Song A2", "Song B1", "Song B2", "Song C1", "Song D1"],
            "play_count": [2, 1, 2, 1, 1, 0],
            "n_unique_users": [1, 1, 2, 1, 1, 0],
            "popularity": [0.5, 0.5, 1.0, 0.5, 0.5, 0.01],
        }
    )
    item_ids = catalog["item_id"].tolist()
    n = len(item_ids)
    sim = np.eye(n) * 0  # start at zero, fill in plausible co-occurrence
    idx = {it: i for i, it in enumerate(item_ids)}
    # item0/item1 (both Artist A) are similar; item2/item3 (Artist B) similar
    sim[idx["item0"], idx["item1"]] = sim[idx["item1"], idx["item0"]] = 0.9
    sim[idx["item2"], idx["item3"]] = sim[idx["item3"], idx["item2"]] = 0.8
    return RecommenderArtifacts(events=events, catalog=catalog, sim_matrix=sim, item_ids=item_ids)


def test_candidate_generation_excludes_played_items():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    # u1 played item0 and item2 — neither should appear as a candidate
    assert "item0" not in scored["item_id"].values
    assert "item2" not in scored["item_id"].values
    assert set(scored["item_id"]) == {"item1", "item3", "item4", "item5"}


def test_co_listening_similarity_favors_items_similar_to_played():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    # item1 co-occurs strongly with item0 (u1's played item, sim=0.9);
    # item4 has no co-occurrence with anything u1 played (sim=0).
    item1_sim = scored.loc[scored["item_id"] == "item1", "co_listening_similarity"].iloc[0]
    item4_sim = scored.loc[scored["item_id"] == "item4", "co_listening_similarity"].iloc[0]
    assert item1_sim > item4_sim


def test_unknown_user_raises():
    artifacts = _synthetic_artifacts()
    with pytest.raises(RecommenderUnavailable):
        score_candidates(artifacts, "does-not-exist")


def test_artist_preference_favors_users_own_artist():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    # u1's most-played artist is "Artist A" (item0, item1 both Artist A) —
    # item1 (also Artist A, unplayed) should score higher on artist_preference
    # than item4/item5 (artists u1 has never played).
    item1_pref = scored.loc[scored["item_id"] == "item1", "artist_preference"].iloc[0]
    item4_pref = scored.loc[scored["item_id"] == "item4", "artist_preference"].iloc[0]
    assert item1_pref > item4_pref


def test_novelty_favors_less_popular_items():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    item5_novelty = scored.loc[scored["item_id"] == "item5", "novelty"].iloc[0]
    item3_novelty = scored.loc[scored["item_id"] == "item3", "novelty"].iloc[0]
    assert item5_novelty > item3_novelty  # item5 has popularity=0.01, item3 has 0.5


def test_diversify_respects_max_per_artist():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    ranked = diversify(scored, artifacts, limit=4, max_per_artist=1)
    assert ranked["artist_name"].value_counts().max() <= 1


def test_diversify_returns_at_most_limit():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    ranked = diversify(scored, artifacts, limit=2)
    assert len(ranked) <= 2


def test_context_alignment_exploratory_favors_unfamiliar():
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1", context_override="Exploratory")
    item1_align = scored.loc[scored["item_id"] == "item1", "context_alignment"].iloc[0]  # familiar (Artist A)
    item4_align = scored.loc[scored["item_id"] == "item4", "context_alignment"].iloc[0]  # unfamiliar (Artist C)
    assert item4_align > item1_align


def test_is_new_artist_uses_full_history_not_just_top10():
    # u1 played item0 (Artist A) heavily and item2 (Artist B) once — both
    # played artists must never be flagged "new", regardless of play count.
    artifacts = _synthetic_artifacts()
    scored = score_candidates(artifacts, "u1")
    item1_new = scored.loc[scored["item_id"] == "item1", "is_new_artist"].iloc[0]  # Artist A, played
    item3_new = scored.loc[scored["item_id"] == "item3", "is_new_artist"].iloc[0]  # Artist B, played once
    item4_new = scored.loc[scored["item_id"] == "item4", "is_new_artist"].iloc[0]  # Artist C, never played
    assert item1_new == False  # noqa: E712
    assert item3_new == False  # noqa: E712
    assert item4_new == True  # noqa: E712


# --- Part D: feedback integration ------------------------------------------

def test_feedback_excludes_hidden_item_from_candidates():
    artifacts = _synthetic_artifacts()
    feedback = {"artist_multiplier": {}, "excluded_items": {"item1"}}
    scored = score_candidates(artifacts, "u1", feedback=feedback)
    assert "item1" not in scored["item_id"].values


def test_feedback_boosts_artist_preference_score():
    # A multiplier can only raise a preference that starts above zero —
    # item4 (Artist C) is never played by u1, so its base preference is
    # exactly 0 and no multiplier can lift it; use item3 (Artist B, u1 has
    # a real nonzero preference for) instead.
    artifacts = _synthetic_artifacts()
    baseline = score_candidates(artifacts, "u1")
    baseline_pref = baseline.loc[baseline["item_id"] == "item3", "artist_preference"].iloc[0]
    assert baseline_pref > 0  # sanity: the test premise requires a nonzero base

    feedback = {"artist_multiplier": {"Artist B": 1.8}, "excluded_items": set()}
    boosted = score_candidates(artifacts, "u1", feedback=feedback)
    boosted_pref = boosted.loc[boosted["item_id"] == "item3", "artist_preference"].iloc[0]

    assert boosted_pref > baseline_pref


def test_feedback_dampens_artist_preference_score():
    artifacts = _synthetic_artifacts()
    baseline = score_candidates(artifacts, "u1")
    baseline_pref = baseline.loc[baseline["item_id"] == "item1", "artist_preference"].iloc[0]

    feedback = {"artist_multiplier": {"Artist A": 0.3}, "excluded_items": set()}
    dampened = score_candidates(artifacts, "u1", feedback=feedback)
    dampened_pref = dampened.loc[dampened["item_id"] == "item1", "artist_preference"].iloc[0]

    assert dampened_pref < baseline_pref
