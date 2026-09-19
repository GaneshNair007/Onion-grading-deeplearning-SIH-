"""Batch aggregation.

Percentage rules are explicit and reported: every onion contributes to
`total_detected`, and all percentages use **total_detected** as the
denominator. Manual-review onions are never silently excluded from the
percentages — they are a visible class of their own, which is the honest way
to present an inspection where some onions could not be graded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.grading.engine import Decision

DECISION_CLASSES = ("grade_a", "relaxed", "reject", "manual_review")


@dataclass
class OnionResult:
    onion_id: str
    decision: Optional[Decision] = None
    is_onion: Optional[bool] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def _pct(count: int, total: int) -> float:
    return round(100.0 * count / total, 2) if total else 0.0


def aggregate(batch_id: str, center_id: str, inspector_id: str,
              results: List[OnionResult],
              policy_summary: Dict[str, Any],
              model_versions: Dict[str, str],
              created_at: Optional[str] = None,
              lot_id: Optional[str] = None,
              notes: Optional[str] = None) -> Dict[str, Any]:
    """Build the batch summary document (the report's core payload)."""
    total = len(results)
    counts = {name: 0 for name in DECISION_CLASSES}
    non_onion = 0
    ungraded = 0
    reason_histogram: Dict[str, int] = {}
    confidences: List[float] = []

    for r in results:
        if r.is_onion is False:
            non_onion += 1
            continue
        if r.decision is None:
            ungraded += 1
            continue
        counts[r.decision.decision] = counts.get(r.decision.decision, 0) + 1
        for code in r.decision.reason_codes:
            reason_histogram[code] = reason_histogram.get(code, 0) + 1
        if r.confidence is not None:
            confidences.append(float(r.confidence))

    graded = sum(counts.values())
    return {
        "batch_id": batch_id,
        "center_id": center_id,
        "inspector_id": inspector_id,
        "lot_id": lot_id,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "policy": policy_summary,
        "model_versions": model_versions,
        "totals": {
            "total_detected": total,
            "graded": graded,
            "non_onion_rejected": non_onion,
            "ungraded_errors": ungraded,
            "manual_review": counts["manual_review"],
        },
        "counts": counts,
        "percentages": {
            name: _pct(counts[name], total) for name in DECISION_CLASSES
        },
        "denominator_note": (
            "All percentages use total_detected as the denominator; "
            "manual_review onions are reported explicitly and are never "
            "silently excluded."),
        "mean_confidence": (round(sum(confidences) / len(confidences), 4)
                            if confidences else None),
        "reason_histogram": dict(sorted(reason_histogram.items(),
                                        key=lambda kv: (-kv[1], kv[0]))),
        "notes": notes or "",
    }


def batch_id_for(center_id: str, when: Optional[datetime] = None,
                 seq: int = 1) -> str:
    """Deterministic-looking batch identifier: CENTER-YYYYMMDD-NNNN.

    Not a security token — uniqueness is the caller's responsibility (the
    mobile app generated a UUID and keeps `client_generated_uuid` separate).
    """
    when = when or datetime.now(timezone.utc)
    return f"{center_id}-{when.strftime('%Y%m%d')}-{seq:04d}"
