"""Part D — simple, transparent feedback -> future-score adjustment.

Deliberately NOT reinforcement learning, bandits, or online learning: this
is a deterministic weighted adjustment computed fresh from a user's
feedback history each time recommendations are requested. "dislike" and
"hide" hard-exclude the specific item from future candidate pools;
every feedback type also nudges a per-artist preference multiplier used
in ml/recommendation/hybrid.py's scoring.
"""

from __future__ import annotations

from collections import defaultdict

FEEDBACK_WEIGHTS = {
    "like": 1.0,
    "save": 1.2,
    "replay": 0.8,
    "skip": -0.3,
    "dislike": -1.5,
    "hide": -2.0,
}

HARD_EXCLUDE_TYPES = {"dislike", "hide"}

# Bounds on the artist preference multiplier so a burst of feedback can't
# push a single artist's contribution to an extreme.
MULTIPLIER_MIN = 0.3
MULTIPLIER_MAX = 1.8
MULTIPLIER_STEP = 0.15


def compute_feedback_adjustments(feedback_rows: list[dict]) -> dict:
    """feedback_rows: [{"item_id": str, "artist_name": str, "feedback_type": str}, ...]

    Returns {"artist_multiplier": {artist_name: float}, "excluded_items": set[str]}.
    """
    artist_scores: dict[str, float] = defaultdict(float)
    excluded_items: set[str] = set()

    for row in feedback_rows:
        ftype = row["feedback_type"]
        weight = FEEDBACK_WEIGHTS.get(ftype, 0.0)
        artist_scores[row["artist_name"]] += weight
        if ftype in HARD_EXCLUDE_TYPES:
            excluded_items.add(row["item_id"])

    artist_multiplier = {
        artist: max(MULTIPLIER_MIN, min(MULTIPLIER_MAX, 1.0 + MULTIPLIER_STEP * score))
        for artist, score in artist_scores.items()
    }
    return {"artist_multiplier": artist_multiplier, "excluded_items": excluded_items}
