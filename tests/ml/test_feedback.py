import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml" / "recommendation"))

from feedback import compute_feedback_adjustments  # noqa: E402


def test_no_feedback_gives_neutral_adjustments():
    result = compute_feedback_adjustments([])
    assert result["artist_multiplier"] == {}
    assert result["excluded_items"] == set()


def test_like_boosts_artist_multiplier_above_one():
    rows = [{"item_id": "i1", "artist_name": "Artist A", "feedback_type": "like"}]
    result = compute_feedback_adjustments(rows)
    assert result["artist_multiplier"]["Artist A"] > 1.0


def test_dislike_dampens_artist_multiplier_below_one():
    rows = [{"item_id": "i1", "artist_name": "Artist A", "feedback_type": "dislike"}]
    result = compute_feedback_adjustments(rows)
    assert result["artist_multiplier"]["Artist A"] < 1.0


def test_dislike_and_hide_hard_exclude_the_item():
    rows = [
        {"item_id": "i1", "artist_name": "Artist A", "feedback_type": "dislike"},
        {"item_id": "i2", "artist_name": "Artist B", "feedback_type": "hide"},
        {"item_id": "i3", "artist_name": "Artist C", "feedback_type": "like"},
    ]
    result = compute_feedback_adjustments(rows)
    assert result["excluded_items"] == {"i1", "i2"}


def test_multiplier_bounded_even_with_many_likes():
    rows = [{"item_id": f"i{i}", "artist_name": "Artist A", "feedback_type": "like"} for i in range(100)]
    result = compute_feedback_adjustments(rows)
    assert result["artist_multiplier"]["Artist A"] <= 1.8


def test_multiplier_bounded_even_with_many_dislikes():
    rows = [{"item_id": f"i{i}", "artist_name": "Artist A", "feedback_type": "dislike"} for i in range(100)]
    result = compute_feedback_adjustments(rows)
    assert result["artist_multiplier"]["Artist A"] >= 0.3


def test_mixed_feedback_nets_out():
    rows = [
        {"item_id": "i1", "artist_name": "Artist A", "feedback_type": "like"},
        {"item_id": "i2", "artist_name": "Artist A", "feedback_type": "dislike"},
    ]
    result = compute_feedback_adjustments(rows)
    # like (+1.0) + dislike (-1.5) nets negative -> multiplier below 1.0
    assert result["artist_multiplier"]["Artist A"] < 1.0
