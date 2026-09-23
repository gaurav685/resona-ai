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


def test_detect_device_cpu_fallback_path(monkeypatch):
    """This development machine has a CUDA GPU, so the CPU-fallback branch
    never runs in the test above. Force torch.cuda.is_available() to False
    at the boundary to verify that branch actually falls back correctly
    (device='cpu', no fabricated GPU name, a real stated reason) rather
    than trusting it by inspection alone."""
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    device, info = detect_device()
    assert str(device) == "cpu"
    assert info["cuda_available"] is False
    assert info["gpu_name"] is None
    assert info["reason"] == "torch.cuda.is_available() returned False on this machine"


def test_detect_device_cuda_path_moves_to_real_device(monkeypatch):
    """When CUDA is reported available, detect_device must return a CUDA
    device object backed by the actual detected GPU name, not a hardcoded
    string."""
    if not torch.cuda.is_available():
        pytest.skip("no CUDA device on this machine to verify the positive path against")
    device, info = detect_device()
    assert device.type == "cuda"
    x = torch.zeros(2, 2).to(device)
    assert x.is_cuda
