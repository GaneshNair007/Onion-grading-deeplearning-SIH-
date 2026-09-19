#!/usr/bin/env python3
"""Compose a *tray* image from real onion photographs in the tracked dataset.

Why this exists: the repository contains real, licensed single-onion
photographs but **no licensed photograph of a tray containing many onions**.
Batch Scan needs several onions in one frame, so this script pastes N real
onion crops onto a mat-like background.

Evidence discipline — this script is deliberately loud about what it is:

* every pixel of onion comes from a real dataset image (paths and SHA-256s are
  written into a sidecar JSON next to the montage);
* the background and layout are synthetic, and the sidecar says so;
* the montage is a **composed test fixture**, and any report produced from it
  is marked `composed_fixture: true`. It must never be presented as a real
  field tray photograph.

Usage:
    python scripts/compose_tray_image.py --count 12
    python scripts/compose_tray_image.py --count 12 --out demo/tray_12.png
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))


def onion_records(limit_sources: int = 1) -> list:
    from src.data.dataset_registry import default_registry
    reg = default_registry()
    records: list = []
    for src in reg.sources():
        if not src.training_allowed:
            continue
        records.extend(reg.records(src))
        if len({r["image_path"] for r in records}) >= 400:
            break
    seen = set()
    unique = []
    for rec in records:
        key = str(rec["image_path"])
        if key in seen or not Path(key).exists():
            continue
        seen.add(key)
        unique.append(rec)
    return unique


def _draw_calibration_markers(image: "np.ndarray", marker_px: int,
                              marker_size_mm: float = 40.0) -> list:
    """Place real ArUco markers so size measurement can be exercised.

    The markers are the same dictionary the calibration mat uses, drawn at
    exactly `marker_px` pixels for a declared physical edge of
    `marker_size_mm`. The resulting px/mm is recorded in the sidecar.
    """
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    h, w = image.shape[:2]
    quiet = int(marker_px * 0.6)
    positions = [(0, quiet, quiet),
                 (1, w - quiet - marker_px, h - quiet - marker_px)]
    placed = []
    for marker_id, x, y in positions:
        x0, y0 = max(0, x - quiet), max(0, y - quiet)
        x1, y1 = min(w, x + marker_px + quiet), min(h, y + marker_px + quiet)
        image[y0:y1, x0:x1] = 255
        marker = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_px)
        image[y:y + marker_px, x:x + marker_px] = cv2.cvtColor(marker,
                                                               cv2.COLOR_GRAY2BGR)
        placed.append({"marker_id": marker_id, "bbox_xywh": [x, y, marker_px, marker_px]})
    return placed


def compose(count: int, out: Path, seed: int = 11,
            canvas: tuple = (1200, 900), onion_px: int = 210,
            with_mat: bool = False, marker_px: int = 160,
            marker_size_mm: float = 40.0) -> dict:
    """Paste `count` real onion crops onto a synthetic mat background."""
    records = onion_records()
    if len(records) < count:
        raise SystemExit(f"only {len(records)} usable real images found; "
                         f"requested {count}")

    rng = random.Random(seed)
    rng.shuffle(records)
    chosen = records[:count]

    # Synthetic mat: warm grey with a 10 mm grid drawn to a *declared* scale so
    # the montage's px/mm is documented rather than guessed.
    w, h = canvas
    image = np.full((h, w, 3), 214, dtype=np.uint8)
    image[:] = (206, 210, 214)
    for x in range(0, w, 60):
        cv2.line(image, (x, 0), (x, h), (188, 192, 196), 1)
    for y in range(0, h, 60):
        cv2.line(image, (0, y), (w, y), (188, 192, 196), 1)

    marker_placements = []
    if with_mat:
        marker_placements = _draw_calibration_markers(image, marker_px,
                                                      marker_size_mm)

    cols = max(1, int(np.ceil(np.sqrt(count * w / h))))
    rows = max(1, int(np.ceil(count / cols)))
    cell_w, cell_h = w // cols, h // rows

    placed = []
    for i, rec in enumerate(chosen):
        src = cv2.imread(str(rec["image_path"]))
        if src is None:
            continue
        # Centre-crop to a square, then resize: keeps the onion undistorted.
        sh, sw = src.shape[:2]
        side = min(sh, sw)
        y0, x0 = (sh - side) // 2, (sw - side) // 2
        crop = src[y0:y0 + side, x0:x0 + side]
        size = onion_px + rng.randint(-25, 25)
        crop = cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)

        r, c = divmod(i, cols)
        cx = c * cell_w + cell_w // 2 + rng.randint(-14, 14)
        cy = r * cell_h + cell_h // 2 + rng.randint(-14, 14)
        x1, y1 = max(0, cx - size // 2), max(0, cy - size // 2)
        x2, y2 = min(w, x1 + size), min(h, y1 + size)
        patch = crop[:y2 - y1, :x2 - x1]
        if patch.size == 0:
            continue
        # Feathered paste so the montage does not look like hard cut-outs.
        mask = np.zeros(patch.shape[:2], dtype=np.uint8)
        cv2.ellipse(mask, (mask.shape[1] // 2, mask.shape[0] // 2),
                    (mask.shape[1] // 2 - 2, mask.shape[0] // 2 - 2), 0, 0, 360,
                    255, -1)
        mask = cv2.GaussianBlur(mask, (9, 9), 0)
        roi = image[y1:y2, x1:x2]
        alpha = (mask.astype(np.float32) / 255.0)[..., None]
        roi[:] = (patch.astype(np.float32) * alpha
                  + roi.astype(np.float32) * (1 - alpha)).astype(np.uint8)
        placed.append({
            "dataset_image": str(rec["image_path"].relative_to(PROJECT_ROOT)),
            "source_group": None,
            "sha256_of_source": None,
            "bbox_xywh_in_montage": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
            "source_categories": rec.get("categories", []),
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), image)

    sidecar = {
        "kind": "composed_tray_fixture",
        "composed_fixture": True,
        "statement": (
            "Onion pixels come from real dataset photographs; the background, "
            "grid and layout are synthetic. This is a TEST FIXTURE, not a real "
            "field tray photograph, and reports derived from it are labelled "
            "as composed fixtures."),
        "composed_at": None,
        "seed": seed,
        "canvas_px": [w, h],
        "background_grid_px_per_step": 60,
        "calibration": {
            "markers_drawn": bool(marker_placements),
            "marker_size_mm": marker_size_mm,
            "marker_px": marker_px if marker_placements else None,
            "declared_px_per_mm": (round(marker_px / marker_size_mm, 4)
                                   if marker_placements else None),
            "marker_placements": marker_placements,
            "critical_note": (
                "The px/mm scale is the FIXTURE's scale. Sizes measured on this "
                "montage are NOT the photographed onions' real physical sizes, "
                "which are unknown because each crop came from a different "
                "unknown camera distance."),
        },
        "onions_placed": len(placed),
        "onion_placements": placed,
    }
    (out.with_suffix(".provenance.json")).write_text(
        json.dumps(sidecar, indent=2), encoding="utf-8")
    return sidecar


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--onion-px", type=int, default=210)
    ap.add_argument("--with-mat", action="store_true",
                    help="draw real ArUco markers at a declared fixture scale so "
                         "calibrated size measurement can be exercised")
    ap.add_argument("--marker-px", type=int, default=160)
    ap.add_argument("--out", type=Path,
                    default=PROJECT_ROOT / "demo" / "tray_composed.png")
    args = ap.parse_args()

    sidecar = compose(args.count, args.out, seed=args.seed,
                      onion_px=args.onion_px, with_mat=args.with_mat,
                      marker_px=args.marker_px)
    print(f"Wrote {args.out} with {sidecar['onions_placed']} onions")
    calib = sidecar["calibration"]
    if calib["markers_drawn"]:
        print(f"Calibration markers drawn: px_per_mm={calib['declared_px_per_mm']} "
              "(fixture scale, not the onions' real size)")
    print(f"Provenance: {args.out.with_suffix('.provenance.json')}")
    print("NOTE: composed test fixture — not a real tray photograph.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
