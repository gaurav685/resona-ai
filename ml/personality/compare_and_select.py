"""Compare classical baselines vs the PyTorch NN on actual test-set metrics
and select the final model for models/personality/selected_model.json.

Selection criterion: lowest average test-set MAE across the five Big Five
traits (same train/test split, same random seed, across all candidates —
see train_classical.py and train_nn.py). Whichever model actually wins is
used; the neural network is NOT assumed to win.

Also computes global feature importance for the selected model:
  - tree-based (random_forest / xgboost): SHAP TreeExplainer, mean |SHAP|
  - linear_regression: mean |coefficient| across the 5 trait regressors
  - pytorch_nn: permutation importance (already computed in train_nn.py)

Usage:
    python ml/personality/compare_and_select.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import load_personality_dataset  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "personality"


def shap_importance(model, X_background: np.ndarray, feature_columns: list[str]) -> list[dict]:
    import shap

    # model is a MultiOutputRegressor; explain each trait's sub-estimator
    # and average |SHAP value| across traits and samples.
    all_abs = np.zeros((X_background.shape[0], len(feature_columns)))
    for sub_estimator in model.estimators_:
        explainer = shap.TreeExplainer(sub_estimator)
        sv = explainer.shap_values(X_background)
        all_abs += np.abs(sv)
    mean_abs = (all_abs / len(model.estimators_)).mean(axis=0)
    ranked = sorted(
        [{"feature": f, "importance": float(v)} for f, v in zip(feature_columns, mean_abs)],
        key=lambda d: d["importance"],
        reverse=True,
    )
    return ranked


def linear_importance(model, feature_columns: list[str]) -> list[dict]:
    coefs = np.abs(np.array([est.coef_ for est in model.estimators_])) if hasattr(model, "estimators_") else np.abs(model.coef_)
    mean_abs = coefs.mean(axis=0)
    ranked = sorted(
        [{"feature": f, "importance": float(v)} for f, v in zip(feature_columns, mean_abs)],
        key=lambda d: d["importance"],
        reverse=True,
    )
    return ranked


def main() -> None:
    with open(MODELS_DIR / "classical_results.json", "r", encoding="utf-8") as f:
        classical = json.load(f)
    with open(MODELS_DIR / "nn_results.json", "r", encoding="utf-8") as f:
        nn = json.load(f)

    candidates = {
        "linear_regression": classical["results"]["linear_regression"]["average"]["mae"],
        "random_forest": classical["results"]["random_forest"]["average"]["mae"],
        "xgboost": classical["results"]["xgboost"]["average"]["mae"],
        "pytorch_nn": nn["final_metrics"]["average"]["mae"],
    }

    print("Model comparison (average test-set MAE across 5 traits, lower is better):")
    for name, mae in sorted(candidates.items(), key=lambda kv: kv[1]):
        print(f"  {name:20s} MAE={mae:.4f}")

    selected_name = min(candidates, key=candidates.get)
    print(f"\nSelected: {selected_name} (lowest average MAE = {candidates[selected_name]:.4f})")

    feature_columns = classical["feature_columns"]
    trait_columns = classical["trait_columns"]

    if selected_name == "pytorch_nn":
        info = {
            "model_type": "pytorch",
            "model_version": "pytorch_nn-v1",
            "artifact_file": "pytorch_nn.pt",
            "feature_columns": feature_columns,
            "trait_columns": trait_columns,
            "global_feature_importance": nn["permutation_feature_importance"],
            "selection_metric": "test_avg_mae",
            "selection_value": candidates[selected_name],
            "all_candidate_scores": candidates,
        }
    else:
        model = joblib.load(MODELS_DIR / f"{selected_name}.joblib")
        X, y, _ = load_personality_dataset()
        X_np = X.to_numpy()

        if selected_name == "linear_regression":
            importance = linear_importance(model, feature_columns)
            method = "abs_coefficient"
        else:
            # SHAP on a manageable background sample for speed.
            bg = X_np[:100] if len(X_np) > 100 else X_np
            importance = shap_importance(model, bg, feature_columns)
            method = "shap_tree_explainer_mean_abs"

        info = {
            "model_type": selected_name,
            "model_version": f"{selected_name}-v1",
            "artifact_file": f"{selected_name}.joblib",
            "feature_columns": feature_columns,
            "trait_columns": trait_columns,
            "global_feature_importance": importance,
            "global_feature_importance_method": method,
            "selection_metric": "test_avg_mae",
            "selection_value": candidates[selected_name],
            "all_candidate_scores": candidates,
        }

    with open(MODELS_DIR / "selected_model.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    print(f"\nWrote {MODELS_DIR / 'selected_model.json'}")
    print("Top 5 global feature importances:")
    for item in info["global_feature_importance"][:5]:
        print(f"  {item['feature']:24s} {item['importance']:.4f}")


if __name__ == "__main__":
    main()
