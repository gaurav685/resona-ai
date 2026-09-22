import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "personas"

pytestmark = pytest.mark.skipif(
    not (MODELS_DIR / "persona_metadata.json").exists(),
    reason="run ml/personas/cluster.py first",
)


def test_persona_metadata_has_real_scores():
    with open(MODELS_DIR / "persona_metadata.json", encoding="utf-8") as f:
        meta = json.load(f)
    assert -1.0 <= meta["silhouette_score"] <= 1.0
    assert meta["davies_bouldin_score"] >= 0
    assert meta["k_selected"] in range(2, 9)
    assert len(meta["cluster_profiles"]) == meta["k_selected"]


def test_cluster_names_derived_not_hardcoded():
    with open(MODELS_DIR / "persona_metadata.json", encoding="utf-8") as f:
        meta = json.load(f)
    names = [p["name"] for p in meta["cluster_profiles"].values()]
    # every name must reference an actual feature column from this run
    feature_columns = set(meta["feature_columns"])
    for name in names:
        assert any(
            feat.replace("_utc", "").replace("_", " ").title() in name for feat in feature_columns
        )


def test_cluster_assignments_cover_clustered_users():
    with open(MODELS_DIR / "persona_metadata.json", encoding="utf-8") as f:
        meta = json.load(f)
    df = pd.read_csv(MODELS_DIR / "user_cluster_assignments.csv")
    assert len(df) == meta["n_users_clustered"]
    assert set(df["cluster_id"].unique()) == set(range(meta["k_selected"]))
    assert df["user_id"].is_unique
