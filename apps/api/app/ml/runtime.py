"""Loads Phase 3 ML artifacts (trained models, cluster assignments,
processed listening-event data) and exposes them to the FastAPI routes.

All artifacts are read from the local models/ and data/processed/
directories produced by the ml/ scripts — nothing here retrains or
fabricates anything; it's inference-time loading only.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "ml"))

from features.listening_dna import compute_listening_dna  # noqa: E402

MODELS_PERSONALITY_DIR = REPO_ROOT / "models" / "personality"
MODELS_PERSONAS_DIR = REPO_ROOT / "models" / "personas"
LASTFM_EVENTS_PATH = REPO_ROOT / "data" / "processed" / "lastfm_1k" / "listening_events.csv"


class ArtifactUnavailable(Exception):
    """Raised when a requested model/data artifact hasn't been produced yet."""


@lru_cache(maxsize=1)
def get_listening_events_df() -> pd.DataFrame:
    if not LASTFM_EVENTS_PATH.exists():
        raise ArtifactUnavailable(
            f"{LASTFM_EVENTS_PATH} not found — run scripts/process_datasets.py --dataset lastfm_1k"
        )
    df = pd.read_csv(LASTFM_EVENTS_PATH)
    df["played_at"] = pd.to_datetime(df["played_at"], utc=True)
    return df


def known_user_ids() -> set[str]:
    return set(get_listening_events_df()["user_id"].unique())


def get_listening_dna(user_id: str) -> dict:
    events = get_listening_events_df()
    if user_id not in set(events["user_id"].unique()):
        raise ArtifactUnavailable(f"unknown user_id: {user_id}")
    dna = compute_listening_dna(events, user_id)
    return dna.to_dict()


@lru_cache(maxsize=1)
def _persona_metadata() -> dict:
    path = MODELS_PERSONAS_DIR / "persona_metadata.json"
    if not path.exists():
        raise ArtifactUnavailable(f"{path} not found — run ml/personas/cluster.py")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _persona_assignments() -> pd.DataFrame:
    path = MODELS_PERSONAS_DIR / "user_cluster_assignments.csv"
    if not path.exists():
        raise ArtifactUnavailable(f"{path} not found — run ml/personas/cluster.py")
    df = pd.read_csv(path)
    df["user_id"] = df["user_id"].astype(str)
    return df


def get_persona(user_id: str) -> dict:
    assignments = _persona_assignments()
    row = assignments[assignments["user_id"] == user_id]
    if row.empty:
        raise ArtifactUnavailable(
            f"no persona assignment for user_id={user_id} "
            f"(user may have had fewer than the minimum events required for clustering)"
        )
    row = row.iloc[0]
    metadata = _persona_metadata()
    cluster_id = int(row["cluster_id"])
    profile = metadata["cluster_profiles"][str(cluster_id)]
    return {
        "user_id": user_id,
        "cluster_id": cluster_id,
        "persona_name": profile["name"],
        "cluster_size": profile["n_users"],
        "pca_coordinates": {"x": float(row["pca_x"]), "y": float(row["pca_y"])},
        "cluster_feature_means": profile["feature_means"],
        "algorithm": metadata["algorithm"],
        "model_version": f"kmeans-k{metadata['k_selected']}",
        "silhouette_score": metadata["silhouette_score"],
    }


@lru_cache(maxsize=1)
def get_personality_model_info() -> dict:
    path = MODELS_PERSONALITY_DIR / "selected_model.json"
    if not path.exists():
        raise ArtifactUnavailable(
            f"{path} not found — run ml/personality/train_classical.py, "
            f"ml/personality/train_nn.py, then ml/personality/compare_and_select.py"
        )
    with open(path, "r", encoding="utf-8") as f:
        info = json.load(f)
    model_path = MODELS_PERSONALITY_DIR / info["artifact_file"]
    if info["model_type"] == "pytorch":
        import torch
        sys.path.insert(0, str(REPO_ROOT / "ml" / "personality"))
        from nn_model import PersonalityNet  # noqa: E402

        checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
        net = PersonalityNet(input_dim=len(info["feature_columns"]))
        net.load_state_dict(checkpoint["model_state_dict"])
        net.eval()
        info["_model"] = net
        info["_scaler"] = checkpoint.get("scaler")
    else:
        info["_model"] = joblib.load(model_path)
        info["_scaler"] = None
    return info


def predict_personality(features: dict[str, float]) -> dict:
    info = get_personality_model_info()
    feature_columns = info["feature_columns"]
    trait_columns = info["trait_columns"]
    missing = [c for c in feature_columns if c not in features]
    if missing:
        raise ValueError(f"missing required features: {missing}")

    x = np.array([[features[c] for c in feature_columns]], dtype=np.float32)

    model = info["_model"]
    if info["model_type"] == "pytorch":
        import torch

        scaler = info["_scaler"]
        x_scaled = scaler.transform(x) if scaler is not None else x
        with torch.no_grad():
            pred = model(torch.from_numpy(x_scaled.astype(np.float32))).numpy()[0]
        confidence = None
        confidence_reason = "not supported for the PyTorch model in this MVP"
    elif info["model_type"] == "random_forest":
        # MultiOutputRegressor wraps one RandomForestRegressor per trait —
        # each has .estimators_ (individual trees), so per-trait prediction
        # std across trees is a real, computable uncertainty estimate.
        pred = model.predict(x)[0]
        per_trait_std = [
            float(np.std([tree.predict(x)[0] for tree in sub_model.estimators_]))
            for sub_model in model.estimators_
        ]
        confidence = per_trait_std
        confidence_reason = None
    else:
        pred = model.predict(x)[0]
        confidence = None
        confidence_reason = "not supported by this model type"

    global_importance = info.get("global_feature_importance", [])

    results = []
    for i, trait in enumerate(trait_columns):
        trait_confidence = confidence[i] if isinstance(confidence, list) else confidence
        results.append(
            {
                "trait": trait,
                "score": float(pred[i]),
                "confidence": trait_confidence,
                "confidence_note": confidence_reason,
                "model_version": info["model_version"],
                "important_features": global_importance[:5],
            }
        )
    return {
        "predictions": results,
        "disclaimer": "Model-estimated associations, not a psychological diagnosis.",
    }
