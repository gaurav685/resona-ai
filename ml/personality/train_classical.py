"""Train classical baselines (Linear Regression, Random Forest, XGBoost) for
Big Five trait regression on the beyond_big_five dataset.

Multi-output regression: one model instance per algorithm, wrapped with
MultiOutputRegressor where the underlying estimator doesn't natively
support multiple targets. A single train/test split is used (279
participants total — too small for a held-out test set AND cross-
validation to both be meaningful within MVP scope); 5-fold CV on the
training split is additionally reported to sanity-check the single-split
numbers aren't a fluke of the split. All numbers below are real — this
script does not invent metrics.

Usage:
    python ml/personality/train_classical.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import TRAIT_COLUMNS, load_personality_dataset  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "personality"
RANDOM_SEED = 42
TEST_SIZE = 0.2


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, trait_names: list[str]) -> dict:
    per_trait = {}
    for i, trait in enumerate(trait_names):
        yt, yp = y_true[:, i], y_pred[:, i]
        mae = float(mean_absolute_error(yt, yp))
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        r2 = float(r2_score(yt, yp))
        # Pearson/Spearman are undefined (NaN) if a vector is constant; guard.
        if np.std(yt) > 0 and np.std(yp) > 0:
            pearson = float(pearsonr(yt, yp)[0])
            spearman = float(spearmanr(yt, yp)[0])
        else:
            pearson = None
            spearman = None
        per_trait[trait] = {"mae": mae, "rmse": rmse, "r2": r2, "pearson": pearson, "spearman": spearman}

    avg = {
        metric: float(np.mean([per_trait[t][metric] for t in trait_names if per_trait[t][metric] is not None]))
        for metric in ("mae", "rmse", "r2")
    }
    return {"per_trait": per_trait, "average": avg}


def cross_validate(model_factory, X_train: np.ndarray, y_train: np.ndarray) -> dict:
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    fold_maes = []
    for train_idx, val_idx in kf.split(X_train):
        model = model_factory()
        model.fit(X_train[train_idx], y_train[train_idx])
        pred = model.predict(X_train[val_idx])
        fold_maes.append(float(mean_absolute_error(y_train[val_idx], pred)))
    return {"cv_5fold_mae_mean": float(np.mean(fold_maes)), "cv_5fold_mae_std": float(np.std(fold_maes))}


def main() -> None:
    X, y, participant_ids = load_personality_dataset()
    X_np, y_np = X.to_numpy(), y.to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X_np, y_np, test_size=TEST_SIZE, random_state=RANDOM_SEED
    )
    print(f"Dataset: {len(X_np)} participants, {X_np.shape[1]} features, {y_np.shape[1]} traits")
    print(f"Split: {len(X_train)} train / {len(X_test)} test (test_size={TEST_SIZE}, seed={RANDOM_SEED})")
    print()

    model_factories = {
        "linear_regression": lambda: LinearRegression(),
        "random_forest": lambda: MultiOutputRegressor(
            RandomForestRegressor(n_estimators=200, max_depth=6, random_state=RANDOM_SEED)
        ),
        "xgboost": lambda: MultiOutputRegressor(
            XGBRegressor(
                n_estimators=200, max_depth=3, learning_rate=0.05,
                random_state=RANDOM_SEED, verbosity=0,
            )
        ),
    }

    results = {}
    trained_models = {}
    for name, factory in model_factories.items():
        print(f"--- {name} ---")
        t0 = time.time()
        model = factory()
        model.fit(X_train, y_train)
        train_time = time.time() - t0
        pred = model.predict(X_test)

        metrics = evaluate(y_test, pred, TRAIT_COLUMNS)
        cv = cross_validate(factory, X_train, y_train)
        results[name] = {**metrics, **cv, "train_time_sec": train_time}
        trained_models[name] = model

        print(f"  train time: {train_time:.3f}s")
        for trait in TRAIT_COLUMNS:
            m = metrics["per_trait"][trait]
            print(f"  {trait:18s} MAE={m['mae']:.3f} RMSE={m['rmse']:.3f} R2={m['r2']:.3f} "
                  f"Pearson={m['pearson']}")
        print(f"  average: MAE={metrics['average']['mae']:.3f} RMSE={metrics['average']['rmse']:.3f} "
              f"R2={metrics['average']['r2']:.3f}")
        print(f"  5-fold CV MAE on train split: {cv['cv_5fold_mae_mean']:.3f} +/- {cv['cv_5fold_mae_std']:.3f}")
        print()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, model in trained_models.items():
        joblib.dump(model, MODELS_DIR / f"{name}.joblib")

    with open(MODELS_DIR / "classical_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "dataset": "beyond_big_five",
                "n_participants": len(X_np),
                "n_features": X_np.shape[1],
                "feature_columns": list(X.columns),
                "trait_columns": TRAIT_COLUMNS,
                "test_size": TEST_SIZE,
                "random_seed": RANDOM_SEED,
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"Saved models and classical_results.json to {MODELS_DIR}")


if __name__ == "__main__":
    main()
