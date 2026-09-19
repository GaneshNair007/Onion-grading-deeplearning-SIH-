"""Procurement grading engine: measurements + policy → decision.

The engine never invents a measurement. If a policy requires something the
pipeline cannot provide (for example defect surface area, which needs
segmentation masks the current detector does not output), the decision
escalates to manual review with `MEASUREMENT_UNAVAILABLE` rather than
silently passing.

Everything a decision depends on is recorded: policy id, policy hash, and the
machine-readable reason codes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.common import reasons as R
from src.grading.policy import Policy


@dataclass
class Measurements:
    """Everything the vision/acoustic pipeline measured about one onion.

    ``None`` means *not measured* — never substitute 0.0 or a default.
    """

    diameter_mm: Optional[float] = None
    size_method: str = "uncalibrated"          # aruco_calibrated | uncalibrated | unknown
    rot_detected: Optional[bool] = None
    rot_confidence: Optional[float] = None
    sprout_detected: Optional[bool] = None
    sprout_confidence: Optional[float] = None
    damage_surface_pct: Optional[float] = None  # requires masks: currently unavailable
    internal_defect_probability: Optional[float] = None
    internal_evidence_valid: bool = False
    model_confidence: Optional[float] = None
    occlusion_fraction: Optional[float] = None
    multimodal_disagreement: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    decision: str                    # grade_a | relaxed | reject | manual_review
    reason_codes: List[str]
    policy_id: str
    policy_version: str
    policy_hash: str
    policy_verified: bool
    measurements: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "reason_codes": self.reason_codes,
            "reasons_text": R.describe_all(self.reason_codes),
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "policy_verified": self.policy_verified,
            "measurements": self.measurements,
        }


def _unavailable(value: Optional[float]) -> bool:
    return value is None


def decide(m: Measurements, policy: Policy) -> Decision:
    """Apply the policy to one onion's measurements."""
    codes: List[str] = []
    grade_a = policy.grade_named("grade_a")
    relaxed = policy.grade_named("relaxed")
    mr = policy.manual_review or {}
    size_cfg = policy.size or {}

    def finish(decision: str) -> Decision:
        return Decision(
            decision=decision,
            reason_codes=codes,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            policy_hash=policy.policy_hash,
            policy_verified=policy.source_verified,
            measurements={
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
            },
        )

    if not policy.source_verified:
        codes.append(R.POLICY_UNVERIFIED)

    # --- gate 1: model confidence -----------------------------------------
    min_conf = mr.get("min_model_confidence")
    if min_conf is not None and m.model_confidence is not None \
            and m.model_confidence < float(min_conf):
        codes.append(R.LOW_MODEL_CONFIDENCE)
        return finish("manual_review")

    # --- gate 2: capture quality (occlusion) ------------------------------
    max_occ = mr.get("max_occlusion_fraction")
    if max_occ is not None and m.occlusion_fraction is not None \
            and m.occlusion_fraction > float(max_occ):
        codes.append(R.OCCLUSION_HIGH)
        return finish("manual_review")

    # --- gate 3: physical size availability -------------------------------
    needs_size = (grade_a.get("min_diameter_mm") is not None
                  or grade_a.get("max_diameter_mm") is not None)
    if needs_size and size_cfg.get("require_calibration_for_decision", True) \
            and (m.diameter_mm is None or m.size_method != "aruco_calibrated"):
        codes.append(R.CALIBRATION_MISSING)
        if mr.get("on_missing_calibration", True):
            return finish("manual_review")

    # --- gate 4: multimodal disagreement ----------------------------------
    if m.multimodal_disagreement and mr.get("on_multimodal_disagreement", True):
        codes.append(R.MULTIMODAL_DISAGREEMENT)
        return finish("manual_review")

    # --- hard visible defects --------------------------------------------
    if m.rot_detected is True and grade_a.get("allow_visible_rot") is False:
        codes.append(R.VISIBLE_ROT)
        return finish("reject")
    if m.sprout_detected is True and grade_a.get("allow_sprouting") is False:
        codes.append(R.SPROUT_DETECTED)
        return finish("reject")

    # --- surface damage ---------------------------------------------------
    max_damage = grade_a.get("max_surface_damage_pct")
    if max_damage is not None:
        if _unavailable(m.damage_surface_pct):
            codes.append(R.MEASUREMENT_UNAVAILABLE)
            return finish("manual_review")
        if m.damage_surface_pct > float(max_damage):
            codes.append(R.SURFACE_DAMAGE_EXCEEDS)
            return finish("reject")

    # --- size class -------------------------------------------------------
    lo = grade_a.get("min_diameter_mm")
    hi = grade_a.get("max_diameter_mm")
    if m.diameter_mm is not None and m.size_method == "aruco_calibrated":
        if lo is not None and m.diameter_mm < float(lo):
            r_lo = relaxed.get("min_diameter_mm")
            r_hi = relaxed.get("max_diameter_mm")
            if r_lo is not None and r_hi is not None \
                    and float(r_lo) <= m.diameter_mm <= float(r_hi):
                codes.append(R.BELOW_GRADE_A_SIZE)
                return finish("relaxed")
            codes.append(R.BELOW_SIZE_THRESHOLD)
            return finish("reject")
        if hi is not None and m.diameter_mm > float(hi):
            r_lo = relaxed.get("min_diameter_mm")
            r_hi = relaxed.get("max_diameter_mm")
            if r_lo is not None and r_hi is not None \
                    and float(r_lo) <= m.diameter_mm <= float(r_hi):
                codes.append(R.BELOW_GRADE_A_SIZE)
                return finish("relaxed")
            codes.append(R.ABOVE_SIZE_THRESHOLD)
            return finish("reject")

    # --- internal condition (acoustic) -----------------------------------
    max_internal = grade_a.get("max_internal_defect_probability")
    if max_internal is not None and m.internal_defect_probability is not None:
        if not m.internal_evidence_valid:
            codes.append(R.ACOUSTIC_NOT_VALIDATED)
            # Unvalidated acoustic evidence may never change a grade.
        elif m.internal_defect_probability > float(max_internal):
            codes.append(R.INTERNAL_DEFECT_RISK)
            return finish("manual_review")

    if not codes:
        codes.append("MEETS_POLICY")
    return finish("grade_a")


def explain(decision: Decision) -> str:
    """One-paragraph explanation suitable for an inspector."""
    lines = [
        f"Decision: {decision.decision.upper()}",
        f"Policy: {decision.policy_id} v{decision.policy_version} "
        f"({'verified' if decision.policy_verified else 'DEMO / unverified'})",
    ]
    for code in decision.reason_codes:
        lines.append(f"  - {code}: {R.describe(code)}")
    return "\n".join(lines)
