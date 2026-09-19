#!/usr/bin/env python3
"""Export the cases a human should look at next (Phase N — active learning).

Pulls, from the stored reports + the server store, the onions that are most
informative for improving the system:

* low-confidence decisions (the model was unsure);
* human overrides (the inspector disagreed with the machine);
* manual-review escalations with their reason codes;
* out-of-distribution / non-onion rejections;
* capture-quality failures that prevented grading at all.

What this script deliberately does NOT do
-----------------------------------------
It never retrains, never relabels and never deletes. It writes a *queue* plus a
manifest, so a human decides what becomes training data and the provenance of
that data stays explicit. Auto-training on the model's own uncertain output is
how label noise gets baked in permanently.

Usage:
    python scripts/export_review_queue.py
    python scripts/export_review_queue.py --store local_data/server/onionq.sqlite3 \
        --out review-export --db local_data/server/onionq.sqlite3
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.reasons import (CALIBRATION_MISSING, INTERNAL_DEFECT_RISK,
                                LOW_MODEL_CONFIDENCE, MEASUREMENT_UNAVAILABLE,
                                MODEL_UNAVAILABLE, MULTIMODAL_DISAGREEMENT,
                                NOT_AN_ONION, OCCLUSION_HIGH)

#: Reason codes that mean "the pipeline could not decide" — the highest-value
#: candidates for new labelled data.
REVIEW_CODES = {LOW_MODEL_CONFIDENCE, MULTIMODAL_DISAGREEMENT, OCCLUSION_HIGH,
                CALIBRATION_MISSING, MEASUREMENT_UNAVAILABLE, MODEL_UNAVAILABLE,
                INTERNAL_DEFECT_RISK}

#: Confidence below which a case is worth a human look even if it was graded.
LOW_CONFIDENCE_FLOOR = 0.65

FIELDS = ["case_id", "category", "onion_id", "batch_id", "center_id",
          "inspector_id", "source_image", "machine_decision", "human_decision",
          "reason_codes", "confidence", "model_version", "requires_label",
          "suggested_label_field"]


def load_reports(report_dir: Path) -> List[Dict[str, Any]]:
    out = []
    if not report_dir.exists():
        return out
    for path in sorted(report_dir.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue          # a corrupt report must not stop the export
    return out


def load_overrides(db_path: Path) -> List[Dict[str, Any]]:
    if not db_path.exists():
        return []
    from server.store import Store
    return Store(db_path).overrides()


def cases_from_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    header = report.get("header") or {}
    summary = report.get("summary") or {}
    notes = (report.get("notes") or "")
    cases: List[Dict[str, Any]] = []

    for onion in report.get("onion_results") or []:
        codes = list(onion.get("reason_codes") or [])
        measurements = onion.get("measurements") or {}
        confidence = measurements.get("model_confidence")
        caught = [c for c in codes if c in REVIEW_CODES]
        low_conf = (confidence is not None
                    and float(confidence) < LOW_CONFIDENCE_FLOOR)
        if not caught and not low_conf:
            continue
        category = ("low_confidence" if low_conf and not caught
                    else "review_escalation")
        cases.append({
            "case_id": f"{report.get('report_id')}:{onion.get('onion_id')}",
            "category": category,
            "onion_id": onion.get("onion_id"),
            "batch_id": header.get("batch_id"),
            "center_id": header.get("center_id"),
            "inspector_id": header.get("inspector_id"),
            "source_image": onion.get("source_image"),
            "machine_decision": onion.get("decision"),
            "human_decision": "",
            "reason_codes": "|".join(codes),
            "confidence": confidence,
            "model_version": (header.get("model_versions") or {}).get("attributes"),
            "requires_label": "yes",
            "suggested_label_field": ("visible rot / sprout confirmation "
                                      "(cut-open ground truth)"),
        })

    # Capture failures prevented any per-onion grading: record the input itself.
    for evidence in report.get("evidence") or []:
        quality = evidence.get("capture_quality") or {}
        if quality.get("status") in {"reject", "retake"}:
            cases.append({
                "case_id": f"{report.get('report_id')}:capture:{evidence.get('file_name')}",
                "category": "capture_failure",
                "onion_id": "",
                "batch_id": header.get("batch_id"),
                "center_id": header.get("center_id"),
                "inspector_id": header.get("inspector_id"),
                "source_image": evidence.get("path"),
                "machine_decision": "not_graded",
                "human_decision": "",
                "reason_codes": "|".join(quality.get("issues") or []),
                "confidence": None,
                "model_version": None,
                "requires_label": "yes",
                "suggested_label_field": "recapture with better framing/lighting",
            })

    if "COMPOSED FIXTURE" in notes:
        for case in cases:
            case["category"] += ":fixture"
    return cases


def cases_from_overrides(overrides: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in overrides:
        machine = row.get("machine_decision")
        human = row.get("human_decision")
        category = ("human_override" if machine and machine != human
                    else "human_confirmation")
        out.append({
            "case_id": row.get("override_id"),
            "category": category,
            "onion_id": row.get("onion_id"),
            "batch_id": row.get("batch_id"),
            "center_id": row.get("center_id"),
            "inspector_id": row.get("inspector_id"),
            "source_image": "",
            "machine_decision": machine,
            "human_decision": human,
            "reason_codes": row.get("reason_code") or row.get("reason") or "",
            "confidence": row.get("machine_confidence"),
            "model_version": row.get("model_version"),
            "requires_label": "yes",
            "suggested_label_field": "verified human decision (ground truth)",
        })
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reports", type=Path, default=PROJECT_ROOT / "reports")
    ap.add_argument("--db", type=Path,
                    default=PROJECT_ROOT / "local_data" / "server" / "onionq.sqlite3")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "review-export")
    args = ap.parse_args(argv)

    reports = load_reports(args.reports)
    overrides = load_overrides(args.db)
    cases: List[Dict[str, Any]] = []
    for report in reports:
        cases.extend(cases_from_report(report))
    cases.extend(cases_from_overrides(overrides))

    # Deterministic order: category, then case id.
    cases.sort(key=lambda c: (str(c["category"]), str(c["case_id"])))

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "review_queue.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for case in cases:
            writer.writerow({k: case.get(k, "") for k in FIELDS})

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reports_scanned": len(reports),
        "overrides_scanned": len(overrides),
        "cases": len(cases),
        "by_category": dict(Counter(c["category"] for c in cases)),
        "low_confidence_floor": LOW_CONFIDENCE_FLOOR,
        "statement": (
            "This queue is a work list for humans. Nothing here was auto-labelled "
            "or auto-trained: the model's uncertain output is not ground truth. "
            "Every promoted case must carry a real label and a source."),
        "how_to_use": [
            "1. Inspect each case and record the true label (cut-open ground "
            "truth for internal condition).",
            "2. Add it with the tools in docs/REAL_DATA_TOOLING.md so provenance "
            "and licence are recorded.",
            "3. Retrain only with the labelled set, then re-evaluate on the "
            "held-out grouped split.",
        ],
    }
    (args.out / "review_queue.json").write_text(json.dumps(manifest, indent=2),
                                                encoding="utf-8")
    (args.out / "README.md").write_text(
        "# Review queue\n\n"
        f"Generated {manifest['generated_at']} from {len(reports)} report(s) and "
        f"{len(overrides)} override(s): **{len(cases)} case(s)**.\n\n"
        + "\n".join(f"* {k}: {v}" for k, v in manifest["by_category"].items())
        + "\n\n> " + manifest["statement"] + "\n\n"
        + "\n".join(manifest["how_to_use"]) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    print(f"\nwrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
