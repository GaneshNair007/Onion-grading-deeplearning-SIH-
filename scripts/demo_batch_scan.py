#!/usr/bin/env python3
"""MODE A demo — Quick Batch Scan, from tray image to signed report.

    python scripts/demo_batch_scan.py --compose 12
    python scripts/demo_batch_scan.py --images demo/tray_field.png --lot LOT-2026-0182

Every number printed here comes from a real model call. If the detector or
attribute artifact is missing the demo says so and exits non-zero instead of
printing plausible-looking grades.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from inference.combined_scan import scan_tray_batch, save_scan_result  # noqa: E402
from src.grading.policy import active_policy                           # noqa: E402
from src.reporting.audit_hash import verify_integrity                  # noqa: E402
from src.reporting.evidence import capture_evidence                   # noqa: E402
from src.reporting.generator import build_report, finalize, write_report  # noqa: E402


def _print_table(batch: dict) -> None:
    counts = batch["counts"]
    totals = batch["totals"]
    pct = batch["percentages"]
    print("\n  BATCH SUMMARY")
    print(f"    batch      : {batch['batch_id']}   lot: {batch.get('lot_id') or '-'}")
    print(f"    policy     : {batch['policy']['policy_id']} v{batch['policy']['version']}"
          f"  verified={batch['policy']['source_verified']}")
    print(f"    detected   : {totals['total_detected']}")
    for name in ("grade_a", "relaxed", "reject", "manual_review"):
        print(f"    {name:<11}: {counts.get(name, 0):>4}   ({pct.get(name, 0):>5.1f}%)")
    if totals.get("non_onion_rejected"):
        print(f"    non-onion  : {totals['non_onion_rejected']}")
    if batch.get("mean_confidence") is not None:
        print(f"    mean conf  : {batch['mean_confidence']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", nargs="*", default=[],
                    help="one or more tray images")
    ap.add_argument("--compose", type=int, default=0,
                    help="compose a tray fixture from N real dataset onions")
    ap.add_argument("--policy", default=None)
    ap.add_argument("--center", default="MH-NSK")
    ap.add_argument("--inspector", default="INSP-001")
    ap.add_argument("--batch-id", default=None)
    ap.add_argument("--lot", default=None)
    ap.add_argument("--with-mat", action="store_true",
                    help="with --compose: draw ArUco calibration markers on the "
                         "composed tray so calibrated size measurement runs")
    ap.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "reports")
    ap.add_argument("--no-calibration", action="store_true",
                    help="do not require the calibration mat to be visible")
    ap.add_argument("--json", action="store_true", help="print full JSON")
    args = ap.parse_args()

    images = list(args.images)
    composed_fixture = False
    if args.compose:
        from scripts.compose_tray_image import compose
        out = PROJECT_ROOT / "demo" / "tray_composed.png"
        sidecar = compose(args.compose, out, with_mat=args.with_mat)
        images = [str(out)]
        composed_fixture = True
        print(f"Composed fixture: {out} ({sidecar['onions_placed']} real onions, "
              "synthetic background — NOT a field photograph)"
              + (" + ArUco mat markers" if args.with_mat else ""))
    if not images:
        ap.error("provide --images or --compose N")

    policy = active_policy(args.policy)
    result = scan_tray_batch(images, policy, center_id=args.center,
                             inspector_id=args.inspector,
                             batch_id=args.batch_id, lot_id=args.lot,
                             require_calibration=not args.no_calibration,
                             progress=True)

    batch = result["batch"]
    if not result["onions"]:
        print("\nNo onion instances were produced. Detector status: "
              f"{result['images'][0].get('detector', {}).get('status')}")
        for warning in result.get("warnings", []):
            print(f"  ! {warning}")
        return 2

    _print_table(batch)
    print("\n  CAPTURE QUALITY PER IMAGE")
    for img in result["images"]:
        quality = img.get("capture_quality") or {}
        print(f"    {Path(img['image']).name}: {quality.get('status')} "
              f"{quality.get('issues')}")
        for line in quality.get("guidance", []):
            print(f"      guide: {line}")

    report = build_report(
        batch=batch,
        onion_results=[{
            "onion_id": o["onion_id"],
            "source_image": o["source_image"],
            "decision": o["decision"]["decision"],
            "reason_codes": o["decision"]["reason_codes"],
            "measurements": o["measurements"],
            "crop_box": o["crop_box"],
        } for o in result["onions"]],
        # Hash the actual tray image(s) as evidence: the report then records
        # *which* image was graded, not merely that one existed.
        evidence=capture_evidence(result["images"]),
        demo_mode=not policy.source_verified,
    )
    report["composed_fixture"] = composed_fixture
    if composed_fixture:
        report["notes"] = (report.get("notes", "") +
                           " Source image is a COMPOSED FIXTURE built from real "
                           "onion photographs on a synthetic tray background.")
    finalized = finalize(report)
    written = write_report(finalized, args.out_dir)

    integrity = finalized["integrity"]["canonical_hash"]
    print("\n  REPORT")
    print(f"    id      : {finalized['report_id']}")
    print(f"    hash    : {integrity}")
    print(f"    qr      : {finalized['qr_payload']}")
    for kind, path in written.items():
        print(f"    {kind:<15}: {path}")
    verdict = verify_integrity(finalized)
    print(f"    integrity verify: {verdict['valid']} ({verdict['reason']})")

    saved = save_scan_result(result, center_id=args.center, device_id="demo-cli")
    print(f"    offline journal : {saved['journal']} record {saved['record_id']}")

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
