"""Contract conformance (Phase B.1).

The canonical contracts are only worth having if the **real pipeline** satisfies
them. These tests run the actual code paths — the vision inference wrapper, the
acoustic inference wrapper, the grading engine, batch aggregation and report
generation — and assert that what comes out still validates against the
contract. A refactor that changes a shape without updating the contract fails
here rather than in front of a judge.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "inference"))

from src.common.contracts import (BatchResult, ContractError,             # noqa: E402
                                  GradingDecision, HumanOverride,
                                  InspectionReport, OnionMeasurement,
                                  SizeResult, VisionResult,
                                  acoustic_grading_eligible)
from src.grading.batch import OnionResult, aggregate                       # noqa: E402
from src.grading.engine import Measurements, decide                        # noqa: E402
from src.grading.policy import active_policy                               # noqa: E402
from src.reporting.generator import build_report, finalize                 # noqa: E402


@pytest.fixture(scope="module")
def policy():
    return active_policy("demo_policy")


# ------------------------------------------------------------------- vision
def test_vision_inference_output_satisfies_the_vision_contract(real_onion_image):
    from vision_inference import classify_vision

    try:
        result = classify_vision(str(real_onion_image))
    except RuntimeError as exc:
        pytest.skip(f"torch unavailable: {exc}")
    if result["status"] == "model_unavailable":
        pytest.skip("attribute artifact absent in this checkout")

    contract = VisionResult.from_dict(result["vision"])
    assert contract.model_version
    assert contract.confidence is None or 0.0 <= contract.confidence <= 1.0
    # A defect entry must be a probability + decision, never a bare 0.0.
    for name, defect in contract.defects.items():
        assert "detected" in defect, f"{name} has no 'detected' flag"

    # The research-only head is isolated from the production vision block.
    assert "quality_class" not in result["vision"]
    research = result.get("research_outputs") or {}
    assert "quality_class" in research
    assert "NOT USED BY PROCUREMENT ENGINE" in research["note"]

    # The object-level decision lives at the top level, not in the block.
    assert "is_onion" in result


# ----------------------------------------------------------------- acoustic
def test_acoustic_inference_output_satisfies_the_acoustic_contract(tmp_path):
    import numpy as np
    from scipy.io import wavfile

    from inference.acoustic_inference import classify_acoustic

    sr = 44100
    t = np.linspace(0, 1.6, int(sr * 1.6), endpoint=False)
    sig = 0.5 * np.sin(2 * np.pi * 1200 * t) * np.exp(-6 * t)
    sig[: int(sr * 0.1)] = 0.004 * np.sin(2 * np.pi * 50 * t[: int(sr * 0.1)])
    path = tmp_path / "tap.wav"
    wavfile.write(str(path), sr, np.clip(sig, 1e-9, 1).astype(np.float32))

    result = classify_acoustic(str(path))
    contract = result and __import__(
        "src.common.contracts", fromlist=["AcousticResult"]).AcousticResult.from_dict(result)
    assert contract.status in {"valid", "retest_required", "model_not_trained"}
    # The whole point of the flag: synthetic audio is never eligible.
    if "synthetic" in contract.dataset_types:
        assert contract.research_only is True
        assert contract.grading_eligible is False
        assert acoustic_grading_eligible(result) is False


# ------------------------------------------------------------------ decision
def test_engine_decision_satisfies_the_decision_contract(policy):
    decision = decide(Measurements(diameter_mm=52.0,
                                   size_method="aruco_calibrated",
                                   model_confidence=0.9), policy)
    payload = decision.to_dict()
    contract = GradingDecision.from_dict(payload)
    assert contract.decision in {"grade_a", "relaxed", "reject", "manual_review"}
    assert contract.reason_codes
    assert contract.policy_hash.startswith("sha256:")
    assert contract.policy_verified is False      # demo policy, stated everywhere

    # Every measurement key the engine promises is present, and "not measured"
    # is null rather than 0.0.
    for field in OnionMeasurement.FIELDS:
        assert field in contract.measurements, f"{field} missing from measurements"
    assert contract.measurements["damage_surface_pct"] is None
    assert contract.measurements["internal_defect_probability"] is None
    assert contract.measurements["diameter_mm"] == 52.0


def test_measurement_contract_rejects_fabricated_size():
    with pytest.raises(ContractError):
        SizeResult(diameter_mm=50.0, size_method="uncalibrated")


# --------------------------------------------------------------------- batch
def test_batch_aggregation_satisfies_the_batch_contract(policy):
    decisions = [
        decide(Measurements(diameter_mm=52.0, size_method="aruco_calibrated",
                            model_confidence=0.9), policy),
        decide(Measurements(diameter_mm=None, size_method="uncalibrated",
                            model_confidence=0.9), policy),
        decide(Measurements(diameter_mm=52.0, size_method="aruco_calibrated",
                            rot_detected=True, rot_confidence=0.9,
                            model_confidence=0.9), policy),
    ]
    results = [OnionResult(onion_id=f"ONION_SCAN_{i:04d}", decision=d,
                           is_onion=True, confidence=0.9)
               for i, d in enumerate(decisions, start=1)]
    payload = aggregate("B-1", "MH-NSK", "INSP-1", results,
                        policy.summary(), {"attributes": "test"})
    contract = BatchResult.from_dict(payload)

    counts = contract.counts
    assert counts["grade_a"] == 1 and counts["manual_review"] == 1
    assert counts["reject"] == 1
    assert sum(counts.values()) == contract.totals["total_detected"]
    assert contract.check_percentages() == [], contract.check_percentages()
    assert "manual_review" in contract.denominator_note or \
        "manual_review" in payload["denominator_note"]


def test_batch_percentages_are_reconciled_not_asserted():
    """A hand-written percentage that disagrees with the counts is caught."""
    payload = {
        "batch_id": "B", "center_id": "C", "inspector_id": "I",
        "totals": {"total_detected": 4},
        "counts": {"grade_a": 2, "manual_review": 2},
        "percentages": {"grade_a": 75.0, "manual_review": 25.0},
    }
    problems = BatchResult.from_dict(payload).check_percentages()
    assert problems and "grade_a" in problems[0]


# -------------------------------------------------------------------- report
def test_report_satisfies_the_report_contract(policy):
    batch = {"batch_id": "B-1", "center_id": "MH-NSK", "inspector_id": "INSP-1",
             "policy": policy.summary(), "model_versions": {"attributes": "test"},
             "totals": {"total_detected": 1}, "counts": {"grade_a": 1},
             "percentages": {"grade_a": 100.0}}
    report = finalize(build_report(batch, [{"onion_id": "O1",
                                           "decision": "grade_a",
                                           "reason_codes": ["MEETS_POLICY"],
                                           "measurements": {}}]))
    contract = InspectionReport.from_dict(report)
    assert contract.header["policy_hash"] == policy.policy_hash
    assert contract.header["policy_display_label"]
    assert contract.integrity["canonical_hash"].startswith("sha256:")
    identity = contract.header["identity"]
    assert identity["schema_version"]
    assert identity["git_commit"]


# ------------------------------------------------------------------ override
def test_override_contract_rejects_an_unknown_decision():
    with pytest.raises(ContractError):
        HumanOverride.from_dict({"onion_id": "O1", "human_decision": "banana"})


def test_override_contract_flags_disagreement():
    override = HumanOverride.from_dict({
        "onion_id": "O1", "human_decision": "grade_a",
        "machine_decision": "manual_review", "machine_confidence": 0.42,
        "reason_code": "LOW_MODEL_CONFIDENCE"})
    assert override.is_disagreement is True
    assert override.machine_confidence == 0.42


def test_acoustic_eligibility_is_an_allow_list_not_a_deny_list():
    """Unknown metadata must fail closed."""
    assert acoustic_grading_eligible({}) is False
    assert acoustic_grading_eligible(None) is False
    assert acoustic_grading_eligible({"status": "valid"}) is False
    assert acoustic_grading_eligible(
        {"status": "valid", "dataset_type": ["related_produce_acoustic"]}) is False
    assert acoustic_grading_eligible(
        {"status": "retest_required",
         "dataset_type": ["verified_onion_acoustic"],
         "ground_truth_verified": True}) is False
    assert acoustic_grading_eligible(
        {"status": "valid", "dataset_type": ["verified_onion_acoustic"],
         "ground_truth_verified": True, "research_only": False}) is True
