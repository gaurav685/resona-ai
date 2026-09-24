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

from features.listening_dna import compute_listening_dna, sessionize  # noqa: E402
from features.context import compute_current_context  # noqa: E402
from features.taste_evolution import compute_taste_evolution  # noqa: E402
from features.upload_parser import parse_uploaded_file, UnrecognizedUploadFormat  # noqa: E402

MODELS_PERSONALITY_DIR = REPO_ROOT / "models" / "personality"
MODELS_PERSONAS_DIR = REPO_ROOT / "models" / "personas"
MODELS_RECOMMENDATION_DIR = REPO_ROOT / "models" / "recommendation"
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


@lru_cache(maxsize=1)
def list_users() -> list[dict]:
    """Real Last.fm 1K users with their actual event counts — used by the
    frontend's demo-listener picker (there is no auth/signup flow in this
    MVP, so a real user must be selected explicitly rather than assumed)."""
    events = get_listening_events_df()
    counts = events.groupby("user_id").size().sort_values(ascending=False)
    return [{"user_id": uid, "n_events": int(n)} for uid, n in counts.items()]


def get_listening_dna(user_id: str) -> dict:
    events = get_listening_events_df()
    if user_id not in set(events["user_id"].unique()):
        raise ArtifactUnavailable(f"unknown user_id: {user_id}")
    dna = compute_listening_dna(events, user_id)
    return dna.to_dict()


def get_taste_evolution(user_id: str) -> dict:
    events = get_listening_events_df()
    if user_id not in set(events["user_id"].unique()):
        raise ArtifactUnavailable(f"unknown user_id: {user_id}")
    periods = compute_taste_evolution(events, user_id)
    return {"user_id": user_id, "periods": periods}


def get_current_context(user_id: str) -> dict:
    events = get_listening_events_df()
    if user_id not in set(events["user_id"].unique()):
        raise ArtifactUnavailable(f"unknown user_id: {user_id}")
    result = compute_current_context(events, user_id)
    return result.to_dict()


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
        "cluster_feature_z_scores": profile["feature_z_scores_vs_global"],
        "algorithm": metadata["algorithm"],
        "model_version": f"kmeans-k{metadata['k_selected']}",
        "silhouette_score": metadata["silhouette_score"],
    }


@lru_cache(maxsize=1)
def list_personality_sample_participants(limit: int = 30) -> list[dict]:
    """Real participants (and their real feature vectors + actual measured
    Big Five scores) from the beyond_big_five research dataset — this is
    the ONLY dataset in the project with real inputs for the personality
    model (see MODEL_CARD.md). There is no personality data for Last.fm
    users, so the frontend lets a user pick one of these real research
    participants rather than pretending Last.fm listening behavior can
    feed this model."""
    sys.path.insert(0, str(REPO_ROOT / "ml" / "personality"))
    from dataset import load_personality_dataset

    X, y, ids = load_personality_dataset()
    out = []
    for i in range(min(limit, len(X))):
        out.append(
            {
                "participant_id": str(ids.iloc[i]),
                "features": {c: float(X.iloc[i][c]) for c in X.columns},
                "actual_traits": {c: float(y.iloc[i][c]) for c in y.columns},
            }
        )
    return out


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


# ---------------------------------------------------------------------------
# Phase 4: content similarity + hybrid recommender
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _content_similarity_artifacts() -> dict:
    sim_path = MODELS_RECOMMENDATION_DIR / "content_similarity_matrix.npy"
    catalog_path = MODELS_RECOMMENDATION_DIR / "content_track_catalog.csv"
    index_path = MODELS_RECOMMENDATION_DIR / "content_similarity_index.joblib"
    if not (sim_path.exists() and catalog_path.exists() and index_path.exists()):
        raise ArtifactUnavailable(
            f"content similarity artifacts not found — run ml/recommendation/content_similarity.py"
        )
    sim = np.load(sim_path)
    catalog = pd.read_csv(catalog_path)
    index = joblib.load(index_path)
    track_ids = index["track_ids"]
    return {"sim": sim, "catalog": catalog, "track_ids": track_ids, "track_idx": {t: i for i, t in enumerate(track_ids)}}


def get_similar_tracks(track_id: str, limit: int = 10) -> dict:
    art = _content_similarity_artifacts()
    if track_id not in art["track_idx"]:
        raise ArtifactUnavailable(
            f"unknown track_id: {track_id} (this catalog is the 745-track beyond_big_five "
            f"audio-feature set, not Last.fm or MSD track ids — see MODEL_CARD.md)"
        )
    idx = art["track_idx"][track_id]
    sims = art["sim"][idx]
    top_idx = np.argsort(sims)[::-1][:limit]
    results = [
        {"track_id": art["track_ids"][i], "similarity": float(sims[i])}
        for i in top_idx if sims[i] > 0
    ]
    return {
        "track_id": track_id,
        "similar_tracks": results,
        "method": "cosine similarity over 29 real audio/emotion features (beyond_big_five dataset)",
    }


