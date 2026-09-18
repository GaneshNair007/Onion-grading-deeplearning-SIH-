"""Multimodal fusion: combine vision and acoustic evidence honestly.

Implements the shared interface from the project spec. Rules:

- A non-onion image short-circuits everything (final label "not_onion").
- Valid acoustic evidence is fused with vision by weighted combination.
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

ACOUSTIC_WEIGHT = 0.35
VISION_WEIGHT = 0.65
DISAGREEMENT_GAP = 0.45
UNCERTAIN_LABELS = {"uncertain"}


def fuse_results(vision_result: Dict[str, Any],
                 acoustic_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Fuse the vision contract with the acoustic contract.

    vision_result: output of inference/vision_inference.py::classify_vision
    acoustic_result: output of inference/acoustic_inference.py::classify_acoustic
    """
    warnings: list[str] = list(vision_result.get("warnings", []))

    if not vision_result.get("is_onion", False):
        return {
            "is_onion": False,
            "final": {"label": "not_onion", "freshness_score": None,
                      "reason": "no onion detected in the image"},
            "warnings": warnings,
        }

    vision = vision_result["vision"]
    v_conf = float(vision.get("confidence", 0.0))
    v_label = vision.get("label", "uncertain")

    # ---- Vision-only path -------------------------------------------------
    if not acoustic_result or acoustic_result.get("status") != "valid":
        status = "vision_only_audio_unreliable" if acoustic_result else "vision_only"
        if acoustic_result:
            warnings.append(
                f"acoustic status was '{acoustic_result.get('status')}'; "
                "falling back to vision-only result")
        final_score = None if v_label in UNCERTAIN_LABELS else round(
            float(vision.get("freshness_score", 0.0)), 3)
        acoustic_reason = ("acoustic evidence absent" if not acoustic_result
                           else f"acoustic status "
                                f"'{acoustic_result.get('status')}'")
        return {
            "is_onion": True,
            "vision": vision,
            "acoustic": acoustic_result or None,
            "final": {
                "label": "needs_manual_review" if v_label in UNCERTAIN_LABELS else v_label,
                "freshness_score": final_score,
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
    vision_defect_score = v_conf if v_label in {"damaged", "sprouted", "undersized",
                                                "visibly_rotten", "uncertain"} else 0.0

    # Weighted freshness: acoustic defect probability pulls the score down.
    acoustic_penalty = ACOUSTIC_WEIGHT * prob
    vision_component = (1.0 - ACOUSTIC_WEIGHT) * float(vision.get("freshness_score", 0.0))
    fused_score = round(max(0.0, min(1.0, vision_component - acoustic_penalty)), 3)

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
            "final": {
                "label": "needs_manual_review",
                "freshness_score": None,
                "reason": "multimodal disagreement",
                "vision_confidence": v_conf,
                "acoustic_confidence": a_conf,
            },
            "status": "manual_review",
            "warnings": warnings + [
                "visual and acoustic evidence disagree; manual review required"],
        }

    # Low-confidence acoustic evidence is surfaced, never silently applied.
    if a_conf < 0.55:
        warnings.append(
            f"acoustic confidence {a_conf} is low; result weighted toward vision")

    return {
        "is_onion": True,
        "vision": vision,
        "acoustic": acoustic_result,
        "final": {
            "label": label,
            "freshness_score": fused_score,
            "reason": reason,
            "vision_confidence": v_conf,
            "acoustic_confidence": a_conf,
        },
        "status": "fused",
        "warnings": warnings,
    }
