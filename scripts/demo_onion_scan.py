#!/usr/bin/env python3
"""Combined onion-scan demo (vision + optional acoustic, fused).

Usage
-----
    python scripts/demo_onion_scan.py --image path/to/onion.jpg
    python scripts/demo_onion_scan.py --image path/to/onion.jpg \
        --audio path/to/tap_recording.wav

Shows: onion detection, the vision prediction + confidence, the acoustic
status/prediction when audio is supplied, the final fused result, and honest
warnings (untrained model, insufficient data, low confidence). It reuses the
same inference modules and fusion rules as the API server — no separate demo
logic, no fabricated outputs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from inference.vision_inference import classify_vision  # noqa: E402
from src.fusion.fusion import fuse_results  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True, help="path to an onion/vegetable photo")
    ap.add_argument("--audio", help="optional WAV recording (chirp response or tap)")
    ap.add_argument("--policy", default="demo_policy", help="grading policy id")
    args = ap.parse_args()

    if not Path(args.image).exists():
        print(f"error: image not found: {args.image}", file=sys.stderr)
        return 2

    print("=" * 64)
    print("ONION-Q combined scan demo")
    print("=" * 64)

    vision = classify_vision(args.image)
    is_onion = vision.get("is_onion")
    print(f"\n1) Onion detection      : {is_onion!r}")
    v = vision.get("vision") or {}
    print(f"   vision label         : {v.get('label')}")
    print(f"   vision confidence    : {v.get('confidence')}")
    print(f"   defects              : {v.get('defects')}")
    for w in vision.get("warnings", []):
        print(f"   warning              : {w}")

    acoustic = None
    if args.audio:
        if not Path(args.audio).exists():
            print(f"error: audio not found: {args.audio}", file=sys.stderr)
            return 2
        from inference.acoustic_inference import classify_acoustic

        acoustic = classify_acoustic(args.audio)
        print(f"\n2) Acoustic status      : {acoustic.get('status')}")
        print(f"   internal-defect prob : {acoustic.get('internal_defect_probability')}"
              f"   (research-only: {acoustic.get('research_only')})")
        print(f"   acoustic confidence  : {acoustic.get('confidence')}")
        q = acoustic.get("audio_quality") or {}
        print(f"   audio SNR / clipping : {q.get('snr_db')} dB / {q.get('clipping')}")
        for w in acoustic.get("warnings", []):
            print(f"   warning              : {w}")

    print("\n3) Fused result")
    fused = fuse_results(vision, acoustic) if acoustic is not None else None
    if fused is None:
        print("   status               : vision_only")
        print("   (no audio supplied — vision-only flow)")
    else:
        final = fused.get("final") or {}
        print(f"   status               : {fused.get('status')}")
        print(f"   final label          : {final.get('label')}")
        print(f"   freshness score      : {final.get('freshness_score')} (null = no such model exists)")
        print(f"   reason               : {final.get('reason')}")
        for w in fused.get("warnings", []):
            print(f"   warning              : {w}")

    print("\n4) Warnings / data honesty")
    print("   - Acoustic model (if any) is a synthetic-data demo; it can NEVER")
    print("     change a procurement grade until real cut-open-labelled onion")
    print("     audio is collected (dataset-acoustic/collection_protocol.md).")
    print("   - freshness_score is null everywhere: no longitudinal labels exist.")

    print("\nFull JSON:")
    print(json.dumps({"vision": vision, "acoustic": acoustic, "fused": fused},
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
