"""Builds the Last.fm item catalog used by the recommender: one row per
distinct (artist, track) pair actually present in the processed listening
events, with real play counts and popularity — no synthetic items.

Item ids are stable md5 hashes of "artist||title" so they can be reused
across runs without a database.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = REPO_ROOT / "data" / "processed" / "lastfm_1k" / "listening_events.csv"

# Candidate/similarity pool is capped to the most-played items so the
# item-item similarity matrix and per-request candidate generation stay
# cheap — this is a deliberate, documented MVP tradeoff, not an attempt to
# do a full-catalog computation synchronously.
TOP_N_ITEMS = 1500


def item_id(artist_name: str, track_title: str) -> str:
    key = f"{str(artist_name).strip().lower()}||{str(track_title).strip().lower()}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:16]


def load_events() -> pd.DataFrame:
    df = pd.read_csv(EVENTS_PATH)
    df["played_at"] = pd.to_datetime(df["played_at"], utc=True)
    df["item_id"] = [item_id(a, t) for a, t in zip(df["artist_name"], df["track_title"])]
    return df


def build_item_catalog(events: pd.DataFrame, top_n: int = TOP_N_ITEMS) -> pd.DataFrame:
    """One row per (artist, track): item_id, artist_name, track_title,
    play_count, n_unique_users, popularity (play_count normalized to
    [0,1] by the most-played item)."""
    grouped = events.groupby("item_id").agg(
        artist_name=("artist_name", "first"),
        track_title=("track_title", "first"),
        play_count=("item_id", "size"),
        n_unique_users=("user_id", "nunique"),
    ).reset_index()
    # Rank by unique listeners, not raw play count — a track replayed 100x
    # by one user isn't "popular", it's one person's habit. play_count is
    # kept as secondary info; popularity (used for novelty/coverage) is
    # unique-listener-based.
    grouped = grouped.sort_values(["n_unique_users", "play_count"], ascending=False).head(top_n).reset_index(drop=True)
    max_users = grouped["n_unique_users"].max()
    grouped["popularity"] = grouped["n_unique_users"] / max_users
    return grouped


def build_user_item_matrix(events: pd.DataFrame, catalog: pd.DataFrame) -> tuple[sparse.csr_matrix, list[str], list[str]]:
    """Binary user x item "played" matrix restricted to catalog items.

    Returns (matrix, user_ids, item_ids) where matrix rows follow user_ids
    order and columns follow item_ids order.
    """
    catalog_items = set(catalog["item_id"])
    filtered = events[events["item_id"].isin(catalog_items)]

    user_ids = sorted(filtered["user_id"].unique())
    item_ids = list(catalog["item_id"])
    user_idx = {u: i for i, u in enumerate(user_ids)}
    item_idx = {it: i for i, it in enumerate(item_ids)}

    counts = filtered.groupby(["user_id", "item_id"]).size().reset_index(name="n")
    rows = counts["user_id"].map(user_idx).to_numpy()
    cols = counts["item_id"].map(item_idx).to_numpy()
    data = counts["n"].to_numpy()

    matrix = sparse.csr_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))
    return matrix, user_ids, item_ids


if __name__ == "__main__":
    events = load_events()
    catalog = build_item_catalog(events)
    matrix, user_ids, item_ids = build_user_item_matrix(events, catalog)
    print(f"{len(events):,} events, {events['item_id'].nunique():,} distinct items total")
    print(f"catalog: top {len(catalog)} items by play count")
    print(f"user-item matrix: {matrix.shape}, {matrix.nnz:,} non-zero entries "
          f"({matrix.nnz / (matrix.shape[0] * matrix.shape[1]) * 100:.2f}% density)")
    print(catalog.head(5).to_string())
