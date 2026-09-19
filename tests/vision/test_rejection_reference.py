"""The embedding OOD reference is fitted from real bulbs and actually used.

``rejection_reference.npz`` is a machine-local artifact (gitignored because
its source images carry an unresolved license). These tests activate only
when the artifact exists on this machine; CI skips them, and
``scripts/build_rejection_reference.py`` rebuilds the artifact in ~1 min.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.rejection import load_reference  # noqa: E402

REFERENCE = PROJECT_ROOT / "models" / "vision" / "rejection_reference.npz"

pytestmark = pytest.mark.skipif(
    not REFERENCE.exists(),
    reason="machine-local rejection reference not built; run "
           "scripts/build_rejection_reference.py")


def test_reference_is_fitted_from_enough_bulbs():
    stats = load_reference(REFERENCE)
    assert stats is not None
    assert stats.n_samples >= 500, "reference must be fitted from real bulbs"


def test_embedding_gate_runs_and_reports_scores():
    from PIL import Image
    from inference.vision_inference import classify_pil_image

    img_path = PROJECT_ROOT / "demo" / "calibration_mat_A4_300dpi.png"
    if not img_path.exists():
        pytest.skip("demo fixture missing")
    r = classify_pil_image(Image.open(img_path).convert("RGB"))
    rej = r.get("rejection") or {}
    if rej.get("gate") != "embedding_ood":
        pytest.skip("detector gate took precedence on this machine")
    # The gate must actually measure against the fitted reference.
    assert rej.get("threshold") == pytest.approx(
        load_reference(REFERENCE).threshold, rel=1e-4)
    assert "ood_score" in rej


def test_report_records_license_caveat():
    import json
    report = PROJECT_ROOT / "evaluation" / "rejection_reference_report.json"
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert "unresolved" in data.get("license_note", "")
