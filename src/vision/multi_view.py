"""Multi-angle Deep Scan: guided views + conservative per-view fusion.

The inspector captures four guided views of one onion:

    VIEW 1  neck / top
    VIEW 2  root / base
    VIEW 3  side A
    VIEW 4  side B

Fusion rules (deliberately conservative, documented in docs/ARCHITECTURE.md):

* **Existence of a defect** is decided by `any` view above threshold — one
  clear view of rot is evidence; three clean views do not disprove it.
* **Severity** uses the maximum observed probability, never the mean, because
  averaging hides the worst region and manufactures false confidence.
* Masks/surface-area estimates are NOT summed across views: the views overlap
  and the geometry is unknown, so per-view areas are reported separately and
  aggregation is explicitly marked unavailable.
* Coverage is reported. A partial capture cannot claim a complete inspection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

GUIDED_VIEWS = ["neck", "base", "side_a", "side_b"]
REQUIRED_VIEWS = ["side_a", "side_b"]     # minimum for a "complete" claim
DEFECT_THRESHOLD = 0.5


@dataclass
class ViewResult:
    view: str
    label: str
    confidence: float
    defects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    is_onion: Optional[bool] = None
    warnings: List[str] = field(default_factory=list)


def view_instructions() -> List[Dict[str, str]]:
    """Human guidance for the app's guided-capture UI."""
    return [
        {"view": "neck", "prompt": "Point the camera at the top (neck) of the onion.",
         "action": "Keep the onion on the tray; do not rotate it yet."},
        {"view": "base", "prompt": "Turn the onion over and show the root (base).",
         "action": "Rotate 180 degrees so the root faces the camera."},
        {"view": "side_a", "prompt": "Show side A of the onion.",
         "action": "Rotate a quarter turn from the base view."},
        {"view": "side_b", "prompt": "Show side B of the onion.",
         "action": "Rotate another quarter turn; this is the last required view."},
    ]


def fuse_views(views: List[ViewResult]) -> Dict[str, Any]:
    """Combine per-view attribute results into one Deep Scan verdict."""
    captured = [v.view for v in views]
    missing = [v for v in GUIDED_VIEWS if v not in captured]
    complete = all(v in captured for v in REQUIRED_VIEWS)

    usable = [v for v in views if v.is_onion is not False]
    if not usable:
        return {
            "views_captured": captured,
            "views_missing": missing,
            "coverage_status": "incomplete",
            "is_onion": False,
            "visible_defects": {},
            "multi_view_confidence": 0.0,
            "status": "not_onion",
            "warnings": ["no view contained a detectable onion"],
        }

    names = sorted({n for v in usable for n in v.defects})
    visible_defects: Dict[str, Any] = {}
    for name in names:
        per_view = {}
        detected = False
        max_conf = 0.0
        for v in usable:
            d = v.defects.get(name)
            if not d:
                continue
            conf = float(d.get("confidence", 0.0))
            per_view[v.view] = round(conf, 4)
            max_conf = max(max_conf, conf)
            if d.get("detected"):
                detected = True
        visible_defects[name] = {
            "detected": detected,
            "max_confidence": round(max_conf, 4),
            "per_view_confidence": per_view,
            "views_positive": sum(1 for c in per_view.values()
                                  if c >= DEFECT_THRESHOLD),
        }

    confidences = [float(v.confidence) for v in usable]
    multi_view_confidence = round(max(confidences), 4) if confidences else 0.0

    disagreement = any(v.label != usable[0].label for v in usable[1:])
    warnings: List[str] = []
    if not complete:
        warnings.append(
            f"Guided capture incomplete (missing: {', '.join(missing) or 'none'}) "
            "— this is not a full inspection.")
    if disagreement:
        warnings.append("Views disagree on the visible condition; the most "
                        "severe observation is retained.")
    warnings.append("Defect surface-area percentages are not aggregated across "
                    "views: the views overlap, so summing them would inflate "
                    "the measurement.")

    return {
        "views_captured": captured,
        "views_missing": missing,
        "coverage_status": "complete" if complete else "incomplete",
        "views_used": len(usable),
        "is_onion": True,
        "visible_defects": visible_defects,
        "per_view": [
            {"view": v.view, "label": v.label, "confidence": round(v.confidence, 4)}
            for v in usable
        ],
        "label": _most_severe([v.label for v in usable]),
        "multi_view_confidence": multi_view_confidence,
        "view_disagreement": disagreement,
        "status": "success",
        "warnings": warnings,
    }


_SEVERITY_ORDER = ["visibly_rotten", "reject_grade", "sprouted", "uncertain",
                   "sound"]


def _most_severe(labels: List[str]) -> str:
    """Worst visible condition across views (never the average/majority)."""
    for candidate in _SEVERITY_ORDER:
        if candidate in labels:
            return candidate
    return labels[0] if labels else "uncertain"


def to_measurements(fused: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a fused multi-view result into grading-engine inputs."""
    defects = fused.get("visible_defects", {})
    rot = defects.get("rotten")
    sprout = defects.get("sprout")
    return {
        "rot_detected": bool(rot["detected"]) if rot else None,
        "rot_confidence": rot["max_confidence"] if rot else None,
        "sprout_detected": bool(sprout["detected"]) if sprout else None,
        "sprout_confidence": sprout["max_confidence"] if sprout else None,
        "model_confidence": fused.get("multi_view_confidence"),
        "damage_surface_pct": None,   # not measurable: no masks, overlapping views
    }
