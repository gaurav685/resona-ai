"""PyTorch Big Five regression: small feed-forward net, GPU-aware training,
visible epoch progress, early stopping.

Usage:
    python ml/personality/train_nn.py
    python ml/personality/train_nn.py --epochs 100 --lr 0.001 --batch-size 16
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import FEATURE_COLUMNS, TRAIT_COLUMNS, load_personality_dataset  # noqa: E402
from nn_model import PersonalityNet  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models" / "personality"
RANDOM_SEED = 42
TEST_SIZE = 0.2
VAL_SIZE = 0.15  # of the training split


def detect_device():
    import torch

    info = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "gpu_name": None,
        "reason": None,
    }
    if torch.cuda.is_available():
        device = torch.device("cuda")
        info["gpu_name"] = torch.cuda.get_device_name(0)
    else:
        device = torch.device("cpu")
        info["reason"] = "torch.cuda.is_available() returned False on this machine"
    return device, info


def print_device_banner(device, info: dict) -> None:
    print(f"PyTorch version: {info['torch_version']}")
    print(f"CUDA available: {info['cuda_available']}")
    if info["cuda_available"]:
        print(f"Device: CUDA")
        print(f"GPU: {info['gpu_name']}")
        print(f"CUDA version: {info['cuda_version']}")
    else:
        print(f"Device: CPU")
        print(f"Reason: {info['reason']}")


def evaluate_np(y_true: np.ndarray, y_pred: np.ndarray, trait_names: list[str]) -> dict:
    per_trait = {}
    for i, trait in enumerate(trait_names):
        yt, yp = y_true[:, i], y_pred[:, i]
        mae = float(mean_absolute_error(yt, yp))
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        r2 = float(r2_score(yt, yp))
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


def permutation_importance(model, X_test, y_test, feature_columns, device, baseline_mae, n_repeats=5):
    import torch

    rng = np.random.RandomState(RANDOM_SEED)
    importances = []
    for j, feat in enumerate(feature_columns):
        maes = []
        for _ in range(n_repeats):
            X_perm = X_test.copy()
            rng.shuffle(X_perm[:, j])
            with torch.no_grad():
                pred = model(torch.from_numpy(X_perm.astype(np.float32)).to(device)).cpu().numpy()
            maes.append(mean_absolute_error(y_test, pred))
        importances.append({"feature": feat, "importance": float(np.mean(maes) - baseline_mae)})
    importances.sort(key=lambda d: d["importance"], reverse=True)
    return importances


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    import torch
    from torch import nn, optim
    from torch.utils.data import DataLoader, TensorDataset

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    device, device_info = detect_device()
    print_device_banner(device, device_info)
    print()

    X, y, _ = load_personality_dataset()
    X_np, y_np = X.to_numpy(dtype=np.float32), y.to_numpy(dtype=np.float32)

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X_np, y_np, test_size=TEST_SIZE, random_state=args.seed
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=VAL_SIZE, random_state=args.seed
    )
    print(f"Dataset: {len(X_np)} participants -> {len(X_train)} train / {len(X_val)} val / {len(X_test)} test")

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train).astype(np.float32)
    X_val_s = scaler.transform(X_val).astype(np.float32)
    X_test_s = scaler.transform(X_test).astype(np.float32)

    train_ds = TensorDataset(torch.from_numpy(X_train_s), torch.from_numpy(y_train))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, generator=torch.Generator().manual_seed(args.seed))

    model = PersonalityNet(input_dim=X_np.shape[1]).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.MSELoss()

    X_val_t = torch.from_numpy(X_val_s).to(device)
    y_val_t = torch.from_numpy(y_val).to(device)

    best_val_loss = float("inf")
    best_epoch = 0
    best_state = None
    epochs_no_improve = 0
    epochs_completed = 0

    t_start = time.time()
    for epoch in tqdm(range(1, args.epochs + 1), desc="training", unit="epoch"):
        model.train()
        train_losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())
        train_loss = float(np.mean(train_losses))

        model.eval()
        with torch.no_grad():
            val_pred = model(X_val_t)
            val_loss = float(criterion(val_pred, y_val_t).item())

        epochs_completed = epoch
        print(f"Epoch {epoch}/{args.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss - 1e-5:
            best_val_loss = val_loss
            best_epoch = epoch
            best_state = {k: v.clone().cpu() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                print(f"Early stopping at epoch {epoch}/{args.epochs}")
                print(f"Best epoch: {best_epoch}")
                break

    training_duration_sec = time.time() - t_start

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()

    X_test_t = torch.from_numpy(X_test_s).to(device)
    with torch.no_grad():
        test_pred = model(X_test_t).cpu().numpy()

    metrics = evaluate_np(y_test, test_pred, TRAIT_COLUMNS)
    baseline_mae = metrics["average"]["mae"]

    print()
    print(f"Test set evaluation (best checkpoint, epoch {best_epoch}):")
    for trait in TRAIT_COLUMNS:
        m = metrics["per_trait"][trait]
        print(f"  {trait:18s} MAE={m['mae']:.3f} RMSE={m['rmse']:.3f} R2={m['r2']:.3f} Pearson={m['pearson']}")
    print(f"  average: MAE={metrics['average']['mae']:.3f} RMSE={metrics['average']['rmse']:.3f} "
          f"R2={metrics['average']['r2']:.3f}")

    print("\nComputing permutation feature importance on test set...")
    importances = permutation_importance(model, X_test_s, y_test, list(X.columns), device, baseline_mae)
    print("Top 5 features by permutation importance (MAE increase when shuffled):")
    for imp in importances[:5]:
        print(f"  {imp['feature']:24s} +{imp['importance']:.4f} MAE")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "scaler": scaler,
            "input_dim": X_np.shape[1],
        },
        MODELS_DIR / "pytorch_nn.pt",
    )

    metadata = {
        "model_name": "pytorch_nn",
        "architecture": "Linear(32->64)-ReLU-Dropout-Linear(64->32)-ReLU-Dropout-Linear(32->5)",
        "dataset_version": "beyond_big_five (data/raw/beyond_big_five/PER_dataset.xls, 279 participants)",
        "feature_version": "ml/personality/dataset.py FEATURE_COLUMNS v1 (32 features)",
        "device": "cuda" if device_info["cuda_available"] else "cpu",
        "gpu_name": device_info["gpu_name"],
        "cuda_available": device_info["cuda_available"],
        "pytorch_version": device_info["torch_version"],
        "cuda_version": device_info["cuda_version"],
        "epochs_requested": args.epochs,
        "epochs_completed": epochs_completed,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "patience": args.patience,
        "random_seed": args.seed,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "final_metrics": metrics,
        "training_duration_sec": training_duration_sec,
        "feature_columns": list(X.columns),
        "trait_columns": TRAIT_COLUMNS,
        "permutation_feature_importance": importances,
    }
    with open(MODELS_DIR / "nn_results.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nTraining duration: {training_duration_sec:.1f}s")
    print(f"Saved model checkpoint and nn_results.json to {MODELS_DIR}")


if __name__ == "__main__":
    main()
