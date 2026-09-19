"""Vision tests: honest size calibration and conservative multi-view fusion."""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("cv2")

from src.vision.multi_view import (DEFECT_THRESHOLD, ViewResult, fuse_views,
                                  to_measurements, view_instructions)
from src.vision.size import (DEFAULT_MARKER_SIZE_MM, detect_markers,
                             measure_size, pixel_per_mm)


# ------------------------------------------------------------------- size
@pytest.fixture(scope="module")
def calibration_mat(tmp_path_factory):
    """Render the real calibration mat and save it as a PNG."""
    from scripts.make_calibration_mat import build_mat
    import cv2
    mat = build_mat()
    path = tmp_path_factory.mktemp("mat") / "mat.png"
    cv2.imwrite(str(path), mat)
    return path


@pytest.fixture(scope="module")
def uncalibrated_image(tmp_path_factory):
    """A plain image with no marker: nothing may be reported in millimetres."""
    import cv2
    img = np.full((600, 600, 3), 180, dtype=np.uint8)
    img[200:400, 200:400] = (90, 120, 60)
    path = tmp_path_factory.mktemp("plain") / "plain.png"
    cv2.imwrite(str(path), img)
    return path


def test_markers_are_detected_in_the_generated_mat(calibration_mat):
    import cv2
    markers = detect_markers(cv2.imread(str(calibration_mat)))
    assert len(markers) >= 3, "the mat must be detectable by the same code the field uses"


def test_measured_scale_matches_the_declared_marker_size(calibration_mat):
    import cv2
    from scripts.make_calibration_mat import DPI, MM_PER_INCH
    markers = detect_markers(cv2.imread(str(calibration_mat)))
    scale = pixel_per_mm(markers, DEFAULT_MARKER_SIZE_MM)
    expected = (DEFAULT_MARKER_SIZE_MM / MM_PER_INCH * DPI) / DEFAULT_MARKER_SIZE_MM
    assert scale == pytest.approx(expected, rel=0.05)


def test_calibrated_measurement_reports_millimetres(calibration_mat):
    result = measure_size(str(calibration_mat), (100, 100, 400, 400),
                          marker_size_mm=DEFAULT_MARKER_SIZE_MM)
    assert result["size_method"] == "aruco_calibrated"
    assert result["diameter_mm"] is not None
    assert result["diameter_mm"] > 0
    assert result["pixels_per_mm"]


def test_uncalibrated_image_reports_no_millimetres(uncalibrated_image):
    result = measure_size(str(uncalibrated_image), (100, 100, 200, 200))
    assert result["size_method"] == "uncalibrated"
    assert result["diameter_mm"] is None            # the critical guarantee
    assert "approximate_size" in result
    assert any("CALIBRATION_MISSING" in w for w in result["warnings"])


# -------------------------------------------------------------- multi-view
def _view(name: str, label: str, conf: float, rot: float = 0.0,
          sprout: float = 0.0) -> ViewResult:
    return ViewResult(view=name, label=label, confidence=conf,
                      defects={
                          "rotten": {"detected": rot >= DEFECT_THRESHOLD,
                                     "confidence": rot},
                          "sprout": {"detected": sprout >= DEFECT_THRESHOLD,
                                     "confidence": sprout},
                      }, is_onion=True)


def test_guided_views_are_documented():
    assert {v["view"] for v in view_instructions()} == \
        {"neck", "base", "side_a", "side_b"}


def test_one_bad_view_is_enough_to_flag_a_defect():
    views = [_view("neck", "sound", 0.9),
             _view("base", "sound", 0.9),
             _view("side_a", "visibly_rotten", 0.62, rot=0.88),
             _view("side_b", "sound", 0.9)]
    fused = fuse_views(views)
    assert fused["visible_defects"]["rotten"]["detected"] is True
    assert fused["visible_defects"]["rotten"]["views_positive"] == 1
    assert fused["label"] == "visibly_rotten"


def test_severity_uses_max_not_mean():
    views = [_view("neck", "sound", 0.9, rot=0.51),
             _view("base", "sound", 0.9, rot=0.52),
             _view("side_a", "sound", 0.9, rot=0.55),
             _view("side_b", "sound", 0.9, rot=0.99)]
    fused = fuse_views(views)
    assert fused["visible_defects"]["rotten"]["max_confidence"] == 0.99


def test_no_false_defect_when_all_views_are_clean():
    views = [_view(v, "sound", 0.9) for v in ("neck", "base", "side_a", "side_b")]
    fused = fuse_views(views)
    assert fused["visible_defects"]["rotten"]["detected"] is False
    assert fused["label"] == "sound"


def test_incomplete_capture_is_not_reported_as_complete():
    fused = fuse_views([_view("neck", "sound", 0.9)])
    assert fused["coverage_status"] == "incomplete"
    assert fused["views_missing"]
    assert any("incomplete" in w.lower() for w in fused["warnings"])


def test_defect_area_is_never_aggregated_across_views():
    fused = fuse_views([_view(v, "sound", 0.9) for v in ("neck", "side_a")])
    assert any("not aggregated" in w for w in fused["warnings"])
    assert to_measurements(fused)["damage_surface_pct"] is None


def test_not_onion_when_no_view_contains_an_onion():
    views = [ViewResult(view="side_a", label="unavailable", confidence=0.0,
                        is_onion=False)]
    fused = fuse_views(views)
    assert fused["is_onion"] is False
    assert fused["status"] == "not_onion"


def test_view_disagreement_is_surfaced():
    views = [_view("neck", "sound", 0.9), _view("base", "sprouted", 0.7, sprout=0.8)]
    fused = fuse_views(views)
    assert fused["view_disagreement"] is True
