import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml" / "personality"))
from train_nn import detect_device  # noqa: E402


def test_detect_device_matches_actual_torch_state():
    device, info = detect_device()
    actual_cuda = torch.cuda.is_available()
    assert info["cuda_available"] == actual_cuda
    if actual_cuda:
        assert str(device) == "cuda"
        assert info["gpu_name"] == torch.cuda.get_device_name(0)
        assert info["reason"] is None
    else:
        assert str(device) == "cpu"
        assert info["gpu_name"] is None
        assert info["reason"]
    assert info["torch_version"] == torch.__version__
