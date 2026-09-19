"""MODE A — Quick Batch Scan.

Tray image(s) → onion instances → per-onion visible attributes + size →
policy engine → per-onion decisions → batch aggregation.

Design rules that keep this honest:

* Every per-onion number comes from a real model call or a real measurement.
  When a model artifact is missing the pipeline returns `model_unavailable` and
  grades nothing.
* An onion whose capture quality is unusable is never graded: it is reported as
  `manual_review` with the capture issue attached.
* No acoustic work happens in this mode (throughput requirement), so
  `internal_defect_probability` stays `None` and the report says so.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.common import reasons as R                      # noqa: E402
from src.grading.batch import OnionResult, aggregate     # noqa: E402
from src.grading.engine import Decision, Measurements, decide  # noqa: E402
from src.grading.policy import Policy                    # noqa: E402


def _measurement_payload(m: "Measurements", **extra: Any) -> Dict[str, Any]:
    """The same measurement block the engine emits, for non-engine decisions.

    Kept field-for-field identical to `Decision.measurements` so a report can
    never mix two different shapes (a reviewer must see the same keys whatever
    path produced the decision).
    """
    payload: Dict[str, Any] = {
        "diameter_mm": m.diameter_mm,
        "size_method": m.size_method,
        "rot_detected": m.rot_detected,
        "rot_confidence": m.rot_confidence,
        "sprout_detected": m.sprout_detected,
        "sprout_confidence": m.sprout_confidence,
        "damage_surface_pct": m.damage_surface_pct,
        "internal_defect_probability": m.internal_defect_probability,
        "internal_evidence_valid": m.internal_evidence_valid,
        "model_confidence": m.model_confidence,
        "occlusion_fraction": m.occlusion_fraction,
    }
    payload.update(extra)
    return payload


def _manual_review_decision(policy: Policy, code: str,
                            measurements: Dict[str, Any]) -> Decision:
    return Decision(decision="manual_review", reason_codes=[code],
                    policy_id=policy.policy_id, policy_version=policy.version,
                    policy_hash=policy.policy_hash,
                    policy_verified=policy.source_verified,
                    measurements=measurements)


def scan_image(image_path: str, policy: Policy,
               detector_model: Optional[str] = None,
               attribute_model: Optional[str] = None,
               require_calibration: bool = True,
               crop_padding: float = 0.08,
               progress: bool = False) -> Dict[str, Any]:
    """Run the full Quick Batch Scan pipeline on one tray image."""
    from PIL import Image

    from inference.vision_inference import (classify_pil_image,
                                            resolve_artifact)
    from src.vision.capture_quality import evaluate_capture
    from src.vision.detector import detect_onions
    from src.vision.size import detect_markers, measure_size

    detection = detect_onions(image_path, model_path=detector_model)
    warnings: List[str] = list(detection.get("warnings", []))
    instances = detection.get("instances", []) if detection["status"] == "success" \
        else []

    if detection["status"] != "success":
        return {
            "image": str(image_path),
            "status": "model_unavailable",
            "detector": detection,
            "capture_quality": None,
            "onions": [],
            "warnings": warnings,
        }

    try:
        import cv2
        bgr = cv2.imread(str(image_path))
        markers = detect_markers(bgr) if bgr is not None else []
    except Exception:  # pragma: no cover - opencv optional
        markers = []

    quality = evaluate_capture(image_path, instances=instances,
                               image_size=detection.get("image_size"),
                               markers_detected=len(markers),
                               require_calibration=require_calibration)

    attribute_artifact = resolve_artifact(attribute_model)
    if attribute_artifact is None:
        warnings.append("No attribute model artifact: onions are detected but "
                        "not graded.")

    img = Image.open(image_path).convert("RGB")
    iw, ih = img.size
    onions: List[Dict[str, Any]] = []

    for idx, inst in enumerate(instances):
        onion_id = f"ONION_SCAN_{idx + 1:04d}"
        x, y, w, h = inst["bbox_xywh"]
        pad_x, pad_y = w * crop_padding, h * crop_padding
        box = (max(0, int(x - pad_x)), max(0, int(y - pad_y)),
               min(iw, int(x + w + pad_x)), min(ih, int(y + h + pad_y)))
        crop = img.crop(box) if box[2] > box[0] and box[3] > box[1] else img

        vision = classify_pil_image(crop, model_path=attribute_model,
                                    detector_instances=[inst],
                                    artifact=attribute_artifact)
        size = measure_size(image_path, inst["bbox_xywh"])

        visible = vision.get("vision", {})
        defects = visible.get("defects") or {}
        measurements = Measurements(
            diameter_mm=size.get("diameter_mm"),
            size_method=size.get("size_method", "unknown"),
            rot_detected=(defects.get("rotten") or {}).get("detected"),
            rot_confidence=(defects.get("rotten") or {}).get("confidence"),
            sprout_detected=(defects.get("sprout") or {}).get("detected"),
            sprout_confidence=(defects.get("sprout") or {}).get("confidence"),
            damage_surface_pct=None,          # not measurable without masks
            internal_defect_probability=None,  # not measured in batch mode
            internal_evidence_valid=False,
            model_confidence=visible.get("confidence"),
            occlusion_fraction=None,
        )

        if vision.get("status") == "model_unavailable":
            decision = _manual_review_decision(
                policy, R.MODEL_UNAVAILABLE,
                _measurement_payload(
                    measurements,
                    size_method="unknown",   # nothing was classified
                    model_confidence=None))
        elif quality.status == "reject":
            # Unusable capture: grade nothing, escalate with the reason.
            code = (quality.issues[0] if quality.issues else R.OCCLUSION_HIGH)
            decision = _manual_review_decision(
                policy, code,
                _measurement_payload(
                    measurements,
                    model_confidence=None,
                    capture_issues=quality.issues))
        else:
            decision = decide(measurements, policy)

        onions.append({
            "onion_id": onion_id,
            "instance": inst,
            "vision": visible,
            "vision_status": vision.get("status"),
            "size": size,
            "measurements": decision.measurements,
            "decision": decision.to_dict(),
            "crop_box": list(box),
            "warnings": vision.get("warnings", []) + size.get("warnings", []),
        })
        if progress:
            print(f"  {onion_id}: {decision.decision} "
                  f"({', '.join(decision.reason_codes)})")

    return {
        "image": str(image_path),
        "status": "success",
        "detector": detection,
        "capture_quality": quality.to_dict(),
        "markers_detected": len(markers),
        "onions": onions,
        "warnings": warnings,
    }


def scan_batch(image_paths: Sequence[str], policy: Policy,
               center_id: str = "MH-NSK", inspector_id: str = "INSP-001",
               batch_id: Optional[str] = None, lot_id: Optional[str] = None,
               **kwargs: Any) -> Dict[str, Any]:
    """Scan one or more tray images and aggregate the batch report."""
    from src.grading.batch import batch_id_for
    from src.vision.detector import MODEL_ID as DETECTOR_ID
    from inference.vision_inference import MODEL_ID as ATTR_ID

    batch_id = batch_id or batch_id_for(center_id)
    all_onions: List[Dict[str, Any]] = []
    per_image: List[Dict[str, Any]] = []
    results_for_aggregate: List[OnionResult] = []
    warnings: List[str] = []

    for path in image_paths:
        scanned = scan_image(path, policy, **kwargs)
        per_image.append({k: v for k, v in scanned.items() if k != "onions"})
        warnings.extend(scanned.get("warnings", []))
        for onion in scanned.get("onions", []):
            onion["source_image"] = str(path)
            all_onions.append(onion)
            results_for_aggregate.append(OnionResult(
                onion_id=onion["onion_id"],
                decision=_decision_from_dict(onion["decision"]),
                is_onion=onion.get("decision", {}).get("decision") != "not_onion",
                confidence=(onion.get("measurements") or {}).get("model_confidence"),
            ))

    summary = aggregate(batch_id=batch_id, center_id=center_id,
                        inspector_id=inspector_id,
                        results=results_for_aggregate,
                        policy_summary=policy.summary(),
                        model_versions={"detector": DETECTOR_ID,
                                        "attributes": ATTR_ID,
                                        "acoustic": "not_used_in_batch_mode"},
                        lot_id=lot_id)

    return {
        "batch": summary,
        "images": per_image,
        "onions": all_onions,
        "policy": policy.summary(),
        "mode": "quick_batch_scan",
        "warnings": warnings,
        "notes": (
            "Measured attributes drive the decision; the neural network never "
            "decides the grade. Acoustic analysis is not part of Quick Batch "
            "Scan — suspicious onions should be examined with Deep Scan."),
    }


def _decision_from_dict(payload: Dict[str, Any]) -> Decision:
    return Decision(decision=payload["decision"],
                    reason_codes=payload.get("reason_codes", []),
                    policy_id=payload.get("policy_id", ""),
                    policy_version=payload.get("policy_version", ""),
                    policy_hash=payload.get("policy_hash", ""),
                    policy_verified=bool(payload.get("policy_verified")),
                    measurements=payload.get("measurements", {}))
