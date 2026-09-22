"""Precomputes item-item similarity from actual co-listening behavior
(users who played item A also played item B), cached to disk so the API
never runs this at request time.

This is a real, standard item-based collaborative-filtering signal — not
audio content similarity (no audio features exist for Last.fm tracks in
this MVP; see ml/recommendation/content_similarity.py for the dataset
that DOES have real audio features). It stands in for the hybrid
recommender's "content_similarity" term and is labeled accordingly
everywhere it's surfaced.

Usage:
    python ml/recommendation/item_similarity.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import binarize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import TOP_N_ITEMS, build_item_catalog, build_user_item_matrix, load_events  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "recommendation"


def build_item_item_similarity(matrix, item_ids: list[str]) -> np.ndarray:
    """Cosine similarity between item columns of a binary user-item matrix."""
    binary = binarize(matrix)  # co-listening presence, not play count magnitude
    sim = cosine_similarity(binary.T)  # items x items
    np.fill_diagonal(sim, 0.0)  # an item is not its own neighbor
    return sim


def main() -> None:
    t0 = time.time()
    events = load_events()
    catalog = build_item_catalog(events)
    matrix, user_ids, item_ids = build_user_item_matrix(events, catalog)

    sim = build_item_item_similarity(matrix, item_ids)
    elapsed = time.time() - t0

    print(f"Built {sim.shape[0]}x{sim.shape[1]} item-item co-occurrence similarity "
          f"from {matrix.shape[0]} users x {matrix.shape[1]} items in {elapsed:.2f}s")
    print(f"Mean off-diagonal similarity: {sim[sim > 0].mean() if (sim > 0).any() else 0:.4f}")
    print(f"Non-zero similarity pairs: {(sim > 0).sum():,} of {sim.size:,}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(MODELS_DIR / "item_similarity_matrix.npy", sim)
    catalog.to_csv(MODELS_DIR / "item_catalog.csv", index=False)
    joblib.dump({"user_ids": user_ids, "item_ids": item_ids}, MODELS_DIR / "item_similarity_index.joblib")
    print(f"Saved to {MODELS_DIR}")


if __name__ == "__main__":
    main()
