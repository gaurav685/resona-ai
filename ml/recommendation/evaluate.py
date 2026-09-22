"""Evaluates the hybrid recommender against a most-popular baseline using
an actual leave-last-N-out split per user — no leakage: the catalog,
item-item similarity matrix, and every user-preference signal used for
scoring are rebuilt from the TRAIN split only; held-out TEST items are
never seen by the recommender before being used as ground truth.

Metrics (computed from the actual overlap between recommended items and
each user's held-out test items): Precision@K, Recall@K, NDCG@K,
HitRate@K, Coverage, Diversity, Novelty.

Whatever the numbers say is what gets reported — this script does not
decide in advance that the hybrid recommender wins.

Usage:
    python ml/recommendation/evaluate.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import build_item_catalog, build_user_item_matrix, load_events  # noqa: E402
from hybrid import RecommenderArtifacts, RecommenderUnavailable, diversify, score_candidates  # noqa: E402
from item_similarity import build_item_item_similarity  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = REPO_ROOT / "models" / "recommendation" / "evaluation_results.json"

MIN_EVENTS_FOR_EVAL = 10
TEST_FRACTION = 0.2
MAX_TEST_ITEMS = 5
K_VALUES = (5, 10)
RANDOM_SEED = 42


def train_test_split_events(events: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, set[str]]]:
    """Per user: hold out their last min(MAX_TEST_ITEMS, 20%) events
    (by timestamp) as test. Returns (train_events_df, {user_id: {test_item_ids}})."""
    train_frames = []
    test_sets: dict[str, set[str]] = {}
    for uid, group in events.groupby("user_id"):
        group = group.sort_values("played_at")
        n = len(group)
        if n < MIN_EVENTS_FOR_EVAL:
            train_frames.append(group)  # not enough history to evaluate; keep as train-only
            continue
        n_test = min(MAX_TEST_ITEMS, max(1, int(n * TEST_FRACTION)))
        train_frames.append(group.iloc[:-n_test])
        test_sets[uid] = set(group.iloc[-n_test:]["item_id"].unique())
    train_events = pd.concat(train_frames, ignore_index=True)
    return train_events, test_sets


def ndcg_at_k(recommended_ids: list[str], relevant_ids: set[str], k: int) -> float:
    dcg = 0.0
    for i, item_id in enumerate(recommended_ids[:k]):
        if item_id in relevant_ids:
            dcg += 1.0 / np.log2(i + 2)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
    return float(dcg / idcg) if idcg > 0 else 0.0


def evaluate_list(recommended_ids: list[str], relevant_ids: set[str], k: int) -> dict:
    top_k = recommended_ids[:k]
    hits = len(set(top_k) & relevant_ids)
    precision = hits / k
    recall = hits / len(relevant_ids) if relevant_ids else 0.0
    hit_rate = 1.0 if hits > 0 else 0.0
    ndcg = ndcg_at_k(recommended_ids, relevant_ids, k)
    return {"precision": precision, "recall": recall, "ndcg": ndcg, "hit_rate": hit_rate}


def diversity_of_list(item_ids: list[str], sim_matrix: np.ndarray, item_idx: dict) -> float:
    idxs = [item_idx[i] for i in item_ids if i in item_idx]
    if len(idxs) < 2:
        return None
    sims = [sim_matrix[a, b] for a in idxs for b in idxs if a != b]
    return float(1.0 - np.mean(sims))


def main() -> None:
    t0 = time.time()
    events = load_events()
    train_events, test_sets = train_test_split_events(events)
    eval_users = list(test_sets.keys())
    print(f"Evaluating on {len(eval_users)} users with >= {MIN_EVENTS_FOR_EVAL} events "
          f"(held out up to {MAX_TEST_ITEMS} most-recent events each)")

    catalog = build_item_catalog(train_events)
    matrix, user_ids, item_ids = build_user_item_matrix(train_events, catalog)
    sim_matrix = build_item_item_similarity(matrix, item_ids)
    artifacts = RecommenderArtifacts(events=train_events, catalog=catalog, sim_matrix=sim_matrix, item_ids=item_ids)
    print(f"Train-only catalog: {len(catalog)} items, {matrix.shape[0]} users")

    # Non-personalized baseline: global most-popular train items (by
    # unique listeners), same list for every user.
    most_popular = catalog.sort_values("n_unique_users", ascending=False)["item_id"].tolist()

    results_per_k = {k: {"resona": [], "baseline": []} for k in K_VALUES}
    resona_recommended_sets = {k: set() for k in K_VALUES}
    baseline_recommended_sets = {k: set() for k in K_VALUES}
    resona_diversities = {k: [] for k in K_VALUES}
    baseline_diversities = {k: [] for k in K_VALUES}
    resona_novelties = {k: [] for k in K_VALUES}
    baseline_novelties = {k: [] for k in K_VALUES}

    popularity_by_item = dict(zip(catalog["item_id"], catalog["popularity"]))
    n_scored = 0
    n_skipped_no_candidates = 0

    for uid in eval_users:
        relevant = test_sets[uid]
        try:
            scored = score_candidates(artifacts, uid)
        except RecommenderUnavailable:
            n_skipped_no_candidates += 1
            continue
        if scored.empty:
            n_skipped_no_candidates += 1
            continue

        user_train_items = set(train_events[train_events["user_id"] == uid]["item_id"].unique())
        baseline_ids = [i for i in most_popular if i not in user_train_items]

        max_k = max(K_VALUES)
        resona_ranked = diversify(scored, artifacts, limit=max_k)
        resona_ids_full = resona_ranked["item_id"].tolist()

        n_scored += 1
        for k in K_VALUES:
            resona_ids = resona_ids_full[:k]
            baseline_ids_k = baseline_ids[:k]

            results_per_k[k]["resona"].append(evaluate_list(resona_ids, relevant, k))
            results_per_k[k]["baseline"].append(evaluate_list(baseline_ids_k, relevant, k))

            resona_recommended_sets[k].update(resona_ids)
            baseline_recommended_sets[k].update(baseline_ids_k)

            rd = diversity_of_list(resona_ids, sim_matrix, artifacts.item_idx)
            bd = diversity_of_list(baseline_ids_k, sim_matrix, artifacts.item_idx)
            if rd is not None:
                resona_diversities[k].append(rd)
            if bd is not None:
                baseline_diversities[k].append(bd)

            resona_novelties[k].append(float(np.mean([1 - popularity_by_item.get(i, 0) for i in resona_ids]) if resona_ids else 0))
            baseline_novelties[k].append(float(np.mean([1 - popularity_by_item.get(i, 0) for i in baseline_ids_k]) if baseline_ids_k else 0))

    elapsed = time.time() - t0
    print(f"Scored {n_scored} users ({n_skipped_no_candidates} skipped: no candidates) in {elapsed:.1f}s\n")

    summary = {"n_users_evaluated": n_scored, "n_users_skipped": n_skipped_no_candidates, "by_k": {}}
    for k in K_VALUES:
        def avg(method, metric):
            vals = [r[metric] for r in results_per_k[k][method]]
            return float(np.mean(vals)) if vals else None

        k_summary = {
            "resona": {
                "precision": avg("resona", "precision"),
                "recall": avg("resona", "recall"),
                "ndcg": avg("resona", "ndcg"),
                "hit_rate": avg("resona", "hit_rate"),
                "coverage": len(resona_recommended_sets[k]) / len(catalog),
                "diversity": float(np.mean(resona_diversities[k])) if resona_diversities[k] else None,
                "novelty": float(np.mean(resona_novelties[k])),
            },
            "baseline_most_popular": {
                "precision": avg("baseline", "precision"),
                "recall": avg("baseline", "recall"),
                "ndcg": avg("baseline", "ndcg"),
                "hit_rate": avg("baseline", "hit_rate"),
                "coverage": len(baseline_recommended_sets[k]) / len(catalog),
                "diversity": float(np.mean(baseline_diversities[k])) if baseline_diversities[k] else None,
                "novelty": float(np.mean(baseline_novelties[k])),
            },
        }
        summary["by_k"][k] = k_summary

        print(f"--- K={k} ---")
        print(f"{'metric':12s} {'resona':>10s} {'baseline':>10s}")
        for metric in ("precision", "recall", "ndcg", "hit_rate", "coverage", "diversity", "novelty"):
            r = k_summary["resona"][metric]
            b = k_summary["baseline_most_popular"][metric]
            r_str = f"{r:.4f}" if r is not None else "n/a"
            b_str = f"{b:.4f}" if b is not None else "n/a"
            print(f"{metric:12s} {r_str:>10s} {b_str:>10s}")
        print()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
