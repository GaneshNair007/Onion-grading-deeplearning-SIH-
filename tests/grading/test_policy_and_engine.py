"""Grading tests: policy loading, versioning, and every engine rule.

These tests are the contract for the most defensible claim in the project —
that a neural network never decides a grade, and that an unavailable
measurement escalates instead of being guessed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common import reasons as R
from src.grading.engine import Measurements, decide
from src.grading.policy import (PolicyError, available_policies, load_policy,
                                validate_policy)


# ------------------------------------------------------------------ policy
def test_default_policy_loads_and_is_unverified(policy):
    assert policy.policy_id
    assert policy.source_verified is False
    assert policy.policy_hash.startswith("sha256:")


def test_policy_hash_is_stable_across_loads():
    a, b = load_policy("demo_policy"), load_policy("demo_policy")
    assert a.policy_hash == b.policy_hash


def test_policy_hash_changes_when_rules_change(tmp_path: Path):
    raw = json.loads((Path("config/grading/demo_policy.json")).read_text(
        encoding="utf-8"))
    original = load_policy("demo_policy").policy_hash
    raw["grades"]["grade_a"]["min_diameter_mm"] = 55
    edited = tmp_path / "edited.json"
    edited.write_text(json.dumps(raw), encoding="utf-8")
    assert load_policy(edited).policy_hash != original


def test_invalid_policy_is_rejected():
    with pytest.raises(PolicyError):
        validate_policy({"policy_id": "x"})
    with pytest.raises(PolicyError):
        validate_policy({"policy_id": "x", "version": "1", "effective_from": "d",
                         "source": "s", "source_verified": "yes"})


def test_strict_policy_is_discoverable():
    assert "demo_policy" in available_policies()


# ------------------------------------------------------------------ engine
def _base(**overrides) -> Measurements:
    values = dict(diameter_mm=52.0, size_method="aruco_calibrated",
                  rot_detected=False, rot_confidence=0.02,
                  sprout_detected=False, sprout_confidence=0.01,
                  model_confidence=0.9)
    values.update(overrides)
    return Measurements(**values)


def test_sound_calibrated_onion_is_grade_a(policy):
    decision = decide(_base(), policy)
    assert decision.decision == "grade_a"
    assert R.POLICY_UNVERIFIED in decision.reason_codes   # demo policy is flagged


def test_visible_rot_is_rejected(policy):
    decision = decide(_base(rot_detected=True, rot_confidence=0.93), policy)
    assert decision.decision == "reject"
    assert R.VISIBLE_ROT in decision.reason_codes


def test_sprouting_is_rejected(policy):
    decision = decide(_base(sprout_detected=True, sprout_confidence=0.8), policy)
    assert decision.decision == "reject"
    assert R.SPROUT_DETECTED in decision.reason_codes


def test_missing_calibration_escalates_not_guesses(policy):
    decision = decide(_base(diameter_mm=None, size_method="uncalibrated"), policy)
    assert decision.decision == "manual_review"
    assert R.CALIBRATION_MISSING in decision.reason_codes


def test_uncalibrated_size_is_never_treated_as_millimetres(policy):
    decision = decide(_base(diameter_mm=None, size_method="uncalibrated"), policy)
    assert decision.measurements["diameter_mm"] is None


def test_undersized_onion_inside_relaxed_band_is_relaxed(policy):
    decision = decide(_base(diameter_mm=40.0), policy)
    assert decision.decision == "relaxed"
    assert R.BELOW_GRADE_A_SIZE in decision.reason_codes


def test_oversized_onion_outside_every_band_is_rejected(policy):
    decision = decide(_base(diameter_mm=120.0), policy)
    assert decision.decision == "reject"
    assert R.ABOVE_SIZE_THRESHOLD in decision.reason_codes


def test_low_confidence_escalates(policy):
    decision = decide(_base(model_confidence=0.2), policy)
    assert decision.decision == "manual_review"
    assert R.LOW_MODEL_CONFIDENCE in decision.reason_codes


def test_high_occlusion_escalates(policy):
    decision = decide(_base(occlusion_fraction=0.9), policy)
    assert decision.decision == "manual_review"
    assert R.OCCLUSION_HIGH in decision.reason_codes


def test_multimodal_disagreement_escalates(policy):
    decision = decide(_base(multimodal_disagreement=True), policy)
    assert decision.decision == "manual_review"
    assert R.MULTIMODAL_DISAGREEMENT in decision.reason_codes


def test_unvalidated_acoustic_never_changes_a_grade(policy):
    """Acoustic evidence without cut-open ground truth must not alter a grade."""
    decision = decide(_base(internal_defect_probability=0.99,
                            internal_evidence_valid=False), policy)
    assert decision.decision == "grade_a"
    assert R.ACOUSTIC_NOT_VALIDATED in decision.reason_codes


def test_policy_requiring_masks_escalates_instead_of_inventing_a_number():
    strict = load_policy("strict_with_segmentation")
    decision = decide(_base(damage_surface_pct=None), strict)
    assert decision.decision == "manual_review"
    assert R.MEASUREMENT_UNAVAILABLE in decision.reason_codes


def test_decision_records_policy_identity(policy):
    decision = decide(_base(), policy)
    assert decision.policy_id == policy.policy_id
    assert decision.policy_hash == policy.policy_hash
    assert decision.policy_version == policy.version


def test_engine_never_returns_none_measurements_as_zero(policy):
    decision = decide(_base(rot_detected=None, sprout_detected=None), policy)
    assert decision.measurements["rot_detected"] is None
    assert decision.measurements["sprout_detected"] is None
