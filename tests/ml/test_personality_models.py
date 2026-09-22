import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "personality"
sys.path.insert(0, str(REPO_ROOT / "ml"))
sys.path.insert(0, str(REPO_ROOT / "ml" / "personality"))

pytestmark = pytest.mark.skipif(
    not (MODELS_DIR / "classical_results.json").exists(),
    reason="run ml/personality/train_classical.py first",
)


def test_classical_results_have_real_metrics_not_placeholders():
    with open(MODELS_DIR / "classical_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["n_participants"] == 279
    assert data["n_features"] == 32
    for model_name, result in data["results"].items():
        avg = result["average"]
        assert isinstance(avg["mae"], float)
        assert avg["mae"] > 0  # a real regression error, never exactly 0 on this task
        for trait, metrics in result["per_trait"].items():
            assert metrics["mae"] >= 0
            assert metrics["rmse"] >= 0


def test_classical_models_load_and_predict_right_shape():
    for name in ("linear_regression", "random_forest", "xgboost"):
        model = joblib.load(MODELS_DIR / f"{name}.joblib")
        x = np.zeros((1, 32), dtype=np.float32)
        pred = model.predict(x)
        assert pred.shape == (1, 5)


@pytest.mark.skipif(not (MODELS_DIR / "nn_results.json").exists(), reason="run ml/personality/train_nn.py first")
def test_nn_results_have_real_gpu_metadata():
    with open(MODELS_DIR / "nn_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["epochs_completed"] > 0
    assert data["epochs_completed"] <= data["epochs_requested"]
    assert data["best_epoch"] > 0
    assert data["best_epoch"] <= data["epochs_completed"]
    assert data["training_duration_sec"] > 0
    assert isinstance(data["cuda_available"], bool)
    # device string must match cuda_available honestly, never claim CUDA falsely
    if data["cuda_available"]:
        assert data["device"] == "cuda"
        assert data["gpu_name"]
    else:
        assert data["device"] == "cpu"


@pytest.mark.skipif(not (MODELS_DIR / "selected_model.json").exists(), reason="run ml/personality/compare_and_select.py first")
def test_selected_model_picked_by_lowest_mae_not_assumed():
    with open(MODELS_DIR / "selected_model.json", encoding="utf-8") as f:
        info = json.load(f)
    scores = info["all_candidate_scores"]
    best_name = min(scores, key=scores.get)
    assert info["model_type"] == best_name or f"{info['model_type']}" in best_name
    assert len(info["global_feature_importance"]) == 32


@pytest.mark.skipif(not (MODELS_DIR / "pytorch_nn.pt").exists(), reason="run ml/personality/train_nn.py first")
def test_nn_checkpoint_loads_and_runs_forward_pass():
    import torch
    from nn_model import PersonalityNet

    checkpoint = torch.load(MODELS_DIR / "pytorch_nn.pt", map_location="cpu", weights_only=False)
    net = PersonalityNet(input_dim=checkpoint["input_dim"])
    net.load_state_dict(checkpoint["model_state_dict"])
    net.eval()

    x = torch.zeros((1, checkpoint["input_dim"]), dtype=torch.float32)
    with torch.no_grad():
        out = net(x)
    assert out.shape == (1, 5)
