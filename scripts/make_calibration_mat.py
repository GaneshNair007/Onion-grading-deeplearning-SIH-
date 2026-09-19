#!/usr/bin/env python3
"""Generate the printable ONION-Q calibration mat (Tier-1 size measurement).

The mat contains:
* four ArUco DICT_4X4_50 markers (ids 0-3) placed on a known square,
* a reference grid in 10 mm steps,
* printed text stating the marker edge length so the field user can verify it
  with a ruler after printing.

**Print at 100 % scale (no "fit to page")** and verify marker 0 measures
exactly `--marker-mm` with a ruler before first field use — paper scaling is
the dominant error source.

Usage:
    python scripts/make_calibration_mat.py --out demo/calibration_mat_A4_300dpi.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DPI = 300
MM_PER_INCH = 25.4


def mm_to_px(mm: float, dpi: int = DPI) -> int:
    return int(round(mm / MM_PER_INCH * dpi))


def build_mat(width_mm: float = 297.0, height_mm: float = 210.0,
              marker_mm: float = 40.0, margin_mm: float = 30.0,
              dpi: int = DPI) -> np.ndarray:
    """A4 landscape mat: white sheet, 4 markers, 10 mm grid."""
    w, h = mm_to_px(width_mm, dpi), mm_to_px(height_mm, dpi)
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)

    # 10 mm grid, light grey, with a stronger 50 mm line.
    step = mm_to_px(10, dpi)
    for x in range(0, w, step):
        colour = (150, 150, 150) if (x // step) % 5 else (90, 90, 90)
        cv2.line(canvas, (x, 0), (x, h), colour, 1)
    for y in range(0, h, step):
        colour = (150, 150, 150) if (y // step) % 5 else (90, 90, 90)
        cv2.line(canvas, (0, y), (w, y), colour, 1)

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker_px = mm_to_px(marker_mm, dpi)
    m = mm_to_px(margin_mm, dpi)
    positions = [
        (0, m, m),
        (1, w - m - marker_px, m),
        (2, w - m - marker_px, h - m - marker_px),
        (3, m, h - m - marker_px),
    ]
    def put(text: str, y_mm: float, scale_mm: float = 5.0, colour=(0, 0, 0)):
        px = mm_to_px(scale_mm, dpi) / 4.0
        cv2.putText(canvas, text, (mm_to_px(20, dpi), mm_to_px(y_mm, dpi)),
                    cv2.FONT_HERSHEY_SIMPLEX, max(px, 0.5), colour,
                    max(int(px * 1.5), 1), cv2.LINE_AA)

    # Text is drawn BEFORE the markers: large text placed later can overlap a
    # marker and make it undetectable (verified while writing this script).
    put("ONION-Q CALIBRATION MAT - PRINT AT 100% (no scaling)", height_mm / 2 - 20)
    put(f"ArUco DICT_4X4_50  |  marker edge = {marker_mm:.0f} mm  |  grid = 10 mm",
        height_mm / 2 - 10)
    put("VERIFY with a ruler before first use.", height_mm / 2, colour=(0, 0, 200))

    # A white quiet zone around each marker: required for reliable detection
    # both on screen and on a printed sheet (grid lines touching a marker edge
    # break the detector — verified while writing this script).
    # 20 mm of clear space is wider than the 10 mm grid step, so no grid line
    # can run alongside a marker border (a line touching the border stops the
    # detector — verified while writing this script).
    quiet = mm_to_px(20, dpi)
    for marker_id, x, y in positions:
        img = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_px)
        x0, y0 = max(0, x - quiet), max(0, y - quiet)
        x1 = min(w, x + marker_px + quiet)
        y1 = min(h, y + marker_px + quiet)
        canvas[y0:y1, x0:x1] = 255
        scale = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        canvas[y:y + marker_px, x:x + marker_px] = scale

    # NOTE: no decorative frame is drawn around the markers. An earlier version
    # drew an inner rectangle whose lines touched the marker borders, and the
    # detector then missed those two markers. Any line touching a marker's
    # black border breaks detection, so the layout keeps a 20 mm clear zone.

    return canvas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path,
                    default=PROJECT_ROOT / "demo" / "calibration_mat_A4_300dpi.png")
    ap.add_argument("--marker-mm", type=float, default=40.0)
    args = ap.parse_args()

    mat = build_mat(marker_mm=args.marker_mm)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out), mat)
    print(f"Wrote {args.out}  ({mat.shape[1]}x{mat.shape[0]} px @ {DPI} dpi)")

    # Self-check: the markers we just drew must be detectable and measure the
    # requested physical size through the same code path used in the field.
    from src.vision.size import detect_markers, pixel_per_mm  # noqa: E402
    markers = detect_markers(mat)
    scale = pixel_per_mm(markers, args.marker_mm)
    if scale is None:
        print("ERROR: drawn markers are not detectable.", file=sys.stderr)
        return 1
    expected = mm_to_px(args.marker_mm) / args.marker_mm
    err = abs(scale - expected) / expected * 100
    print(f"markers detected: {len(markers)}  measured px/mm={scale:.4f}  "
          f"expected={expected:.4f}  error={err:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
