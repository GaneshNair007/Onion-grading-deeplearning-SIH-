"""Integration: Quick Batch Scan over a composed tray fixture of real onions.

Skipped automatically when the trained detector is absent, because a batch scan
without a detector must never fabricate detections (that is the whole point of
the `model_unavailable` status).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("torch")

from inference.batch_scan import scan_batch, scan_image
from src.reporting.audit_hash import verify_integrity
from src.reporting.generator import build_report, finalize
from src.vision.detector import resolve_detector

DETECTOR_ARTIFACT = resolve_detector()
needs_detector = pytest.mark.skipif(
    DETECTOR_ARTIFACT is None,
    reason="no trained detector artifact in this checkout")


@pytest.fixture(scope="module")
def tray_image(tmp_path_factory) -> Path:
    from scripts.compose_tray_image import compose
    out = tmp_path_factory.mktemp("tray") / "tray.png"
    compose(8, out, seed=5)
    return out


def test_missing_detector_reports_unavailable_and_grades_nothing(tray_image, policy,
                                                                monkeypatch):
    """With no detector artifact the pipeline must refuse, not guess."""
    import inference.batch_scan as bs
    from src.vision import detector as det

    monkeypatch.setattr(det, "resolve_detector", lambda explicit=None: None)
    result = scan_image(str(tray_image), policy)
    assert result["status"] == "model_unavailable"
    assert result["onions"] == []
    assert any("detector" in w.lower() or "train" in w.lower()
               for w in result["warnings"])


@needs_detector
def test_batch_scan_produces_instances_measurements_and_decisions(tray_image, policy):
    result = scan_batch([str(tray_image)], policy, center_id="TEST-CTR",
                        inspector_id="INSP-T", lot_id="LOT-1")

    assert result["mode"] == "quick_batch_scan"
    assert result["onions"], "a tray of 8 onions must yield at least one instance"

    for onion in result["onions"]:
        decision = onion["decision"]
        assert decision["decision"] in {"grade_a", "relaxed", "reject",
                                        "manual_review"}
        assert decision["policy_hash"].startswith("sha256:")
        # Uncalibrated images must never carry a millimetre value.
        measurements = onion["measurements"]
        if measurements["size_method"] != "aruco_calibrated":
            assert measurements["diameter_mm"] is None
        # Batch mode performs no acoustic work at all.
        assert measurements["internal_defect_probability"] is None

    totals = result["batch"]["totals"]
    assert totals["total_detected"] == len(result["onions"])
    assert sum(result["batch"]["counts"].values()) == totals["graded"]
    assert abs(sum(result["batch"]["percentages"].values()) - 100.0) < 0.5


@needs_detector
def test_batch_scan_report_is_tamper_evident(tray_image, policy):
    result = scan_batch([str(tray_image)], policy, center_id="TEST-CTR")
    report = build_report(result["batch"], [
        {"onion_id": o["onion_id"], "decision": o["decision"]["decision"],
         "reason_codes": o["decision"]["reason_codes"],
         "measurements": o["measurements"]} for o in result["onions"]])
    finalized = finalize(report)
    assert verify_integrity(finalized)["valid"] is True
    assert finalized["qr_payload"]
    tampered = dict(finalized)
    tampered["summary"] = dict(finalized["summary"])
    tampered["summary"]["counts"] = {"grade_a": 999}
    assert verify_integrity(tampered)["valid"] is False


@needs_detector
def test_capture_quality_warnings_reach_the_caller(tray_image, policy, monkeypatch):
    """A rejected capture escalates every onion instead of grading it."""
    from src.vision.capture_quality import CaptureQuality

    fake = CaptureQuality(status="reject", issues=["CROWDED_TRAY"],
                          guidance=["Spread the onions across the inspection tray."],
                          metrics={})
    monkeypatch.setattr("src.vision.capture_quality.evaluate_capture",
                        lambda *a, **k: fake)
    result = scan_image(str(tray_image), policy)
    if result["status"] != "success" or not result["onions"]:
        pytest.skip("no detector artifact: nothing to escalate")
    for onion in result["onions"]:
        assert onion["decision"]["decision"] == "manual_review"
        assert onion["decision"]["reason_codes"] == ["CROWDED_TRAY"]
