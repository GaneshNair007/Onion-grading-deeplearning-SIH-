"""Capture-quality gate tests (batch tray images)."""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("cv2")
import cv2

from src.vision.capture_quality import evaluate_capture, measure_blur


def _save(tmp_path, name, image):
    path = tmp_path / name
    cv2.imwrite(str(path), image)
    return str(path)


def _sharp_tray():
    """A crisp, evenly lit synthetic tray with onion-sized shapes."""
    img = np.full((800, 1200, 3), 200, dtype=np.uint8)
    for cx, cy in [(200, 200), (500, 200), (800, 200), (200, 600), (500, 600)]:
        cv2.circle(img, (cx, cy), 90, (110, 140, 70), -1)
        cv2.circle(img, (cx - 30, cy - 30), 22, (150, 175, 110), -1)
    return img


def test_clean_tray_passes(tmp_path):
    path = _save(tmp_path, "clean.png", _sharp_tray())
    instances = [{"bbox_xywh": [110, 110, 180, 180]},
                 {"bbox_xywh": [410, 110, 180, 180]}]
    quality = evaluate_capture(path, instances=instances, image_size=[1200, 800])
    assert "NO_ONION_DETECTED" not in quality.issues
    assert "MOTION_BLUR" not in quality.issues
    assert quality.status in {"ok", "warn"}


def test_blurred_image_is_rejected(tmp_path):
    blurred = cv2.GaussianBlur(_sharp_tray(), (31, 31), 0)
    path = _save(tmp_path, "blurred.png", blurred)
    quality = evaluate_capture(path, instances=[{"bbox_xywh": [110, 110, 180, 180]}],
                               image_size=[1200, 800])
    assert "MOTION_BLUR" in quality.issues
    assert quality.status == "reject"
    assert any("still" in g.lower() for g in quality.guidance)


def test_glare_is_reported(tmp_path):
    img = _sharp_tray()
    img[100:300, 300:600] = 255
    path = _save(tmp_path, "glare.png", img)
    quality = evaluate_capture(path, instances=[{"bbox_xywh": [110, 110, 180, 180]}],
                               image_size=[1200, 800])
    assert "GLARE" in quality.issues


def test_crowded_tray_is_rejected_and_asks_for_spacing(tmp_path):
    path = _save(tmp_path, "crowded.png", _sharp_tray())
    instances = [{"bbox_xywh": [0, 0, 1000, 780]}]
    quality = evaluate_capture(path, instances=instances, image_size=[1200, 800])
    assert "CROWDED_TRAY" in quality.issues
    assert quality.status == "reject"
    assert any("spread" in g.lower() for g in quality.guidance)


def test_onion_touching_the_border_is_flagged(tmp_path):
    path = _save(tmp_path, "edge.png", _sharp_tray())
    quality = evaluate_capture(path, instances=[{"bbox_xywh": [0, 300, 200, 200]}],
                               image_size=[1200, 800])
    assert "ONION_OUT_OF_FRAME" in quality.issues


def test_empty_tray_reports_no_onion(tmp_path):
    path = _save(tmp_path, "empty.png", _sharp_tray())
    quality = evaluate_capture(path, instances=[], image_size=[1200, 800])
    assert "NO_ONION_DETECTED" in quality.issues
    assert quality.status == "reject"


def test_missing_calibration_is_only_required_when_asked(tmp_path):
    path = _save(tmp_path, "tray.png", _sharp_tray())
    instances = [{"bbox_xywh": [110, 110, 180, 180]}]
    relaxed = evaluate_capture(path, instances=instances, image_size=[1200, 800],
                               require_calibration=False)
    strict = evaluate_capture(path, instances=instances, image_size=[1200, 800],
                              markers_detected=0, require_calibration=True)
    assert "CALIBRATION_MISSING" not in relaxed.issues
    assert "CALIBRATION_MISSING" in strict.issues
    assert strict.status == "reject"


def test_unreadable_image_rejected(tmp_path):
    quality = evaluate_capture(str(tmp_path / "missing.png"))
    assert quality.status == "reject"
    assert "IMAGE_UNREADABLE" in quality.issues


def test_blur_metric_is_lower_for_blurred_images(tmp_path):
    sharp = measure_blur(_sharp_tray())
    blurred = measure_blur(cv2.GaussianBlur(_sharp_tray(), (31, 31), 0))
    assert blurred < sharp
