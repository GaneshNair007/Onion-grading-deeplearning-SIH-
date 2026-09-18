#!/usr/bin/env python3
"""End-to-end local demo of the multimodal onion scan.

Runs the vision model on an image, optionally runs the acoustic pipeline on
a WAV, fuses the evidence, and prints the shared result contract.

IMPORTANT HONESTY NOTES (also printed with every run):
- The vision artifact was trained on synthetic images; it is not validated
  on real onions.
- The acoustic artifact (if trained via training/train_acoustic.py) is a
  clearly-labelled SYNTHETIC demo model. It is NOT an onion internal-defect
  detector and is not clinically or industrially validated.

Usage:
    python scripts/demo_onion_scan.py path/to/onion.jpg
    python scripts/demo_onion_scan.py path/to/onion.jpg --audio path/to/tap.wav
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "inference"))

HONESTY_BANNER = (
    "NOTE: demo models are trained on synthetic data (see models/*/README.md); "
    "they are NOT validated on real onions and must not be presented as "
    "industrial grading results.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image_path", type=Path)
    ap.add_argument("--audio", type=Path, default=None,
                    help="optional WAV recording for the acoustic test")
    ap.add_argument("--compact", action="store_true",
                    help="print only the final block")
    args = ap.parse_args()

    if not args.image_path.exists():
        print(f"ERROR: image not found: {args.image_path}", file=sys.stderr)
        return 1

    from vision_inference import classify_vision
    vision_result = classify_vision(str(args.image_path))

    acoustic_result = None
    if args.audio:
        if not args.audio.exists():
            print(f"ERROR: audio not found: {args.audio}", file=sys.stderr)
            return 1
        from acoustic_inference import classify_acoustic
        acoustic_result = classify_acoustic(str(args.audio))

    from src.fusion import fuse_results
    fused = fuse_results(vision_result, acoustic_result)

    output = {
        "is_onion": fused.get("is_onion", False),
        "vision": {
            "label": vision_result["vision"]["label"],
            "confidence": vision_result["vision"]["confidence"],
            "defects": vision_result["vision"]["defects"],
            "model_version": vision_result["vision"]["model_version"],
        },
        "acoustic": None if not acoustic_result else {
            "status": acoustic_result["status"],
            "internal_defect_probability": acoustic_result.get("internal_defect_probability"),
            "confidence": acoustic_result.get("confidence"),
            "audio_quality": acoustic_result.get("audio_quality", {}).get("quality_score"),
            "model_version": acoustic_result.get("model_version"),
        },
        "final": fused["final"],
        "status": fused.get("status"),
        "warnings": fused.get("warnings", []) + [HONESTY_BANNER],
    }

    if not args.compact:
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output["final"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
