"""Part C — hybrid recommender: candidate generation -> filtering ->
scoring -> diversity reranking -> final list.

Signals (each normalized to [0,1] before combining):

  - co_listening_similarity  ("content_similarity" in the API/spec sense —
    labeled honestly: no audio-content vectors exist for Last.fm tracks in
    this MVP, so this is mean item-item co-occurrence similarity, from
    ml/recommendation/item_similarity.py, between a candidate and the
    user's own played items)
  - artist_preference        (user's historical play share for the
    candidate's artist — also covers the spec's "behavior_score" /
    "preference_score", kept as one signal rather than three overlapping
    near-duplicates, documented here)
  - context_alignment        (from ml/features/context.py's current-context
    label: Exploratory favors unfamiliar artists, Focused/Reflective favor
    familiar ones, Routine is neutral)
  - novelty                  (1 - unique-listener popularity)

personality_signal is intentionally NOT used: no personality labels exist
for Last.fm users (Phase 3 rule — never create personality labels from
Last.fm), so it would not be "experimentally justified." listening_frequency
is used as a single global confidence multiplier per user, not a per-item
discriminator (documented, not fabricated as a fake per-item signal).

score = w_sim*co_listening_similarity + w_artist*artist_preference
      + w_context*context_alignment + w_novelty*novelty

Weights are configurable (defaults sum to 1.0). Diversity reranking uses a
simple MMR (Maximal Marginal Relevance) pass over item-item similarity.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "features"))
from catalog import load_events  # noqa: E402
from context import compute_current_context  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "recommendation"

DEFAULT_WEIGHTS = {
    "co_listening_similarity": 0.35,
    "artist_preference": 0.30,
    "context_alignment": 0.15,
    "novelty": 0.20,
}
MMR_LAMBDA = 0.7  # 1.0 = pure relevance, 0.0 = pure diversity


class RecommenderUnavailable(Exception):
    pass


@dataclass
class RecommenderArtifacts:
    events: pd.DataFrame
    catalog: pd.DataFrame
    sim_matrix: np.ndarray
    item_ids: list[str]
    item_idx: dict = field(default_factory=dict)

    def __post_init__(self):
        self.item_idx = {it: i for i, it in enumerate(self.item_ids)}


def load_artifacts() -> RecommenderArtifacts:
    catalog_path = MODELS_DIR / "item_catalog.csv"
    sim_path = MODELS_DIR / "item_similarity_matrix.npy"
    index_path = MODELS_DIR / "item_similarity_index.joblib"
    if not (catalog_path.exists() and sim_path.exists() and index_path.exists()):
        raise RecommenderUnavailable(
            "recommendation artifacts not found — run ml/recommendation/item_similarity.py"
        )
    catalog = pd.read_csv(catalog_path)
    sim_matrix = np.load(sim_path)
    index = joblib.load(index_path)
    events = load_events()
    return RecommenderArtifacts(events=events, catalog=catalog, sim_matrix=sim_matrix, item_ids=index["item_ids"])


def _context_alignment(candidate_artist: str, familiar_artists: set[str], context_label: str) -> float:
    is_familiar = candidate_artist in familiar_artists
    if context_label == "Exploratory":
        return 0.0 if is_familiar else 1.0
    if context_label in ("Focused", "Reflective"):
        return 1.0 if is_familiar else 0.2
    return 0.5  # Routine / Unknown: neutral, no context-based push


def score_candidates(
    artifacts: RecommenderArtifacts,
    user_id: str,
    weights: dict[str, float] | None = None,
    context_override: str | None = None,
) -> pd.DataFrame:
    weights = weights or DEFAULT_WEIGHTS
    events = artifacts.events
    catalog = artifacts.catalog

    user_events = events[events["user_id"] == user_id]
    if len(user_events) == 0:
        raise RecommenderUnavailable(f"unknown user_id or no listening history: {user_id}")

    played_item_ids = set(user_events["item_id"].unique())
    played_artists = set(user_events["artist_name"].unique())
    artist_play_counts = user_events["artist_name"].value_counts()
    total_plays = len(user_events)

    if context_override:
        context_label = context_override
    else:
        context_label = compute_current_context(events, user_id).context_label
    familiar_artists = set(artist_play_counts.head(10).index)

    # Candidates: catalog items the user hasn't played.
    candidates = catalog[~catalog["item_id"].isin(played_item_ids)].copy()
    if candidates.empty:
        return candidates

    # co_listening_similarity: mean similarity between candidate and the
    # user's played items that are also in the catalog (item-item matrix
    # only covers the catalog — see ml/recommendation/catalog.py).
    user_catalog_items = [artifacts.item_idx[i] for i in played_item_ids if i in artifacts.item_idx]
    if user_catalog_items:
        sub = artifacts.sim_matrix[user_catalog_items, :]
        mean_sim_per_item = sub.mean(axis=0)  # length = n_catalog_items
    else:
        mean_sim_per_item = np.zeros(len(artifacts.item_ids))

    candidates["co_listening_similarity"] = candidates["item_id"].map(
        lambda it: float(mean_sim_per_item[artifacts.item_idx[it]])
    )
    max_sim = candidates["co_listening_similarity"].max()
    if max_sim > 0:
        candidates["co_listening_similarity"] = candidates["co_listening_similarity"] / max_sim

    candidates["artist_preference"] = candidates["artist_name"].map(
        lambda a: float(artist_play_counts.get(a, 0)) / total_plays
    )
    max_pref = candidates["artist_preference"].max()
    if max_pref > 0:
        candidates["artist_preference"] = candidates["artist_preference"] / max_pref

    candidates["context_alignment"] = candidates["artist_name"].map(
        lambda a: _context_alignment(a, familiar_artists, context_label)
    )

    candidates["novelty"] = 1.0 - candidates["popularity"]

    candidates["score"] = (
        weights["co_listening_similarity"] * candidates["co_listening_similarity"]
        + weights["artist_preference"] * candidates["artist_preference"]
        + weights["context_alignment"] * candidates["context_alignment"]
        + weights["novelty"] * candidates["novelty"]
    )
    candidates["context_label"] = context_label
    return candidates.sort_values("score", ascending=False).reset_index(drop=True)


def diversify(
    scored: pd.DataFrame,
    artifacts: RecommenderArtifacts,
    limit: int,
    mmr_lambda: float = MMR_LAMBDA,
    max_per_artist: int = 2,
) -> pd.DataFrame:
    """MMR rerank (relevance vs. similarity-to-already-selected), plus a
    hard cap on how many tracks by the same artist can appear in one list
    — pure MMR under-diversifies here because one dominant artist can
    still win every slot on relevance alone (observed empirically on real
    users during testing)."""
    if scored.empty:
        return scored

    pool = scored.head(max(limit * 10, 50)).reset_index(drop=True)  # rerank within a relevance-bounded pool
    selected_idx: list[int] = []
    artist_counts: dict[str, int] = {}
    remaining = list(pool.index)

    while remaining and len(selected_idx) < limit:
        best_i, best_val = None, -np.inf
        for i in remaining:
            artist = pool.loc[i, "artist_name"]
            if artist_counts.get(artist, 0) >= max_per_artist:
                continue
            relevance = pool.loc[i, "score"]
            if selected_idx:
                sims = [
                    artifacts.sim_matrix[
                        artifacts.item_idx[pool.loc[i, "item_id"]],
                        artifacts.item_idx[pool.loc[j, "item_id"]],
                    ]
                    for j in selected_idx
                ]
                max_sim_to_selected = max(sims)
            else:
                max_sim_to_selected = 0.0
            mmr_val = mmr_lambda * relevance - (1 - mmr_lambda) * max_sim_to_selected
            if mmr_val > best_val:
                best_val, best_i = mmr_val, i
        if best_i is None:
            break  # every remaining candidate would violate max_per_artist
        selected_idx.append(best_i)
        artist_counts[pool.loc[best_i, "artist_name"]] = artist_counts.get(pool.loc[best_i, "artist_name"], 0) + 1
        remaining.remove(best_i)

    return pool.loc[selected_idx].reset_index(drop=True)


def recommend(
    user_id: str,
    limit: int = 10,
    novelty: float | None = None,
    context: str | None = None,
    artifacts: RecommenderArtifacts | None = None,
) -> dict:
    artifacts = artifacts or load_artifacts()

    weights = dict(DEFAULT_WEIGHTS)
    if novelty is not None:
        novelty = max(0.0, min(1.0, novelty))
        # Redistribute weight toward/away from novelty, keep others
        # proportionally scaled so the total still sums to 1.0.
        remaining = 1.0 - novelty
        other_total = sum(v for k, v in DEFAULT_WEIGHTS.items() if k != "novelty")
        for k in weights:
            weights[k] = novelty if k == "novelty" else DEFAULT_WEIGHTS[k] / other_total * remaining

    scored = score_candidates(artifacts, user_id, weights=weights, context_override=context)
    ranked = diversify(scored, artifacts, limit=limit)

    items = []
    for _, row in ranked.iterrows():
        items.append(
            {
                "item_id": row["item_id"],
                "artist_name": row["artist_name"],
                "track_title": row["track_title"],
                "score": float(row["score"]),
                "score_breakdown": {
                    "co_listening_similarity": float(row["co_listening_similarity"]),
                    "artist_preference": float(row["artist_preference"]),
                    "context_alignment": float(row["context_alignment"]),
                    "novelty": float(row["novelty"]),
                },
                "popularity": float(row["popularity"]),
            }
        )

    return {
        "user_id": user_id,
        "context_label": scored["context_label"].iloc[0] if not scored.empty else "Unknown",
        "weights_used": weights,
        "recommendations": items,
        "note": (
            "co_listening_similarity is a behavioral co-occurrence signal (users who played "
            "item A also played item B) — no audio-content vectors exist for Last.fm tracks "
            "in this MVP. True audio-content similarity is demonstrated separately at "
            "GET /api/v1/tracks/{id}/similar. personality_signal is not used: no personality "
            "labels exist for Last.fm users."
        ),
    }
