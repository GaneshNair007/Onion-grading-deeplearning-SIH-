#!/usr/bin/env python3
"""MODE B demo — Deep Scan (guided views + optional phone acoustic test).

Real use (four photographs of the SAME onion):

    python scripts/demo_deep_scan.py \
        --views neck=neck.jpg base=base.jpg side_a=a.jpg side_b=b.jpg \
        --audio tap_equator_01.wav

Pipeline rehearsal without real multi-angle data:

    python scripts/demo_deep_scan.py --demo-views 4

`--demo-views N` deliberately uses N *different* real dataset onions and marks
the run `demo_mode=true` with a loud warning, because four photographs of four
different onions are NOT a multi-angle inspection of one onion. It exercises
the code path; it must never be shown as a real Deep Scan result.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from inference.combined_scan import deep_scan_onion, save_scan_result  # noqa: E402
from src.grading.policy import active_policy                           # noqa: E402
from src.vision.multi_view import GUIDED_VIEWS                         # noqa: E402


def _parse_views(pairs: list) -> dict:
    views = {}
    for item in pairs:
        if "=" not in item:
            raise SystemExit(f"--views expects view=path, got '{item}'")
        name, path = item.split("=", 1)
        if name not in GUIDED_VIEWS:
            raise SystemExit(f"unknown view '{name}'; allowed: {GUIDED_VIEWS}")
        views[name] = path
    return views


def _demo_views(count: int) -> dict:
    from src.data.dataset_registry import default_registry
    reg = default_registry()
    images = []
    for src in reg.sources():
        if not src.training_allowed:
            continue
        images.extend(str(r["image_path"]) for r in reg.records(src))
        if len(images) >= count:
            break
    if len(images) < count:
        raise SystemExit(f"only {len(images)} real images available")
    return {view: images[i] for i, view in enumerate(GUIDED_VIEWS[:count])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--views", nargs="*", default=[])
    ap.add_argument("--demo-views", type=int, default=0,
                    help="use N DIFFERENT real onions to rehearse the pipeline")
    ap.add_argument("--audio", default=None)
    ap.add_argument("--acoustic-model", default=None)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--center", default="MH-NSK")
    ap.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "reports")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    demo_mode = False
    if args.views:
        views = _parse_views(args.views)
    elif args.demo_views:
        views = _demo_views(args.demo_views)
        demo_mode = True
    else:
        ap.error("provide --views or --demo-views N")

    if demo_mode:
        print("WARNING: --demo-views uses DIFFERENT real onions for each view.")
        print("         This is a pipeline rehearsal, NOT a multi-angle scan")
        print("         of one onion. Results are marked demo_mode=true.\n")

    policy = active_policy(args.policy)
    result = deep_scan_onion(views, policy, audio_path=args.audio,
                             acoustic_model=args.acoustic_model,
                             progress=True)
    result["demo_mode"] = demo_mode

    print("\n  GUIDED VIEWS")
    for view in result.get("view_instructions", []):
        print(f"    {view['view']:<7}: {view['prompt']}")

    fused = result.get("views", {})
    print("\n  MULTI-VIEW FUSION")
    print(f"    coverage        : {fused.get('coverage_status')} "
          f"(captured {len(fused.get('views_captured', []))}/4)")
    print(f"    label           : {fused.get('label')}")
    print(f"    confidence      : {fused.get('multi_view_confidence')}")
    print(f"    view disagreement: {fused.get('view_disagreement')}")
    for name, defect in (fused.get("visible_defects") or {}).items():
        print(f"      {name:<8} detected={defect['detected']} "
              f"max_conf={defect['max_confidence']} per_view={defect['per_view_confidence']}")

    geometry = result.get("best_geometry", {})
    print(f"\n  SIZE: method={geometry.get('size_method')} "
          f"diameter_mm={geometry.get('diameter_mm')}")

    acoustic = result.get("acoustic")
    if acoustic:
        print("\n  ACOUSTIC")
        print(f"    status      : {acoustic.get('status')}")
        print(f"    probability : {acoustic.get('internal_defect_probability')}")
        print(f"    confidence  : {acoustic.get('confidence')}")
        print(f"    model       : {acoustic.get('model_version')}")
        quality = acoustic.get("audio_quality") or {}
        print(f"    audio quality: passed={quality.get('passed')} "
              f"snr_db={quality.get('snr_db')} issues={quality.get('issues')}")
        for warning in acoustic.get("warnings", []):
            print(f"    ! {warning}")
    else:
        print("\n  ACOUSTIC: not performed (no --audio supplied)")

    fusion = result.get("fusion")
    if fusion:
        print("\n  FUSION")
        print(f"    status : {fusion.get('status')}")
        print(f"    final  : {fusion.get('final')}")

    decision = result.get("decision")
    print("\n  PROCUREMENT DECISION")
    if decision:
        print(f"    decision : {decision['decision'].upper()}")
        print(f"    policy   : {decision['policy_id']} v{decision['policy_version']} "
              f"(verified={decision['policy_verified']})")
        for text in decision["reasons_text"]:
            print(f"      - {text}")
    else:
        print("    none (the object was not identified as an onion)")

    saved = save_scan_result(result, center_id=args.center, device_id="demo-cli")
    print(f"\n  offline journal: {saved['journal']} record {saved['record_id']}")

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
