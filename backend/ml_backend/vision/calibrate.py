"""
Pixel-to-mm Metrology & Optical Calibration Engine
Supports ArUco reference markers (DICT_4X4_50) with sub-pixel corner refinement,
perspective tilt & skew quantification, multi-scale template matching fallback,
and multi-axis caliper physical diameter estimation.
"""
from __future__ import annotations
from typing import Optional, Tuple, Dict, Any
import cv2
import numpy as np

# Standard procurement setup: 25.0 mm ArUco marker (DICT_4X4_50)
ARUCO_DICT = cv2.aruco.DICT_4X4_50
DEFAULT_MARKER_SIZE_MM = 25.0


def detect_aruco_calibration(image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[int]]:
    """
    Detect ArUco marker in image with sub-pixel corner refinement.
    Returns (corners_4x2, marker_id) or (None, None).
    """
    if image is None or image.size == 0:
        return None, None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, params)
    corners_list, ids, _ = detector.detectMarkers(gray)

    if corners_list is not None and len(corners_list) > 0 and ids is not None and len(ids) > 0:
        # First detected marker corners reshaped to (4, 2)
        raw_corners = np.array(corners_list[0], dtype=np.float32).reshape(-1, 2)
        marker_id = int(ids[0][0]) if hasattr(ids[0], "__len__") else int(ids[0])

        # Sub-pixel corner refinement for sub-millimeter precision
        try:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
            refined = cv2.cornerSubPix(
                gray,
                raw_corners.reshape(-1, 1, 2),
                winSize=(5, 5),
                zeroZone=(-1, -1),
                criteria=criteria,
            )
            corners = refined.reshape(-1, 2)
        except Exception:
            corners = raw_corners

        return corners, marker_id

    return None, None


def compute_calibration_details(
    image: np.ndarray,
    reference_mm: float = DEFAULT_MARKER_SIZE_MM,
) -> Dict[str, Any]:
    """
    Comprehensive calibration analysis with perspective skew quantification.
    Returns dictionary with calibration status, scale (px/mm), corners, and method.
    """
    if image is None or image.size == 0 or reference_mm <= 0:
        return {
            "calibrated": False,
            "pixels_per_mm": None,
            "marker_id": None,
            "corners": None,
            "method": "none",
            "reference_mm": reference_mm,
            "marker_pixel_size": None,
            "skew_pct": 0.0,
            "perspective_warning": None,
        }

    corners, marker_id = detect_aruco_calibration(image)
    if corners is not None and len(corners) == 4:
        # Calculate lengths of all 4 edges
        d_top = np.linalg.norm(corners[0] - corners[1])
        d_right = np.linalg.norm(corners[1] - corners[2])
        d_bottom = np.linalg.norm(corners[2] - corners[3])
        d_left = np.linalg.norm(corners[3] - corners[0])
        edge_lengths = [d_top, d_right, d_bottom, d_left]

        avg_pixel_side = float(np.mean(edge_lengths))
        if avg_pixel_side > 5.0:
            ppm = avg_pixel_side / reference_mm

            # Quantify perspective distortion (skew between opposite sides)
            h_ratio = abs(d_top - d_bottom) / max(1.0, (d_top + d_bottom) / 2.0)
            v_ratio = abs(d_left - d_right) / max(1.0, (d_left + d_right) / 2.0)
            skew_pct = round(float(max(h_ratio, v_ratio) * 100), 2)
            warning = "high_perspective_tilt" if skew_pct > 18.0 else None

            return {
                "calibrated": True,
                "pixels_per_mm": round(float(ppm), 4),
                "marker_id": marker_id,
                "corners": corners.tolist(),
                "method": "aruco_4x4_50",
                "reference_mm": reference_mm,
                "marker_pixel_size": round(avg_pixel_side, 2),
                "skew_pct": skew_pct,
                "perspective_warning": warning,
            }

    # Fallback template detection with dimension guard
    ppm_fallback = _detect_calibration_card(image, reference_mm)
    if ppm_fallback is not None and ppm_fallback > 0:
        return {
            "calibrated": True,
            "pixels_per_mm": round(float(ppm_fallback), 4),
            "marker_id": None,
            "corners": None,
            "method": "template_contrast_card",
            "reference_mm": reference_mm,
            "marker_pixel_size": round(float(ppm_fallback * reference_mm), 2),
            "skew_pct": 0.0,
            "perspective_warning": None,
        }

    return {
        "calibrated": False,
        "pixels_per_mm": None,
        "marker_id": None,
        "corners": None,
        "method": "none",
        "reference_mm": reference_mm,
        "marker_pixel_size": None,
        "skew_pct": 0.0,
        "perspective_warning": None,
    }


