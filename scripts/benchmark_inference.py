#!/usr/bin/env python3
"""Measure inference latency, honestly (Phase V).

Reports median and p95 latency for the detector, the attribute classifier and a
complete onion, plus a batch throughput figure. Every number is recorded with
the sample count, the hardware and the input size — a latency claim without
those three is not a measurement.

"Real-time" is never printed: the numbers are printed.

Usage:
    python scripts/benchmark_inference.py --images 20
    python scripts/benchmark_inference.py --batch-images demo/tray_calibrated.png
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(pct / 100 * (len(ordered) - 1)))))
    return ordered[index]


def timed(fn: Callable[[], Any], repeats: int) -> Dict[str, Any]:
    durations: List[float] = []
    last = None
    for _ in range(repeats):
        start = time.perf_counter()
        last = fn()
        durations.append((time.perf_counter() - start) * 1000)
    return {
        "n": len(durations),
        "median_ms": round(statistics.median(durations), 1),
        "mean_ms": round(statistics.fmean(durations), 1),
        "p95_ms": round(_percentile(durations, 95), 1),
        "min_ms": round(min(durations), 1),
        "max_ms": round(max(durations), 1),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", type=int, default=10,
                    help="number of dataset images to time the detector on")
    ap.add_argument("--repeats", type=int, default=3,
                    help="timed passes per component")
    ap.add_argument("--batch-images", type=Path, nargs="*", default=None,
                    help="tray image(s) for the end-to-end batch measurement")
    ap.add_argument("--out", type=Path,
                    default=PROJECT_ROOT / "evaluation" / "benchmark_inference.json")
    args = ap.parse_args(argv)

    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {"platform": f"{platform.system()} {platform.release()}",
                 "processor": platform.processor(),
                 "python": sys.version.split()[0]},
        "components": {},
        "notes": [
            "Desktop CPU measurements only — no phone or edge device has been "
            "benchmarked, so no mobile latency claim is made.",
            "timing includes image decoding, which is part of a real request.",
        ],
    }

    # --- detector -------------------------------------------------------------
    try:
        from src.data.dataset_registry import default_registry
        from src.vision.detector import detect_onions, resolve_detector
        detector_path = resolve_detector()
        if detector_path is None:
            report["components"]["detector"] = {
                "status": "unavailable",
                "reason": "no detector artifact; run training/train_detector.py"}
        else:
            registry = default_registry()
            sources = registry.sources()
            samples: List[Path] = []
            for source in sources:
                for record in registry.records(source):
                    samples.append(record["image_path"])
                    if len(samples) >= args.images:
                        break
                if len(samples) >= args.images:
                    break
            if not samples:
                report["components"]["detector"] = {
                    "status": "unavailable",
                    "reason": "dataset not present in this checkout"}
            else:
                first = detect_onions(str(samples[0]))
                repeats = timed(lambda: detect_onions(str(samples[0])),
                                args.repeats)
                per_image = []
                for path in samples:
                    start = time.perf_counter()
                    detect_onions(str(path))
                    per_image.append((time.perf_counter() - start) * 1000)
                report["components"]["detector"] = {
                    "status": first.get("status"),
                    "artifact": str(detector_path),
                    "warm_loop": repeats,
                    "per_image": {
                        "n": len(per_image),
                        "median_ms": round(statistics.median(per_image), 1),
                        "p95_ms": round(_percentile(per_image, 95), 1),
                    },
                    "onions_detected_in_first_image": len(
                        first.get("instances", [])),
                }
    except Exception as exc:  # pragma: no cover - environment dependent
        report["components"]["detector"] = {"status": "error",
                                            "reason": f"{type(exc).__name__}: {exc}"}

    # --- attribute classifier -------------------------------------------------
    try:
        from inference.vision_inference import (classify_vision,
                                                resolve_artifact)
        artifact = resolve_artifact()
        if artifact is None:
            report["components"]["attribute_classifier"] = {
                "status": "unavailable",
                "reason": "attribute artifact missing in this checkout"}
        else:
            from src.data.dataset_registry import default_registry
            registry = default_registry()
            image = None
            for source in registry.sources():
                records = registry.records(source)
                if records:
                    image = records[0]["image_path"]
                    break
            if image is None:
                report["components"]["attribute_classifier"] = {
                    "status": "unavailable", "reason": "dataset not present"}
            else:
                timing = timed(lambda: classify_vision(str(image)), args.repeats)
                report["components"]["attribute_classifier"] = {
                    "status": "measured",
                    "artifact": str(artifact),
                    "image": str(image),
                    "warm_loop": timing,
                }
    except Exception as exc:  # pragma: no cover
        report["components"]["attribute_classifier"] = {
            "status": "error", "reason": f"{type(exc).__name__}: {exc}"}

    # --- end-to-end batch -----------------------------------------------------
    batch_images = args.batch_images or []
    if not batch_images:
        default_tray = PROJECT_ROOT / "demo" / "tray_calibrated.png"
        if default_tray.exists():
            batch_images = [default_tray]
    if batch_images:
        try:
            from inference.combined_scan import scan_tray_batch
            start = time.perf_counter()
            result = scan_tray_batch([str(p) for p in batch_images],
                                     center_id="BENCH")
            elapsed = (time.perf_counter() - start) * 1000
            onion_count = len(result.get("onions", []))
            report["components"]["batch_end_to_end"] = {
                "images": [str(p) for p in batch_images],
                "onions_detected": onion_count,
                "total_ms": round(elapsed, 1),
                "ms_per_onion": (round(elapsed / onion_count, 1)
                                 if onion_count else None),
                "onions_per_second": (round(onion_count / (elapsed / 1000), 3)
                                      if elapsed and onion_count else None),
                "note": ("End-to-end includes detection, cropping, attribute "
                         "classification and the policy engine."),
            }
        except Exception as exc:  # pragma: no cover
            report["components"]["batch_end_to_end"] = {
                "status": "error", "reason": f"{type(exc).__name__}: {exc}"}

    report["statement"] = (
        "Latency is reported with sample counts and hardware. No mobile figure "
        "exists, and 'real-time' is a claim this project does not make without "
        "device measurements.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
