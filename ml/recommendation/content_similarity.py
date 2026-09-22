"""Part B — content-based track similarity from actual audio/emotion
feature vectors.

Track catalog: the 745 unique songs in the beyond_big_five dataset
(data/raw/beyond_big_five/PER_dataset.xls), each with 29 real low-level
audio/emotion features extracted from the audio (rms, brightness,
valence, tension, happy/sad/tender/anger/fear, ...). This is the only
dataset in this project with legitimate per-track audio feature vectors —
Last.fm tracks and the MSD sample have no audio features (see
DATASETS.md), so they are not part of this content-similarity catalog.

Precomputed and cached — GET /api/v1/tracks/{id}/similar never computes
this at request time.

Usage:
    python ml/recommendation/content_similarity.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_XLS = REPO_ROOT / "data" / "raw" / "beyond_big_five" / "PER_dataset.xls"
MODELS_DIR = REPO_ROOT / "models" / "recommendation"

AUDIO_FEATURE_COLUMNS = [
    "rms", "lowenergy", "eventdensity", "pulseclarity",
    "attacktime_mean", "attacktime_std", "attacktime_slope", "attacktime_periodentropy",
    "attackslope_mean", "attackslope_std", "attackslope_slope", "attackslope_periodentropy",
    "zerocross", "brightness", "centroid", "spread", "skewness", "kurtosis",
    "flatness", "mirentropy", "inharmonicity",
    "activity", "valence", "tension", "happy", "sad", "tender", "anger", "fear",
]


def build_track_catalog() -> pd.DataFrame:
    df = pd.read_excel(RAW_XLS)
    per_song = df.groupby("songId")[AUDIO_FEATURE_COLUMNS].first().reset_index()
    per_song["track_id"] = per_song["songId"].astype(str)
    return per_song


def main() -> None:
    catalog = build_track_catalog()
    X = catalog[AUDIO_FEATURE_COLUMNS].to_numpy()
    X_scaled = StandardScaler().fit_transform(X)

    sim = cosine_similarity(X_scaled)
    np.fill_diagonal(sim, 0.0)

    print(f"Content-similarity catalog: {len(catalog)} tracks, {len(AUDIO_FEATURE_COLUMNS)} audio features")
    print(f"{sim.shape[0]}x{sim.shape[1]} cosine similarity matrix, mean similarity "
          f"{sim.mean():.4f}, max {sim.max():.4f}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(MODELS_DIR / "content_similarity_matrix.npy", sim)
    catalog[["track_id"] + AUDIO_FEATURE_COLUMNS].to_csv(MODELS_DIR / "content_track_catalog.csv", index=False)
    joblib.dump({"track_ids": catalog["track_id"].tolist()}, MODELS_DIR / "content_similarity_index.joblib")
    print(f"Saved to {MODELS_DIR}")


if __name__ == "__main__":
    main()
