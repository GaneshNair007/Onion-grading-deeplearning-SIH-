"""Size estimation with an explicit two-tier honesty model.

Tier 1 — **calibrated**: an ArUco-marked inspection mat is visible in the
image, so a pixel→millimetre scale is derived from a marker whose physical
size is known. Only then is `diameter_mm` reported, with
`size_method="aruco_calibrated"`.

Tier 2 — **uncalibrated**: no marker found. The function reports
`size_method="uncalibrated"` and **no millimetre value at all** — pixels are
never presented as millimetres. The grading engine escalates to manual review
when a policy requires a size measurement and calibration is missing.

Accuracy status: the geometry is tested against a *synthesised* mat with a
known scale (`tests/test_vision_pipeline.py`). Physical-print accuracy (paper
shrinkage, print DPI, camera distortion) still requires a ruler comparison on
a real print — tracked in docs/LIMITATIONS.md as pending.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import cv2
    import numpy as np
    _CV2_OK = True
except Exception:  # pragma: no cover
    _CV2_OK = False

#: Physical edge length of the printed markers (metres → mm below).
DEFAULT_MARKER_SIZE_MM = 40.0
ARUCO_DICT_NAME = "DICT_4X4_50"


@dataclass
class DetectedMarker:
    marker_id: int
    corners: List[List[float]]      # 4x [x, y]
    edge_px: float                  # mean edge length in pixels


def detect_markers(image: "np.ndarray") -> List[DetectedMarker]:
    """Detect ArUco markers (OpenCV >= 4.7 API, with legacy fallback)."""
    if not _CV2_OK:
        return []
    dictionary = cv2.aruco.getPredefinedDictionary(
        getattr(cv2.aruco, ARUCO_DICT_NAME))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners = ids = None
    try:
        detector = cv2.aruco.ArucoDetector(dictionary,
                                           cv2.aruco.DetectorParameters())
        corners, ids, _ = detector.detectMarkers(gray)
    except AttributeError:  # OpenCV < 4.7
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary)

    markers: List[DetectedMarker] = []
    if ids is None:
        return markers
    for marker_corners, marker_id in zip(corners, ids.flatten()):
        pts = marker_corners.reshape(-1, 2)
        edges = [float(np.linalg.norm(pts[i] - pts[(i + 1) % 4]))
                 for i in range(4)]
        markers.append(DetectedMarker(marker_id=int(marker_id),
                                      corners=pts.tolist(),
                                      edge_px=float(np.mean(edges))))
    return markers


def pixel_per_mm(markers: List[DetectedMarker],
                 marker_size_mm: float = DEFAULT_MARKER_SIZE_MM) -> Optional[float]:
    """Scale from the median marker edge length, or None when unusable."""
    usable = [m.edge_px for m in markers if m.edge_px > 5]
    if len(usable) < 1:
        return None
    edge = float(np.median(usable))
    if edge <= 0:
        return None
    return edge / float(marker_size_mm)


def measure_size(image_path: str, bbox_xywh: Tuple[float, float, float, float],
                 marker_size_mm: float = DEFAULT_MARKER_SIZE_MM,
                 onion_mask_area_px: Optional[float] = None) -> Dict[str, Any]:
    """Measure one onion's size, calibrated when a mat is visible."""
    if not _CV2_OK:
        return {"size_method": "unknown", "diameter_mm": None,
                "warnings": ["OpenCV unavailable: size measurement skipped"]}

    image = cv2.imread(str(image_path))
    if image is None:
        return {"size_method": "unknown", "diameter_mm": None,
                "warnings": [f"image unreadable: {image_path}"]}

    markers = detect_markers(image)
    scale = pixel_per_mm(markers, marker_size_mm)
    x, y, w, h = bbox_xywh

    if scale is None:
        return {
            "size_method": "uncalibrated",
            "diameter_mm": None,
            "markers_detected": 0,
            "approximate_size": {
                "bbox_px": [round(w, 1), round(h, 1)],
                "note": ("No calibration marker detected. This is an "
                         "approximate visual size in pixels and is NOT a "
                         "procurement-grade physical measurement."),
            },
            "warnings": ["CALIBRATION_MISSING: no ArUco marker found"],
        }

    # Equivalent circular diameter from the projected area when a mask area is
    # available; otherwise from the bounding box (documented approximation).
    if onion_mask_area_px and onion_mask_area_px > 0:
        diameter_px = 2.0 * math.sqrt(float(onion_mask_area_px) / math.pi)
        basis = "mask_area"
    else:
        diameter_px = max(w, h)
        basis = "bbox_long_side"

    diameter_mm = diameter_px / scale
    return {
        "size_method": "aruco_calibrated",
        "diameter_mm": round(diameter_mm, 1),
        "equatorial_width_mm_estimate": round(max(w, h) / scale, 1),
        "min_width_mm_estimate": round(min(w, h) / scale, 1),
        "markers_detected": len(markers),
        "pixels_per_mm": round(scale, 4),
        "marker_size_mm": marker_size_mm,
        "diameter_basis": basis,
        "confidence": 0.9 if len(markers) >= 4 else 0.75,
        "warnings": [
            "Calibrated from printed ArUco markers; accuracy still depends on "
            "flatness, print scale and lens distortion (see docs/LIMITATIONS.md).",
        ],
    }
