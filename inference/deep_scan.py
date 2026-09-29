"""MODE B — Deep Scan (the differentiator).

One onion, multiple guided views, optional phone acoustic measurement.

Pipeline:

    guided views → per-view attributes → conservative multi-view fusion
                                              │
    phone recording → quality gates → features → acoustic model
                                              │
                                     confidence-aware fusion
                                              │
                                measurements → policy engine → decision

The acoustic branch is allowed to influence the outcome **only** when the
recording passes every quality gate and the model carries real onion ground
truth. Today it does not (synthetic demo model only), so the decision is
recorded with `ACOUSTIC_NOT_VALIDATED` and the acoustic output is reported as
supporting information rather than as a grade input. No grade is ever changed
silently by poor-quality audio.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.common import reasons as R                               # noqa: E402
from src.grading.engine import Measurements, decide               # noqa: E402
from src.grading.policy import Policy                             # noqa: E402
from src.vision.multi_view import (GUIDED_VIEWS, ViewResult,      # noqa: E402
                                   fuse_views, to_measurements,
                                   view_instructions)


def scan_onion(views: Dict[str, str], policy: Policy,
               audio_path: Optional[str] = None,
               acoustic_model: Optional[str] = None,
               detector_model: Optional[str] = None,
               attribute_model: Optional[str] = None,
               marker_size_mm: Optional[float] = None,
               progress: bool = False) -> Dict[str, Any]:
    """Deep Scan one onion from guided views (+ optional acoustic recording)."""
    from PIL import Image

    from inference.vision_inference import classify_pil_image, resolve_artifact
    from src.vision.detector import detect_onions
    from src.vision.size import DEFAULT_MARKER_SIZE_MM, measure_size

    unknown = [v for v in views if v not in GUIDED_VIEWS]
    if unknown:
        return {"status": "invalid_input",
                "error": f"unknown view name(s): {unknown}",
                "allowed_views": GUIDED_VIEWS,
                "instructions": view_instructions()}

    attribute_artifact = resolve_artifact(attribute_model)
    view_results: List[ViewResult] = []
    geometry: Dict[str, Any] = {}

    for view_name, path in views.items():
        if not Path(path).exists():
            return {"status": "invalid_input",
                    "error": f"view '{view_name}' image not found: {path}"}

        detection = detect_onions(path, model_path=detector_model)
        instances = detection.get("instances", []) if detection["status"] == "success" else None

        img = Image.open(path).convert("RGB")
        crop = img
        if instances:
            # Deep Scan is single-onion: use the highest-confidence instance.
            best = max(instances, key=lambda i: i.get("confidence", 0.0))
            x, y, w, h = best["bbox_xywh"]
            iw, ih = img.size
            box = (max(0, int(x - w * 0.08)), max(0, int(y - h * 0.08)),
                   min(iw, int(x + w * 1.08)), min(ih, int(y + h * 1.08)))
            if box[2] > box[0] and box[3] > box[1]:
                crop = img.crop(box)
            size = measure_size(path, best["bbox_xywh"],
                                marker_size_mm or DEFAULT_MARKER_SIZE_MM)
            geometry[view_name] = size
        else:
            geometry[view_name] = {
                "size_method": "unknown", "diameter_mm": None,
                "warnings": [] if detection["status"] == "success" else
                            detection.get("warnings", []),
            }

        result = classify_pil_image(crop, model_path=attribute_model,
                                    detector_instances=instances,
                                    artifact=attribute_artifact)
        visible = result.get("vision", {})
        view_results.append(ViewResult(
            view=view_name,
            label=visible.get("label", "unavailable"),
            confidence=float(visible.get("confidence") or 0.0),
            defects=visible.get("defects") or {},
            is_onion=result.get("is_onion"),
            warnings=list(result.get("warnings", [])),
        ))
        if progress:
            print(f"  view {view_name}: {visible.get('label')} "
                  f"(conf {visible.get('confidence')})")

    fused = fuse_views(view_results)

    # --- acoustic branch ---------------------------------------------------
    acoustic: Optional[Dict[str, Any]] = None
    if audio_path:
        from inference.acoustic_inference import classify_acoustic
        acoustic = classify_acoustic(audio_path, model_path=acoustic_model)

    fusion = None
    if acoustic is not None and fused.get("is_onion"):
        from src.fusion.fusion import fuse_results
        vision_contract = {
            "is_onion": True,
            "vision": {
                "label": fused.get("label", "uncertain"),
                "confidence": fused.get("multi_view_confidence", 0.0),
                "defects": fused.get("visible_defects", {}),
                "freshness_score": None,
                "model_version": "vision-attributes-v0.1 (multi-view)",
            },
            "warnings": list(fused.get("warnings", [])),
        }
        fusion = fuse_results(vision_contract, acoustic)

    measurements_payload = to_measurements(fused)
    best_geometry = _best_geometry(geometry)
    # The flag the grading engine reads is DERIVED from the acoustic artifact's
    # own metadata, not hard-coded: a model whose dataset_type is synthetic (or
    # which does not declare verified onion ground truth) can never move a grade,
    # and a future verified-onion model becomes eligible without a code change.
    internal_evidence_valid = bool(acoustic
                                   and acoustic.get("grading_eligible") is True)
    measurements = Measurements(
        diameter_mm=best_geometry.get("diameter_mm"),
        size_method=best_geometry.get("size_method", "unknown"),
        rot_detected=measurements_payload["rot_detected"],
        rot_confidence=measurements_payload["rot_confidence"],
        sprout_detected=measurements_payload["sprout_detected"],
        sprout_confidence=measurements_payload["sprout_confidence"],
        damage_surface_pct=None,
        internal_defect_probability=(acoustic or {}).get("internal_defect_probability"),
        internal_evidence_valid=internal_evidence_valid,
        model_confidence=measurements_payload["model_confidence"],
        multimodal_disagreement=bool(fusion and fusion.get("status") == "manual_review"),
    )

    if not fused.get("is_onion"):
        decision = None
    else:
        decision = decide(measurements, policy)
        if acoustic and acoustic.get("status") not in (None, "valid"):
            decision.reason_codes.append(R.AUDIO_UNRELIABLE)
        if acoustic and not internal_evidence_valid:
            decision.reason_codes.append(R.ACOUSTIC_NOT_VALIDATED)

    instructions = view_instructions()
    return {
        "status": "success" if fused.get("is_onion") else "not_onion",
        "views": fused,
        "view_instructions": instructions,
        "geometry": geometry,
        "best_geometry": best_geometry,
        "acoustic": acoustic,
        "fusion": fusion,
        "decision": decision.to_dict() if decision else None,
        "policy": policy.summary(),
        "mode": "deep_scan",
        "warnings": (list(fused.get("warnings", []))
                     + ([R.describe(R.ACOUSTIC_NOT_VALIDATED)]
                        if acoustic and not internal_evidence_valid else [])),
        "notes": (
            "Acoustic evidence is recorded and reported but cannot change a "
            "grade until it is validated against cut-open onion ground truth. "
            f"internal_evidence_valid={internal_evidence_valid} was derived from "
            "the acoustic artifact's own dataset_type metadata."),
    }


def _best_geometry(geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer a calibrated measurement; otherwise report uncalibrated."""
    calibrated = [g for g in geometry.values()
                  if g.get("size_method") == "aruco_calibrated"
                  and g.get("diameter_mm") is not None]
    if calibrated:
        # Equivalent-diameter basis: use the largest, and say why.
        best = max(calibrated, key=lambda g: g["diameter_mm"])
        return {**best,
                "basis_note": "largest calibrated equivalent diameter across views"}
    for g in geometry.values():
        if g.get("size_method") == "uncalibrated":
            return g
    return {"size_method": "unknown", "diameter_mm": None,
            "warnings": ["no view produced a usable size measurement"]}