def compute_pixels_per_mm(
    image: np.ndarray,
    reference_mm: float = DEFAULT_MARKER_SIZE_MM,
) -> Optional[float]:
    """
    Convenience wrapper returning pixels_per_mm or None if uncalibrated.
    """
    details = compute_calibration_details(image, reference_mm)
    return details["pixels_per_mm"] if details["calibrated"] else None


def _generate_template_marker(size: int = 44) -> np.ndarray:
    """Generate a template for the outer black border of a calibration marker."""
    img = np.ones((size, size), dtype=np.uint8) * 255
    border = max(2, size // 10)
    cv2.rectangle(img, (0, 0), (size, size), 0, border)
    cv2.rectangle(img, (2 * border, 2 * border), (size - 2 * border, size - 2 * border), 255, -1)
    return img


def _detect_calibration_card(
    image: np.ndarray,
    reference_mm: float = DEFAULT_MARKER_SIZE_MM,
) -> Optional[float]:
    """
    Detect high-contrast square calibration reference via multiscale template matching.
    Includes bounds checking to prevent assertion failure on small inputs.
    """
    if image is None or image.size == 0:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    h, w = gray.shape[:2]
    min_dim = min(h, w)

    # Filter candidate sizes so template is always smaller than the input image
    candidate_sizes = [s for s in [200, 160, 144, 120, 100, 80, 48] if s <= min_dim - 8]

    for template_size in candidate_sizes:
        try:
            template = _generate_template_marker(template_size)
            res = cv2.matchTemplate(gray, template, cv2.TM_CCORR_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val > 0.94:
                x, y = max_loc
                border = template_size // 10
                interior = gray[y + 2 * border : y + template_size - 2 * border,
                                x + 2 * border : x + template_size - 2 * border]
                if interior.size > 0 and float(np.mean(interior)) > 190:
                    return float(template_size / reference_mm)
        except Exception:
            continue

    return None


def estimate_diameter(onion_mask: np.ndarray, pixels_per_mm: float) -> float:
    """
    Estimate onion physical diameter in mm from its 2D binary segmentation mask.
    Uses equivalent circular diameter: D = 2 * sqrt(Area / pi) / pixels_per_mm.
    """
    if onion_mask is None or onion_mask.size == 0 or pixels_per_mm <= 0:
        return 0.0
    area_pixels = np.sum(onion_mask > 0)
    if area_pixels == 0:
        return 0.0
    diameter_pixels = 2.0 * np.sqrt(area_pixels / np.pi)
    return float(diameter_pixels / pixels_per_mm)


def estimate_caliper_dimensions(
    onion_mask: np.ndarray,
    pixels_per_mm: float,
) -> Tuple[float, float, float]:
    """
    Computes procurement caliper dimensions:
    Returns (equivalent_diameter_mm, major_caliper_mm, minor_caliper_mm).
    Uses minimum area bounding rectangle on the segmentation contour.
    """
    if onion_mask is None or onion_mask.size == 0 or pixels_per_mm <= 0:
        return 0.0, 0.0, 0.0

    eq_diam = estimate_diameter(onion_mask, pixels_per_mm)

    mask_u8 = (onion_mask > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return eq_diam, eq_diam, eq_diam

    largest_cnt = max(contours, key=cv2.contourArea)
    if len(largest_cnt) < 5:
        x, y, w, h = cv2.boundingRect(largest_cnt)
        major = max(w, h) / pixels_per_mm
        minor = min(w, h) / pixels_per_mm
        return eq_diam, major, minor

    rect = cv2.minAreaRect(largest_cnt)
    w_px, h_px = rect[1]
    major_px = max(w_px, h_px)
    minor_px = min(w_px, h_px)

    return (
        round(eq_diam, 1),
        round(float(major_px / pixels_per_mm), 1),
        round(float(minor_px / pixels_per_mm), 1),
    )
