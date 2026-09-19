"""Inspection report generation.

Produces a professional batch report containing the model versions and policy
version used, the per-onion evidence, and a tamper-evident integrity block.
A farmer-facing plain-language view is generated from the same data.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.common import reasons as R
from src.reporting.audit_hash import attach_integrity
from src.reporting.qr import QrPayload

REPORT_VERSION = "1.0.0"


def new_report_id(center_id: str, when: Optional[datetime] = None) -> str:
    when = when or datetime.now(timezone.utc)
    return f"REPORT-{center_id}-{when.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"


def build_report(batch: Dict[str, Any],
                 onion_results: List[Dict[str, Any]],
                 evidence: Optional[List[Dict[str, Any]]] = None,
                 report_id: Optional[str] = None,
                 app_version: Optional[str] = None,
                 demo_mode: bool = True,
                 identity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Assemble the full report document (without integrity block).

    ``identity`` records the exact code/models/policy that produced the report
    (Phase AK). It defaults to the live version identity, which reads git and
    ``models/registry.json`` — nothing is asserted about versions that the
    repository cannot substantiate.
    """
    report_id = report_id or new_report_id(batch["center_id"])
    policy = batch.get("policy", {})
    if identity is None:
        from src.common.version import APP_VERSION, runtime_versions
        identity = runtime_versions()
    else:
        from src.common.version import APP_VERSION
    if app_version is None:
        app_version = identity.get("app_version") or APP_VERSION
    report = {
        "report_version": REPORT_VERSION,
        "report_id": report_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "demo_mode": demo_mode,
        "header": {
            "system": "ONION-Q",
            "center_id": batch["center_id"],
            "batch_id": batch["batch_id"],
            "lot_id": batch.get("lot_id"),
            "inspector_id": batch["inspector_id"],
            "app_version": app_version,
            "model_versions": batch.get("model_versions", {}),
            "policy_id": policy.get("policy_id"),
            "policy_version": policy.get("version"),
            "policy_hash": policy.get("policy_hash"),
            "policy_verified": policy.get("source_verified"),
            "policy_display_label": policy.get("display_label"),
            "identity": identity,
        },
        "summary": {
            "totals": batch.get("totals", {}),
            "counts": batch.get("counts", {}),
            "percentages": batch.get("percentages", {}),
            "mean_confidence": batch.get("mean_confidence"),
            "denominator_note": batch.get("denominator_note", ""),
        },
        "defect_summary": _defect_summary(batch, onion_results),
        "evidence": evidence or [],
        "onion_results": onion_results,
        "notes": batch.get("notes", ""),
    }
    report["farmer_view"] = farmer_view(report)
    return report


def _defect_summary(batch: Dict[str, Any],
                    onion_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    histogram = batch.get("reason_histogram", {})
    return {
        "reason_codes": histogram,
        "reason_text": {code: R.describe(code) for code in histogram},
        "low_confidence_count": sum(
            1 for r in onion_results
            if R.LOW_MODEL_CONFIDENCE in (r.get("reason_codes") or [])),
        "internal_risk_flagged": sum(
            1 for r in onion_results
            if R.INTERNAL_DEFECT_RISK in (r.get("reason_codes") or [])),
    }


def farmer_view(report: Dict[str, Any]) -> Dict[str, Any]:
    """Plain-language view: no model jargon, no probabilities as absolutes."""
    counts = report["summary"]["counts"]
    totals = report["summary"]["totals"]
    histogram = report["defect_summary"]["reason_codes"]
    main_reasons = [
        {"reason": R.describe(code), "count": n}
        for code, n in list(histogram.items())[:6]
        if code not in {"MEETS_POLICY", "POLICY_UNVERIFIED"}
    ]
    return {
        "lot": report["header"].get("lot_id") or report["header"]["batch_id"],
        "total_inspected": totals.get("total_detected", 0),
        "accepted": counts.get("grade_a", 0),
        "accepted_relaxed": counts.get("relaxed", 0),
        "rejected": counts.get("reject", 0),
        "needs_review": counts.get("manual_review", 0),
        "main_reasons": main_reasons,
        "policy_note": (
            "Decisions follow the procurement policy in force at inspection "
            f"time ({report['header'].get('policy_id')}). Grading rules can "
            "change without re-inspecting the produce."),
    }


def finalize(report: Dict[str, Any]) -> Dict[str, Any]:
    """Attach the integrity block and derive the QR payload."""
    finalized = attach_integrity(report)
    payload = QrPayload(report_id=finalized["report_id"],
                        report_hash=finalized["integrity"]["canonical_hash"])
    finalized["qr_payload"] = payload.encode()
    return finalized


def write_report(report: Dict[str, Any], out_dir: str | Path,
                 write_farmer_markdown: bool = True) -> Dict[str, str]:
    """Write report JSON (+ optional farmer markdown). Returns written paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / f"{report['report_id']}.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    written = {"json": str(json_path)}

    if write_farmer_markdown:
        fv = report["farmer_view"]
        lines = [
            f"# Inspection summary — Lot {fv['lot']}",
            "",
            f"- Total inspected: **{fv['total_inspected']}**",
            f"- Accepted: **{fv['accepted']}**",
            f"- Accepted under relaxed rules: **{fv['accepted_relaxed']}**",
            f"- Rejected: **{fv['rejected']}**",
            f"- Needs manual review: **{fv['needs_review']}**",
            "",
            "## Main reasons",
        ]
        if fv["main_reasons"]:
            lines += [f"- {r['reason']} ({r['count']})" for r in fv["main_reasons"]]
        else:
            lines.append("- No rejection reasons recorded.")
        lines += ["", f"_{fv['policy_note']}_", ""]
        md_path = out / f"{report['report_id']}_farmer.md"
        md_path.write_text("\n".join(lines), encoding="utf-8")
        written["farmer_markdown"] = str(md_path)
    return written
