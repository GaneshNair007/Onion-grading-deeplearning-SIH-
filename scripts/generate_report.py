#!/usr/bin/env python3
"""Generate, sign, render and verify an inspection report.

Two entry points:

    # from a saved batch-scan result
    python scripts/generate_report.py --from-scan local_data/scans/MH-NSK/scans.jsonl

    # verify a report that already exists (QR payload check)
    python scripts/generate_report.py --verify reports/REPORT-....json

Reports are tamper-EVIDENT, not tamper-proof: any edit to the content changes
the canonical hash, and `--verify` reports that. QR rendering needs the
optional `qrcode` package; without it the text payload is still printed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.reporting.audit_hash import verify_integrity                # noqa: E402
from src.reporting.evidence import capture_evidence                  # noqa: E402
from src.reporting.generator import build_report, finalize, write_report  # noqa: E402
from src.reporting.qr import QrUnavailable, QrPayload, render_png    # noqa: E402


def _latest_batch(journal: Path) -> dict:
    if journal.is_dir():
        candidates = sorted(journal.glob("*.jsonl"))
        if not candidates:
            raise SystemExit(f"no .jsonl journal in {journal}")
        journal = candidates[-1]
    if not journal.exists():
        raise SystemExit(f"journal not found: {journal}")
    record = None
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        if entry.get("kind") in {"quick_batch_scan", "batch_scan", "scan"}:
            record = entry
    if record is None:
        raise SystemExit("no batch scan record found in the journal")
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-scan", type=Path, default=None,
                    help="scan result JSON file or journal (jsonl)")
    ap.add_argument("--verify", type=Path, default=None,
                    help="verify an existing report JSON")
    ap.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "reports")
    ap.add_argument("--qr", action="store_true", help="render a QR PNG")
    ap.add_argument("--app-version", default=None,
                    help="override the app version stamped into the report "
                         "(default: the version in src/common/version.py)")
    args = ap.parse_args()

    if args.verify:
        report = json.loads(args.verify.read_text(encoding="utf-8"))
        verdict = verify_integrity(report)
        payload = report.get("qr_payload")
        print(f"report      : {report.get('report_id')}")
        print(f"hash        : {report.get('integrity', {}).get('canonical_hash')}")
        print(f"recomputed  : {verdict.get('actual')}")
        print(f"valid       : {verdict['valid']} ({verdict['reason']})")
        if payload:
            print(f"qr payload  : {payload}")
            decoded = QrPayload(report_id=report["report_id"],
                                report_hash=report["integrity"]["canonical_hash"])
            print(f"qr re-encode: {decoded.encode()}")
        return 0 if verdict["valid"] else 1

    if not args.from_scan:
        ap.error("provide --from-scan or --verify")

    record = _latest_batch(args.from_scan)
    scan = record["payload"]
    batch = scan["batch"]
    report = build_report(
        batch=batch,
        onion_results=[{
            "onion_id": o["onion_id"],
            "source_image": o.get("source_image"),
            "decision": o["decision"]["decision"],
            "reason_codes": o["decision"]["reason_codes"],
            "measurements": o["measurements"],
        } for o in scan.get("onions", [])],
        evidence=capture_evidence(scan.get("images", [])),
        demo_mode=not batch.get("policy", {}).get("source_verified", False),
        app_version=args.app_version,
    )
    finalized = finalize(report)
    written = write_report(finalized, args.out_dir)

    print(f"report_id : {finalized['report_id']}")
    print(f"hash      : {finalized['integrity']['canonical_hash']}")
    print(f"verify    : {verify_integrity(finalized)['valid']}")
    print(f"qr payload: {finalized['qr_payload']}")
    for kind, path in written.items():
        print(f"{kind:<15}: {path}")

    if args.qr:
        payload = QrPayload(report_id=finalized["report_id"],
                            report_hash=finalized["integrity"]["canonical_hash"])
        try:
            png = render_png(payload, Path(written["json"]).with_suffix(".png"))
            print(f"qr image  : {png}")
        except QrUnavailable as exc:
            print(f"qr image  : unavailable — {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
