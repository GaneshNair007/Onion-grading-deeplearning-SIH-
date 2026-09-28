"""No detections must stay inconclusive and must not create grade reports."""
from __future__ import annotations

import importlib
from unittest.mock import Mock

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from inference.batch_scan import scan_batch, scan_image
from inference.combined_scan import scan_onion_image
from src.vision.capture_quality import CaptureQuality


@pytest.fixture
def uploaded_image(tmp_path):
    image = tmp_path / "upload.png"
    Image.new("RGB", (64, 64), (140, 85, 100)).save(image)
    return image


@pytest.fixture
def empty_detection(monkeypatch):
    result = {
        "status": "success",
        "instances": [],
        "onion_count": 0,
        "image_size": [64, 64],
        "score_threshold": 0.5,
        "model_version": "test-detector",
        "warnings": [],
    }
    monkeypatch.setattr("src.vision.detector.detect_onions", Mock(return_value=result))
    monkeypatch.setattr("src.vision.size.detect_markers", Mock(return_value=[]))
    monkeypatch.setattr(
        "src.vision.capture_quality.evaluate_capture",
        Mock(return_value=CaptureQuality(
            status="warn", issues=["CALIBRATION_MISSING"],
            guidance=["Include a calibration marker."], metrics={})),
    )
    return result


def test_empty_detection_never_classifies_or_grades(
        uploaded_image, policy, empty_detection, monkeypatch):
    classify = Mock(side_effect=AssertionError("no onion exists to classify"))
    decide = Mock(side_effect=AssertionError("no onion exists to grade"))
    monkeypatch.setattr("inference.vision_inference.classify_pil_image", classify)
    monkeypatch.setattr("inference.batch_scan.decide", decide)

    result = scan_image(str(uploaded_image), policy)

    assert result["status"] == "no_onion_detected"
    assert result["onions"] == []
    assert "inconclusive" in result["message"].lower()
    assert result["detector"] == empty_detection
    assert result["capture_quality"]["guidance"]
    classify.assert_not_called()
    decide.assert_not_called()


def test_single_scan_keeps_inconclusive_explanation_and_detector_evidence(
        uploaded_image, policy, empty_detection):
    result = scan_onion_image(str(uploaded_image), policy)

    assert result["status"] == "no_onion_detected"
    assert result["is_onion"] is None
    assert result["decision"] is None
    assert result["onion"] is None
    assert "inconclusive" in result["message"].lower()
    assert result["detector"] == empty_detection
    assert result["capture_quality"]["guidance"]


@pytest.mark.parametrize("detector_status,expected_status", [
    ("success", "no_onion_detected"),
    ("model_unavailable", "model_unavailable"),
])
def test_empty_batch_distinguishes_missing_model_from_missing_detections(
        uploaded_image, policy, empty_detection, detector_status, expected_status):
    empty_detection["status"] = detector_status

    result = scan_batch([str(uploaded_image)], policy)

    assert result["status"] == expected_status
    assert result["images"][0]["status"] == expected_status
    assert result["onions"] == []
    assert result["batch"]["totals"]["total_detected"] == 0
    assert result["batch"]["totals"]["graded"] == 0
    assert result["message"]


@pytest.mark.parametrize("detector_status,expected_status", [
    ("success", "no_onion_detected"),
    ("model_unavailable", "model_unavailable"),
])
def test_empty_batch_upload_creates_no_report_or_persisted_annotation(
        uploaded_image, empty_detection, monkeypatch,
        detector_status, expected_status):
    api = importlib.import_module("server.app")
    empty_detection["status"] = detector_status
    prohibited = {}
    for name in ("persist_annotated_evidence", "build_report", "finalize",
                 "write_report", "_store_report"):
        prohibited[name] = Mock(side_effect=AssertionError(
            f"empty detections must not call {name}"))
        monkeypatch.setattr(api, name, prohibited[name])

    with TestClient(api.app) as client:
        response = client.post(
            "/scan/batch",
            files=[("images", ("upload.png", uploaded_image.read_bytes(), "image/png"))],
            data={"policy": "demo_policy", "batch_id": "EMPTY-REGRESSION"},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == expected_status
    assert result["report"] is None
    assert result["annotated_images"] == []
    assert result["onions"] == []
    assert result["batch"]["totals"]["graded"] == 0
    for operation in prohibited.values():
        operation.assert_not_called()


@pytest.mark.parametrize("missing_status", ["no_onion_detected", "model_unavailable"])
def test_mixed_batch_reports_partial_success_without_counting_missing_images(
        uploaded_image, policy, monkeypatch, missing_status):
    decision = {
        "decision": "manual_review", "reason_codes": ["CALIBRATION_MISSING"],
        "policy_id": policy.policy_id, "policy_version": policy.version,
        "policy_hash": policy.policy_hash, "policy_verified": policy.source_verified,
        "measurements": {"model_confidence": 0.9, "diameter_mm": None},
    }
    found = {
        "image": str(uploaded_image), "status": "success", "warnings": [],
        "onions": [{"onion_id": "ONION_SCAN_0001", "decision": decision,
                    "measurements": decision["measurements"]}],
    }
    missing = {
        "image": "second.png", "status": missing_status,
        "onions": [], "warnings": ["Second image requires another attempt."],
    }
    monkeypatch.setattr("inference.batch_scan.scan_image", Mock(side_effect=[found, missing]))

    result = scan_batch([str(uploaded_image), "second.png"], policy)

    assert result["status"] == "partial_success"
    assert len(result["images"]) == 2
    assert result["images"][1]["status"] == missing_status
    assert len(result["onions"]) == 1
    assert result["batch"]["totals"]["total_detected"] == 1
    assert result["batch"]["counts"]["manual_review"] == 1
    assert result["batch"]["percentages"]["manual_review"] == 100.0
    assert "only detected onions" in result["message"]
    assert "Second image requires another attempt." in result["warnings"]
