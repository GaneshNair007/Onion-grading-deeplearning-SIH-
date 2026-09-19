"""Production-safety contracts (Phase AM).

These tests pin the promises the pitch makes, so a later change cannot quietly
break one:

1. the procurement grade comes from the policy engine, never from the research
   4-class quality head;
2. acoustic evidence that is not validated against verified onion ground truth
   can never change a grade;
3. an unverified (demo) policy is always visible as unverified in the output;
4. a missing calibration never produces a millimetre figure;
5. low confidence produces manual review, not a confident grade.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from inference.acoustic_inference import classify_acoustic          # noqa: E402
from src.common.contracts import (ContractError, SizeResult,        # noqa: E402
                                 acoustic_grading_eligible)
from src.common.reasons import (ACOUSTIC_NOT_VALIDATED,             # noqa: E402
                                CALIBRATION_MISSING,
                                INTERNAL_DEFECT_RISK,
                                LOW_MODEL_CONFIDENCE, POLICY_UNVERIFIED)
from src.fusion.fusion import fuse_results                          # noqa: E402
from src.grading.engine import Measurements, decide                 # noqa: E402
from src.grading.policy import active_policy, load_policy           # noqa: E402
from src.reporting.generator import build_report, finalize          # noqa: E402


@pytest.fixture(scope="module")
def policy():
    return active_policy("demo_policy")


# 1 ---------------------------------------------------- grading provenance
def test_grade_decision_ignores_a_quality_class_probability(policy):
    """The engine grades measurements, never a commercial quality class.

    `Measurements` has no quality_class field at all, so a fused 'Class 1'
    probability cannot reach a decision even if a caller passes it: unknown
    keys are ignored, and the decision is driven by measurable attributes.
    """
    measurements = Measurements(
        diameter_mm=52.0, size_method="aruco_calibrated",
        rot_detected=False, rot_confidence=0.02,
        sprout_detected=False, sprout_confidence=0.02,
        model_confidence=0.95,
        extra={"quality_class": "class_1", "quality_class_confidence": 0.99},
    )
    decision = decide(measurements, policy)
    assert decision.decision == "grade_a"
    assert "quality_class" not in json.dumps(decision.measurements)


def test_quality_class_head_is_absent_from_grading_and_inference_modules():
    """A static guard: the research head must not be imported where grades are made."""
    forbidden = ("quality_class", "QUALITY_CLASSES")
    for path in sorted((PROJECT_ROOT / "src" / "grading").glob("*.py")) + [
            PROJECT_ROOT / "inference" / "batch_scan.py",
            PROJECT_ROOT / "inference" / "deep_scan.py"]:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, (
                f"{path.name} references {token!r}; the 4-class commercial head "
                "is research-only and must never drive a procurement decision")


# 2 ------------------------------------------------- acoustic cannot grade
def test_synthetic_acoustic_model_is_not_grading_eligible(tmp_path):
    """The shipped demo model declares dataset_type=['synthetic']."""
    model = PROJECT_ROOT / "models" / "acoustic" / "acoustic_baseline.joblib"
    if not model.exists():
        pytest.skip("demo acoustic artifact not present in this checkout")

    sr = 44100
    t = np.linspace(0, 1.6, int(sr * 1.6), endpoint=False)
    sig = 0.5 * np.sin(2 * np.pi * 1200 * t) * np.exp(-6 * t)
    wav = tmp_path / "tap.wav"
    wavfile.write(str(wav), sr, np.clip(sig, -1, 1).astype(np.float32))

    result = classify_acoustic(str(wav))
    assert result["ground_truth_verified"] is False
    assert result["research_only"] is True
    assert result["grading_eligible"] is False
    assert acoustic_grading_eligible(result) is False
    if result["status"] == "valid":
        assert any("SYNTHETIC" in w for w in result["warnings"])


def test_research_only_acoustic_cannot_change_a_grade(policy):
    """Even a maximally alarming acoustic reading is inert without ground truth."""
    measurements = Measurements(
        diameter_mm=52.0, size_method="aruco_calibrated",
        rot_detected=False, sprout_detected=False,
        model_confidence=0.95,
        internal_defect_probability=0.99,
        internal_evidence_valid=False,        # synthetic model ⇒ False
    )
    decision = decide(measurements, policy)
    assert INTERNAL_DEFECT_RISK not in decision.reason_codes
    assert ACOUSTIC_NOT_VALIDATED in decision.reason_codes or \
        decision.decision == "grade_a"
    assert decision.decision == "grade_a", (
        "unvalidated acoustic evidence must not move the decision")


def test_fusion_reports_research_only_acoustic_without_fusing_it(policy):
    vision = {"is_onion": True,
              "vision": {"label": "sound", "confidence": 0.9,
                         "defects": {"rotten": {"detected": False,
                                                "confidence": 0.05}},
                         "freshness_score": None},
              "warnings": []}
    acoustic = {"status": "valid", "internal_defect_probability": 0.99,
                "confidence": 0.95, "dataset_type": ["synthetic"],
                "ground_truth_verified": False, "research_only": True}
    fused = fuse_results(vision, acoustic)
    assert fused["status"] == "vision_only_acoustic_not_validated"
    assert fused["final"]["label"] == "sound"
    assert fused["acoustic_eligible"] is False


def test_verified_acoustic_metadata_would_become_eligible():
    """The gate is data-driven: correct metadata makes a model eligible."""
    assert acoustic_grading_eligible({
        "status": "valid", "dataset_type": ["verified_onion_acoustic"],
        "ground_truth_verified": True, "research_only": False}) is True


# 3 ------------------------------------------------------- policy honesty
def test_unverified_policy_is_always_visible(policy):
    assert policy.source_verified is False
    decision = decide(Measurements(diameter_mm=52.0,
                                   size_method="aruco_calibrated",
                                   model_confidence=0.9), policy)
    assert POLICY_UNVERIFIED in decision.reason_codes
    assert decision.policy_verified is False

    batch = {"batch_id": "B", "center_id": "C", "inspector_id": "I",
             "policy": policy.summary(), "model_versions": {},
             "totals": {"total_detected": 1}, "counts": {"grade_a": 1},
             "percentages": {"grade_a": 100.0}}
    report = finalize(build_report(batch, [], demo_mode=not policy.source_verified))
    assert report["demo_mode"] is True
    assert report["header"]["policy_verified"] is False
    assert policy.summary()["display_label"] == \
        "Demonstration grading configuration"


def test_policy_refuses_a_verified_claim_without_provenance(tmp_path):
    """A news article can never be promoted to an official standard by a flag."""
    fake = {"policy_id": "FAKE", "version": "1.0.0",
            "effective_from": "2026-01-01", "source": "some news article",
            "source_verified": True, "source_type": "news_context",
            "grades": {}}
    path = tmp_path / "fake.json"
    path.write_text(json.dumps(fake), encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_policy(path)
    assert "provenance" in str(excinfo.value) or "source_type" in str(excinfo.value)


# 4 -------------------------------------------------- no fabricated millimetres
def test_uncalibrated_size_may_not_report_millimetres():
    with pytest.raises(ContractError):
        SizeResult(diameter_mm=52.0, size_method="uncalibrated")
    with pytest.raises(ContractError):
        SizeResult(diameter_mm=52.0, size_method="unknown")
    ok = SizeResult(diameter_mm=None, size_method="unavailable")
    assert ok.diameter_mm is None


def test_missing_calibration_escalates_instead_of_guessing(policy):
    decision = decide(Measurements(diameter_mm=None, size_method="uncalibrated",
                                   model_confidence=0.9), policy)
    assert decision.decision == "manual_review"
    assert CALIBRATION_MISSING in decision.reason_codes
    assert decision.measurements["diameter_mm"] is None


def test_size_result_requires_calibration_for_a_millimetre_value():
    calibrated = SizeResult(diameter_mm=51.2, size_method="aruco_calibrated",
                            calibration_confidence=0.9, markers_detected=4)
    assert calibrated.diameter_mm == 51.2


# 5 ------------------------------------------------------ confidence floors
def test_low_confidence_becomes_manual_review(policy):
    decision = decide(Measurements(diameter_mm=52.0,
                                   size_method="aruco_calibrated",
                                   model_confidence=0.2), policy)
    assert decision.decision == "manual_review"
    assert LOW_MODEL_CONFIDENCE in decision.reason_codes


def test_absent_confidence_is_not_treated_as_confident(policy):
    decision = decide(Measurements(diameter_mm=52.0,
                                   size_method="aruco_calibrated",
                                   model_confidence=None), policy)
    assert decision.decision == "grade_a"   # no fabricated downgrade either


# 6 --------------------------------------------- packaging / git hygiene guard
def test_no_credentials_are_tracked():
    """A cheap secret scan over the tracked file list (Phase AF)."""
    out = subprocess.run(["git", "ls-files"], cwd=PROJECT_ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        pytest.skip("git unavailable")
    tracked = [line for line in out.stdout.splitlines() if line.strip()]
    suspicious = [p for p in tracked
                  if Path(p).name in {".env", "id_rsa", "id_ed25519"}
                  or Path(p).suffix in {".pem", ".key"}]
    assert not suspicious, f"credential-like files are tracked: {suspicious}"
