"""Multimodal fusion: combine vision and acoustic evidence honestly.

Implements the shared interface from the project spec. Rules:

- A non-onion image short-circuits everything (final label "not_onion").
- Acoustic evidence is fused ONLY when `acoustic_grading_eligible()` is true —
  i.e. the recording passed its gates **and** the model carries verified onion
  ground truth. A synthetic/demo or research-only model yields status
  "vision_only_acoustic_not_validated", never a fused number.
- Invalid/absent acoustic evidence NEVER produces a confident fused number:
  the result falls back to vision-only with status
  "vision_only_audio_unreliable".
- Disagreement between visible condition and acoustic defect probability
  yields "needs_manual_review" with the reason attached — a low-confidence
  acoustic reading can never silently upgrade or downgrade an onion.
- Every output carries confidence and the reasons behind it.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.common.config import get_setting
from src.common.contracts import acoustic_grading_eligible

ACOUSTIC_WEIGHT = 0.35
VISION_WEIGHT = 0.65
DISAGREEMENT_GAP = 0.45
UNCERTAIN_LABELS = {"uncertain"}


def _vision_defect_score(vision: Dict[str, Any]) -> Optional[float]:
    """Vision "defect pressure" in [0, 1], or None when not derivable.

    The attribute model does **not** emit a freshness score (no longitudinal
    labels exist), so fusion uses the max of the modelled defect/quality
    probabilities instead of inventing a number.
    """
    defects = vision.get("defects") or {}
    probs = [float(d.get("confidence", 0.0)) for d in defects.values()
             if isinstance(d, dict)]
    if not probs:
        return None
    return max(probs)


def fuse_results(vision_result: Dict[str, Any],
                 acoustic_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Fuse the vision contract with the acoustic contract.

    vision_result: output of inference/vision_inference.py::classify_vision
    acoustic_result: output of inference/acoustic_inference.py::classify_acoustic
    """
    warnings: list[str] = list(vision_result.get("warnings", []))

    acoustic_eligible = acoustic_grading_eligible(acoustic_result)

    if not vision_result.get("is_onion", False):
        return {
            "is_onion": False,
            "final": {"label": "not_onion", "freshness_score": None,
 "shelf_life_status": "not_trained",
 "estimated_days_remaining": None,
                      "reason": "no onion detected in the image"},
            "acoustic_eligible": acoustic_eligible,
            "warnings": warnings,
        }

    vision = vision_result["vision"]
    v_conf = float(vision.get("confidence", 0.0))
    v_label = vision.get("label", "uncertain")

    # ---- Vision-only path -------------------------------------------------
    if not acoustic_eligible:
        if not acoustic_result:
            status = "vision_only"
            acoustic_reason = "acoustic evidence absent"
        elif str(acoustic_result.get("status")) != "valid":
            status = "vision_only_audio_unreliable"
            acoustic_reason = f"acoustic status '{acoustic_result.get('status')}'"
            warnings.append(
                f"acoustic status was '{acoustic_result.get('status')}'; "
                "falling back to vision-only result")
        else:
            # Recording was fine, but the model is not validated (synthetic /
            # research-only). It is reported, never fused.
            status = "vision_only_acoustic_not_validated"
            acoustic_reason = ("acoustic model has no verified onion ground "
                               "truth; not used for grading")
            warnings.append(
                "acoustic evidence is research-only (dataset_type="
                f"{acoustic_result.get('dataset_type') or 'unknown'}); it "
                "cannot change the grading result")
        # freshness_score is only produced when a model actually emits one.
        raw_freshness = vision.get("freshness_score")
        final_score = (round(float(raw_freshness), 3)
                       if raw_freshness is not None
                       and v_label not in UNCERTAIN_LABELS else None)
        return {
            "is_onion": True,
            "vision": vision,
            "acoustic": acoustic_result or None,
            "acoustic_eligible": False,
            "final": {
                "label": "needs_manual_review" if v_label in UNCERTAIN_LABELS else v_label,
                "freshness_score": final_score,
                "shelf_life_status": "not_trained",
                "estimated_days_remaining": None,
                "reason": ("vision below confidence threshold"
                           if v_label in UNCERTAIN_LABELS
                           else f"vision-only result; {acoustic_reason}"),
                "vision_confidence": v_conf,
            },
            "status": status,
            "warnings": warnings,
        }

    # ---- Fusion path ------------------------------------------------------
    prob = float(acoustic_result["internal_defect_probability"])
    a_conf = float(acoustic_result["confidence"])
    vision_defect_score = _vision_defect_score(vision)

    # A fused freshness score is emitted ONLY when both sources provide a
    # comparable quantity. Vision has no freshness output, so the fused score
    # is None unless the caller supplies a real vision freshness score.
    raw_freshness = vision.get("freshness_score")
    fused_score: Optional[float] = None
    if raw_freshness is not None and vision_defect_score is not None:
        fused_score = round(max(0.0, min(1.0,
                                       VISION_WEIGHT * float(raw_freshness)
                                       - ACOUSTIC_WEIGHT * prob)), 3)

    label = "sound"
    reason = "vision and acoustic evidence agree the onion is sound"
    if v_label in {"damaged", "sprouted", "undersized", "visibly_rotten"}:
        label = v_label
        reason = f"vision detected {v_label}; acoustic concordance checked"
    elif prob >= 0.6:
        label = "needs_manual_review"
        reason = "acoustic evidence indicates possible internal defect"

    # Disagreement: vision says sound but acoustic strongly disagrees (or vice versa).
    disagreement = (v_label == "sound" and prob >= 0.6) or \
                   (v_label in {"visibly_rotten", "damaged"} and prob <= 0.15)
    if disagreement and min(v_conf, a_conf) >= 0.5:
        return {
            "is_onion": True,
            "vision": vision,
            "acoustic": acoustic_result,
            "acoustic_eligible": True,
            "final": {
                "label": "needs_manual_review",
                "freshness_score": None,
                "shelf_life_status": "not_trained",
                "estimated_days_remaining": None,
                "reason": "multimodal disagreement",
                "vision_confidence": v_conf,
                "acoustic_confidence": a_conf,
            },
            "status": "manual_review",
            "warnings": warnings + [
                "visual and acoustic evidence disagree; manual review required"],
        }

    # Low-confidence acoustic evidence is surfaced, never silently applied.
    if a_conf < float(get_setting("acoustic_confidence_threshold", 0.55)):
        warnings.append(
            f"acoustic confidence {a_conf} is low; result weighted toward vision")

    if fused_score is None:
        warnings.append(
            "freshness_score is null: no vision freshness model exists, so no "
            "combined score is synthesised. Attribute probabilities and the "
            "defect confidence are reported instead.")

    return {
        "is_onion": True,
        "vision": vision,
        "acoustic": acoustic_result,
        "acoustic_eligible": True,
        "final": {
            "label": label,
            "freshness_score": fused_score,
            "shelf_life_status": "not_trained",
            "estimated_days_remaining": None,
            "visible_defect_score": (round(vision_defect_score, 4)
                                     if vision_defect_score is not None else None),
            "reason": reason,
            "vision_confidence": v_conf,
            "acoustic_confidence": a_conf,
        },
        "status": "fused",
        "warnings": warnings,
    }