@lru_cache(maxsize=1)
def _recommender_artifacts():
    sys.path.insert(0, str(REPO_ROOT / "ml" / "recommendation"))
    from hybrid import RecommenderUnavailable as _Unavailable, load_artifacts

    try:
        return load_artifacts()
    except _Unavailable as e:
        raise ArtifactUnavailable(str(e)) from e


def get_recommendations(
    user_id: str,
    limit: int = 10,
    novelty: float | None = None,
    context: str | None = None,
    feedback_rows: list[dict] | None = None,
) -> dict:
    sys.path.insert(0, str(REPO_ROOT / "ml" / "recommendation"))
    from hybrid import RecommenderUnavailable as _Unavailable, recommend
    from feedback import compute_feedback_adjustments

    artifacts = _recommender_artifacts()
    feedback = compute_feedback_adjustments(feedback_rows) if feedback_rows else None
    try:
        return recommend(user_id, limit=limit, novelty=novelty, context=context, artifacts=artifacts, feedback=feedback)
    except _Unavailable as e:
        raise ArtifactUnavailable(str(e)) from e


# ---------------------------------------------------------------------------
# "Bring your own history": Spotify / YouTube Music / Apple Music uploads
# ---------------------------------------------------------------------------

def analyze_uploaded_history(files: list[tuple[str, bytes]], service: str) -> dict:
    """Parses a listener's own export, runs it through the same real
    Listening DNA / context / taste-evolution / recommendation pipeline
    used for the Last.fm demo listeners. Nothing here is fabricated for a
    catalog gap: recommendation co-listening similarity is only as good as
    the real overlap between the upload and our fixed Last.fm catalog, and
    that overlap is reported honestly rather than papered over.

    Nothing from the upload is written to disk; it's processed in memory
    for this one request. (Recommendation evidence for any resulting
    recommendations is still persisted to SQLite, same as every other
    recommendation this API returns — see MODEL_CARD.md / README privacy
    section.)
    """
    import uuid

    sys.path.insert(0, str(REPO_ROOT / "ml" / "recommendation"))
    from catalog import item_id as _item_id
    from hybrid import RecommenderArtifacts, recommend

    frames = []
    parse_errors: dict[str, str] = {}
    for filename, raw in files:
        try:
            df = parse_uploaded_file(filename, raw, service, user_id="_pending_")
            if not df.empty:
                frames.append(df)
        except UnrecognizedUploadFormat as e:
            parse_errors[filename] = str(e)

    if not frames:
        raise ArtifactUnavailable(
            "Could not parse any events from the uploaded file(s). "
            + ("; ".join(f"{k}: {v}" for k, v in parse_errors.items()) if parse_errors else "No recognizable rows found.")
        )

    user_id = f"uploaded_{uuid.uuid4().hex[:12]}"
    events = pd.concat(frames, ignore_index=True)
    events["user_id"] = user_id
    events = events.drop_duplicates(subset=["user_id", "played_at", "artist_name", "track_title"])
    events["played_at"] = pd.to_datetime(events["played_at"], utc=True)
    events = sessionize(events)

    dna = compute_listening_dna(events, user_id).to_dict()
    context = compute_current_context(events, user_id).to_dict()
    evolution = compute_taste_evolution(events, user_id)

    catalog_item_ids = {
        _item_id(a, t) for a, t in zip(events["artist_name"], events["track_title"])
    }
    artifacts = _recommender_artifacts()
    n_matched = len(catalog_item_ids & set(artifacts.item_idx.keys()))

    uploaded_with_item_id = events.assign(
        item_id=[_item_id(a, t) for a, t in zip(events["artist_name"], events["track_title"])]
    )[["user_id", "artist_name", "track_title", "played_at", "item_id"]]
    merged_events = pd.concat([artifacts.events, uploaded_with_item_id], ignore_index=True)
    merged_artifacts = RecommenderArtifacts(
        events=merged_events, catalog=artifacts.catalog, sim_matrix=artifacts.sim_matrix, item_ids=artifacts.item_ids
    )

    try:
        recommendations = recommend(user_id, limit=10, artifacts=merged_artifacts)
    except Exception:
        recommendations = None

    return {
        "session_user_id": user_id,
        "service": service,
        "n_files": len(files),
        "n_events_parsed": len(events),
        "n_tracks_matched_catalog": n_matched,
        "n_distinct_tracks": len(catalog_item_ids),
        "parse_errors": parse_errors,
        "listening_dna": dna,
        "current_context": context,
        "taste_evolution": {"user_id": user_id, "periods": evolution},
        "recommendations": recommendations,
        "note": (
            f"{n_matched} of {len(catalog_item_ids)} distinct tracks you listened to matched our "
            "recommendation catalog (top 1,500 Last.fm items by unique listener) closely enough "
            "(same artist + track name) to contribute a co-listening similarity signal — "
            "recommendations lean more on artist preference and novelty when overlap is low. "
            "This upload was processed in memory and not saved to disk."
        ),
    }
