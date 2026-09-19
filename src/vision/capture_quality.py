"""Capture-quality gates for batch tray images.

A batch image that is blurred, glaring, crowded or missing its calibration
marker must NOT be graded confidently. Each gate returns a machine-readable
issue plus *actionable* guidance, and `evaluate_capture` decides whether the
image is usable at all.

Thresholds are engineering defaults, not standards-derived values, and are
documented as such in docs/LIMITATIONS.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import cv2
    import numpy as np
    _CV2_OK = True
except Exception:  # pragma: no cover
    _CV2_OK = False

#: Laplacian variance below this is treated as motion blur (empirical).
BLUR_THRESHOLD = 60.0
#: Fraction of pixels above 250 in any channel, above which glare is reported.
GLARE_FRACTION_THRESHOLD = 0.06
#: Mean onion-box coverage above which onions are judged too crowded.
CROWDING_THRESHOLD = 0.60
#: Minimum accepted onion box area, as a fraction of the image.
MIN_ONION_AREA_FRACTION = 0.004


@dataclass
class CaptureQuality:
    status: str                                  # ok | warn | reject
    issues: List[str] = field(default_factory=list)
    guidance: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "issues": self.issues,
                "guidance": self.guidance, "metrics": self.metrics}


def measure_blur(image: "np.ndarray") -> Optional[float]:
    if not _CV2_OK:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def measure_glare(image: "np.ndarray") -> Optional[float]:
    if not _CV2_OK:
        return None
    saturated = (image >= 250).all(axis=2)
    return float(saturated.mean())


def measure_illumination_spread(image: "np.ndarray") -> Optional[float]:
    """Std-dev of block mean luminance; high values signal uneven lighting."""
    if not _CV2_OK:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    h, w = gray.shape
    bh, bw = max(1, h // 8), max(1, w // 8)
    blocks = [gray[y:y + bh, x:x + bw].mean()
              for y in range(0, h - bh + 1, bh) for x in range(0, w - bw + 1, bw)]
    return float(np.std(blocks)) if blocks else None


def evaluate_capture(image_path: str,
                     instances: Optional[List[Dict[str, Any]]] = None,
                     image_size: Optional[List[int]] = None,
                     markers_detected: Optional[int] = None,
                     require_calibration: bool = False) -> CaptureQuality:
    """Evaluate one batch image against all capture gates."""
    if not _CV2_OK:
        return CaptureQuality(status="warn",
                              issues=["openCV_UNAVAILABLE"],
                              guidance=["install opencv-python for capture QC"],
                              metrics={})

    image = cv2.imread(str(image_path))
    if image is None:
        return CaptureQuality(status="reject", issues=["IMAGE_UNREADABLE"],
                              guidance=["re-capture the tray image"], metrics={})

    h, w = image.shape[:2]
    image_size = image_size or [w, h]
    issues: List[str] = []
    guidance: List[str] = []
    metrics: Dict[str, Any] = {}

    blur = measure_blur(image)
    metrics["laplacian_variance"] = round(blur, 2) if blur is not None else None
    if blur is not None and blur < BLUR_THRESHOLD:
        issues.append("MOTION_BLUR")
        guidance.append("Hold the phone still or rest it on the tray frame; "
                        "re-capture the image.")

    glare = measure_glare(image)
    metrics["glare_fraction"] = round(glare, 4) if glare is not None else None
    if glare is not None and glare > GLARE_FRACTION_THRESHOLD:
        issues.append("GLARE")
        guidance.append("Remove direct light/reflection: shade the tray or move "
                        "the lamp to the side.")

    spread = measure_illumination_spread(image)
    metrics["illumination_std"] = round(spread, 2) if spread is not None else None
    if spread is not None and spread > 60.0:
        issues.append("UNEVEN_ILLUMINATION")
        guidance.append("Lighting is uneven across the tray; use a diffuse, "
                        "overhead light source.")

    if instances is not None and image_size:
        total_area = float(image_size[0] * image_size[1]) or 1.0
        areas = []
        for inst in instances:
            x, y, bw, bh = inst.get("bbox_xywh", [0, 0, 0, 0])
            areas.append((bw * bh) / total_area)
        metrics["onion_count"] = len(instances)
        metrics["max_box_area_fraction"] = round(max(areas), 4) if areas else 0.0
        coverage = 0.0
        if instances:
            mask = np.zeros((int(image_size[1]), int(image_size[0])), dtype=bool)
            for inst in instances:
                x, y, bw, bh = [int(v) for v in inst.get("bbox_xywh", [0, 0, 0, 0])]
                x0, y0 = max(0, x), max(0, y)
                x1 = min(int(image_size[0]), x + max(0, bw))
                y1 = min(int(image_size[1]), y + max(0, bh))
                if x1 > x0 and y1 > y0:
                    mask[y0:y1, x0:x1] = True
            coverage = float(mask.mean())
        metrics["onion_coverage_fraction"] = round(coverage, 4)
        # Cropped / clipping onions: a box touching the image border is truncated.
        clipped = 0
        for inst in instances:
            x, y, bw, bh = inst.get("bbox_xywh", [0, 0, 0, 0])
            if x <= 1 or y <= 1 or (x + bw) >= image_size[0] - 1 \
                    or (y + bh) >= image_size[1] - 1:
                clipped += 1
        metrics["onions_touching_border"] = clipped
        if clipped:
            issues.append("ONION_OUT_OF_FRAME")
            guidance.append(f"{clipped} onion(s) touch the image border; "
                            "re-frame so every onion is fully visible.")
        if coverage > CROWDING_THRESHOLD:
            issues.append("CROWDED_TRAY")
            guidance.append("Spread the onions across the inspection tray so "
                            "they do not overlap.")
        if len(instances) == 0:
            issues.append("NO_ONION_DETECTED")
            guidance.append("No onion detected — check the tray is in frame.")
        elif max(areas) < MIN_ONION_AREA_FRACTION:
            issues.append("ONION_TOO_SMALL")
            guidance.append("Onions are too small in frame; move the camera "
                            "closer or use fewer onions per image.")

    if require_calibration:
        metrics["markers_detected"] = markers_detected or 0
        if not markers_detected:
            issues.append("CALIBRATION_MISSING")
            guidance.append("Place the printed ONION-Q calibration mat in "
                            "frame (see scripts/make_calibration_mat.py) for a "
                            "traceable size measurement.")

    blocking = {"IMAGE_UNREADABLE", "NO_ONION_DETECTED", "CROWDED_TRAY",
                "MOTION_BLUR", "CALIBRATION_MISSING"}
    status = "reject" if blocking & set(issues) else ("warn" if issues else "ok")
    return CaptureQuality(status=status, issues=issues, guidance=guidance,
                          metrics=metrics)
