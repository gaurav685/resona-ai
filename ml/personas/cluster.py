"""Persona discovery: cluster Last.fm 1K users on their actual Listening DNA.

Pipeline: Listening DNA features (ml/features/listening_dna.py) ->
standardize -> KMeans (k selected by silhouette score, scanned over a small
range) -> PCA(2) for visualization -> cluster profiles derived from actual
per-cluster feature means (never hard-coded). DBSCAN is run for comparison
only; whichever result is real is reported, including a "found nothing
better than noise" outcome if that's what happens.

Usage:
    python ml/personas/cluster.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from features.listening_dna import NUMERIC_FEATURE_COLUMNS, compute_all  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = REPO_ROOT / "data" / "processed" / "lastfm_1k" / "listening_events.csv"
MODELS_DIR = REPO_ROOT / "models" / "personas"
RANDOM_SEED = 42
K_RANGE = range(2, 9)
MIN_EVENTS_FOR_PROFILE = 20  # users with fewer events give unstable session/rate stats


def build_feature_matrix() -> pd.DataFrame:
    events = pd.read_csv(EVENTS_PATH)
    dna = compute_all(events)
    before = len(dna)
    dna = dna[dna["n_events"] >= MIN_EVENTS_FOR_PROFILE].reset_index(drop=True)
    print(f"Listening DNA computed for {before} users; {len(dna)} retained "
          f"(>= {MIN_EVENTS_FOR_PROFILE} events, for stable session/rate statistics)")
    return dna


def choose_k(X: np.ndarray) -> tuple[int, dict]:
    scores = {}
    for k in K_RANGE:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
        labels = km.fit_predict(X)
        sil = silhouette_score(X, labels)
        db = davies_bouldin_score(X, labels)
        scores[k] = {"silhouette": float(sil), "davies_bouldin": float(db)}
        print(f"  k={k}: silhouette={sil:.4f}  davies_bouldin={db:.4f}")
    best_k = max(scores, key=lambda k: scores[k]["silhouette"])
    return best_k, scores


def name_cluster(centroid_z: pd.Series, top_n: int = 2) -> str:
    """Derive a human-readable cluster name from its standardized centroid.

    Picks the top_n features with the largest |z-score| and describes them
    as High/Low <feature>. Never a hard-coded lookup — purely a function of
    the actual centroid values.
    """
    ranked = centroid_z.abs().sort_values(ascending=False).index[:top_n]
    parts = []
    for feat in ranked:
        direction = "High" if centroid_z[feat] > 0 else "Low"
        label = feat.replace("_utc", "").replace("_", " ").title()
        parts.append(f"{direction} {label}")
    return " / ".join(parts)


def main() -> None:
    dna = build_feature_matrix()
    X_df = dna[NUMERIC_FEATURE_COLUMNS].copy()

    scaler = StandardScaler()
    X = scaler.fit_transform(X_df)

    print("\nSelecting k via silhouette score:")
    best_k, k_scores = choose_k(X)
    print(f"Selected k={best_k} (highest silhouette score)")

    kmeans = KMeans(n_clusters=best_k, random_state=RANDOM_SEED, n_init=10)
    labels = kmeans.fit_predict(X)
    sil = silhouette_score(X, labels)
    db = davies_bouldin_score(X, labels)
    print(f"\nFinal KMeans(k={best_k}): silhouette={sil:.4f}  davies_bouldin={db:.4f}")

    # DBSCAN comparison (reported honestly, whatever it finds).
    dbscan = DBSCAN(eps=1.5, min_samples=5)
    db_labels = dbscan.fit_predict(X)
    n_db_clusters = len(set(db_labels)) - (1 if -1 in db_labels else 0)
    n_noise = int((db_labels == -1).sum())
    print(f"DBSCAN(eps=1.5, min_samples=5) comparison: {n_db_clusters} clusters, "
          f"{n_noise}/{len(db_labels)} points labeled noise")
    if n_db_clusters >= 2:
        db_sil = silhouette_score(X, db_labels) if n_noise < len(db_labels) else None
        print(f"  DBSCAN silhouette (excluding noise handling not applied): {db_sil}")

    pca = PCA(n_components=2, random_state=RANDOM_SEED)
    coords = pca.fit_transform(X)
    print(f"\nPCA(2) explained variance ratio: {pca.explained_variance_ratio_.tolist()}")

    dna["cluster_id"] = labels
    dna["pca_x"] = coords[:, 0]
    dna["pca_y"] = coords[:, 1]

    global_mean = X_df.mean()
    global_std = X_df.std().replace(0, 1)

    profiles = {}
    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        cluster_df = X_df[mask]
        centroid = cluster_df.mean()
        centroid_z = (centroid - global_mean) / global_std
        name = name_cluster(centroid_z)
        profiles[int(cluster_id)] = {
            "name": name,
            "n_users": int(mask.sum()),
            "feature_means": {k: float(v) for k, v in centroid.items()},
            "feature_z_scores_vs_global": {k: float(v) for k, v in centroid_z.items()},
        }
        print(f"\nCluster {cluster_id} — \"{name}\" ({mask.sum()} users)")
        for feat in NUMERIC_FEATURE_COLUMNS:
            print(f"    {feat:32s} mean={centroid[feat]:8.3f}  z={centroid_z[feat]:+.2f}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(kmeans, MODELS_DIR / "kmeans.joblib")
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")
    joblib.dump(pca, MODELS_DIR / "pca.joblib")

    dna[["user_id", "cluster_id", "pca_x", "pca_y", "n_events", "n_sessions"] + NUMERIC_FEATURE_COLUMNS].to_csv(
        MODELS_DIR / "user_cluster_assignments.csv", index=False
    )

    metadata = {
        "algorithm": "KMeans",
        "k_selected": best_k,
        "k_scan_scores": {str(k): v for k, v in k_scores.items()},
        "silhouette_score": float(sil),
        "davies_bouldin_score": float(db),
        "dbscan_comparison": {"n_clusters": n_db_clusters, "n_noise": n_noise, "eps": 1.5, "min_samples": 5},
        "pca_explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "feature_columns": NUMERIC_FEATURE_COLUMNS,
        "n_users_clustered": len(dna),
        "min_events_threshold": MIN_EVENTS_FOR_PROFILE,
        "random_seed": RANDOM_SEED,
        "cluster_profiles": profiles,
    }
    with open(MODELS_DIR / "persona_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved cluster model, assignments, and metadata to {MODELS_DIR}")


if __name__ == "__main__":
    main()
