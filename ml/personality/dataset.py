"""Loads the beyond_big_five dataset into a per-participant feature matrix.

Source: data/raw/beyond_big_five/PER_dataset.xls (Kleć et al., 2023 — see
DATASETS.md). Each row is one (participant, song) rating; the same
participant appears in multiple rows with per-song audio/emotion feature
values and a personality profile that is constant across their rows
(verified in scripts/process_datasets.py). To get one training example per
participant, we aggregate (mean) the audio/emotion features and the three
music-attitude ratings (Q1/Q2/Q3) across each participant's rated songs —
this matches the feature set the source paper uses to relate music
preference to personality. Targets are the five Big Five trait scores.

This is real feature engineering on real data — no labels or values here
are fabricated.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_XLS = REPO_ROOT / "data" / "raw" / "beyond_big_five" / "PER_dataset.xls"

AUDIO_EMOTION_COLUMNS = [
    "rms", "lowenergy", "eventdensity", "pulseclarity",
    "attacktime_mean", "attacktime_std", "attacktime_slope", "attacktime_periodentropy",
    "attackslope_mean", "attackslope_std", "attackslope_slope", "attackslope_periodentropy",
    "zerocross", "brightness", "centroid", "spread", "skewness", "kurtosis",
    "flatness", "mirentropy", "inharmonicity",
    "activity", "valence", "tension", "happy", "sad", "tender", "anger", "fear",
]
ATTITUDE_COLUMNS = ["Q1", "Q2", "Q3"]
FEATURE_COLUMNS = AUDIO_EMOTION_COLUMNS + ATTITUDE_COLUMNS  # 32 features

TRAIT_COLUMNS = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]


def load_personality_dataset(xls_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Returns (X, y, participant_ids).

    X: DataFrame, one row per participant, FEATURE_COLUMNS.
    y: DataFrame, one row per participant, TRAIT_COLUMNS.
    participant_ids: Series aligned with X/y index.
    """
    path = xls_path or RAW_XLS
    df = pd.read_excel(path)

    agg = {**{c: "mean" for c in FEATURE_COLUMNS}, **{c: "first" for c in TRAIT_COLUMNS}}
    per_user = df.groupby("userId").agg(agg)

    n_nulls = int(per_user.isnull().sum().sum())
    if n_nulls:
        raise ValueError(f"unexpected {n_nulls} null values after per-participant aggregation")

    X = per_user[FEATURE_COLUMNS].reset_index(drop=True)
    y = per_user[TRAIT_COLUMNS].reset_index(drop=True)
    participant_ids = per_user.index.to_series().reset_index(drop=True)
    return X, y, participant_ids


if __name__ == "__main__":
    X, y, ids = load_personality_dataset()
    print(f"{len(X)} participants, {X.shape[1]} features, {y.shape[1]} traits")
    print("feature columns:", list(X.columns))
    print(y.describe())
