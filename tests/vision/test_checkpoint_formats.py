"""Checkpoint-format compatibility.

A training run saves ``{"model": state_dict, "epoch": n, "history": [...]}`` so an
interrupted run can resume; older artifacts are bare state dicts. Inference must
read both.

This regressed for real: after the detector trainer gained checkpointing, the
batch-scan integration tests failed with
``Unexpected key(s) in state_dict: "model", "epoch", ...``. These tests pin the
fix at the loader level so the next format change cannot silently break
inference again.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

torch = pytest.importorskip("torch")

from src.vision.model import load_checkpoint_state  # noqa: E402
from src.vision.detector import build_detector       # noqa: E402


def test_loader_accepts_a_raw_state_dict(tmp_path):
    model = build_detector(pretrained=False)
    path = tmp_path / "raw_state.pt"
    torch.save(model.state_dict(), path)
    state = load_checkpoint_state(path)
    assert "roi_heads.box_predictor.cls_score.weight" in state
    model.load_state_dict(state)          # must not raise


def test_loader_accepts_a_training_checkpoint(tmp_path):
    model = build_detector(pretrained=False)
    path = tmp_path / "checkpoint.pt"
    torch.save({"model": model.state_dict(), "epoch": 7,
                "history": [{"epoch": 7}], "model_id": "test"}, path)
    state = load_checkpoint_state(path)
    assert "model" not in state, "the wrapper dict must not leak into the weights"
    model.load_state_dict(state)          # must not raise


def test_detector_inference_works_with_a_checkpoint_wrapped_artifact(tmp_path):
    """End-to-end: detect_onions must run against the wrapped format."""
    from PIL import Image

    from src.vision import detector as det

    path = tmp_path / "wrapped.pt"
    torch.save({"model": build_detector(pretrained=False).state_dict(),
                "epoch": 1, "history": []}, path)

    image = tmp_path / "tray.jpg"
    Image.new("RGB", (240, 180), (170, 120, 60)).save(image)

    det._cache.clear()
    result = det.detect_onions(str(image), model_path=str(path))
    # An untrained model may detect nothing, but it must not raise or crash.
    assert result["status"] == "success"
    assert isinstance(result.get("instances"), list)
