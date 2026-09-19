"""Tamper-evidence tests for inspection reports (Phase O).

Four scenarios, exactly as an auditor would try them:

1. unmodified report  → VALID
2. grade percentage changed by 0.01 → INTEGRITY FAILED
3. inspector name changed → INTEGRITY FAILED
4. evidence hash changed → INTEGRITY FAILED

Plus evidence identity: a swapped input file must be detected by re-hashing.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.reporting.audit_hash import (attach_integrity, canonical_hash,
                                      verify_integrity)
from src.reporting.evidence import hash_evidence, verify_evidence
from src.reporting.generator import build_report, finalize, write_report
from src.reporting.qr import QrPayload


@pytest.fixture()
def report(tmp_path_factory) -> dict:
    # Evidence with a real hash: the report claims which files were inspected,
    # so the hash of each input must be part of what is verified.
    image = tmp_path_factory.mktemp("evidence") / "tray.jpg"
    image.write_bytes(b"stable-bytestream-for-hashing")
    evidence = [hash_evidence("original_image", image,
                              extra={"capture_quality": "ok"})]
    batch = {
        "batch_id": "MH-NSK-20260918-0001",
        "center_id": "MH-NSK",
        "inspector_id": "INSP-001",
        "lot_id": "LOT-77",
        "policy": {"policy_id": "ONIONQ_DEMO_STRICT_V1", "version": "1.0.0",
                   "policy_hash": "sha256:abc", "source_verified": False},
        "model_versions": {"detector": "vision-detector-v0.1",
                           "attributes": "vision-attributes-v0.1"},
        "totals": {"total_detected": 4, "graded": 4, "manual_review": 1,
                   "non_onion_rejected": 0, "ungraded_errors": 0},
        "counts": {"grade_a": 2, "relaxed": 1, "reject": 0, "manual_review": 1},
        "percentages": {"grade_a": 50.0, "relaxed": 25.0, "reject": 0.0,
                        "manual_review": 25.0},
        "reason_histogram": {"MEETS_POLICY": 2, "CALIBRATION_MISSING": 1},
        "denominator_note": "percentages use total_detected",
    }
    onions = [{"onion_id": "ONION_SCAN_0001",
               "decision": "grade_a", "reason_codes": ["MEETS_POLICY"],
               "measurements": {"diameter_mm": 52.0,
                                "size_method": "aruco_calibrated"}}]
    return finalize(build_report(batch, onions, evidence=evidence, demo_mode=True))


# 1 ------------------------------------------------------------------- valid
def test_unmodified_report_verifies(report):
    verdict = verify_integrity(report)
    assert verdict["valid"] is True
    assert verdict["reason"] == "hash matches"
    assert report["integrity"]["algorithm"] == "sha256"


def test_integrity_statement_does_not_overclaim(report):
    statement = report["integrity"]["statement"].lower()
    assert "tamper-evident" in statement
    for overclaim in ("tamper-proof", "unforgeable", "cannot be modified"):
        assert overclaim not in statement


# 2 ------------------------------------------------------- percentage tamper
def test_changing_a_percentage_by_a_hundredth_is_detected(report):
    tampered = copy.deepcopy(report)
    tampered["summary"]["percentages"]["grade_a"] = 50.01
    verdict = verify_integrity(tampered)
    assert verdict["valid"] is False
    assert "modified" in verdict["reason"]


# 3 ------------------------------------------------------- inspector tamper
def test_changing_the_inspector_name_is_detected(report):
    tampered = copy.deepcopy(report)
    tampered["header"]["inspector_id"] = "INSP-999"
    assert verify_integrity(tampered)["valid"] is False


# 4 ---------------------------------------------------------- evidence tamper
def test_changing_an_evidence_hash_is_detected(report):
    tampered = copy.deepcopy(report)
    assert tampered["evidence"], "report must carry evidence entries"
    tampered["evidence"][0]["sha256"] = "sha256:" + "0" * 64
    assert verify_integrity(tampered)["valid"] is False


def test_whitespace_reformatting_does_not_break_verification(report, tmp_path):
    """Canonical hashing ignores formatting, so a re-serialised copy still verifies."""
    path = write_report(report, tmp_path)["json"]
    reloaded = json.loads(Path(path).read_text(encoding="utf-8"))
    assert verify_integrity(reloaded)["valid"] is True


def test_hash_is_stable_for_the_same_content():
    payload = {"b": 1, "a": [2, 3]}
    assert canonical_hash(payload) == canonical_hash({"a": [2, 3], "b": 1})


def test_attach_integrity_is_idempotent(report):
    again = attach_integrity(report)
    assert verify_integrity(again)["valid"] is True


# ---------------------------------------------------------- evidence identity
def test_evidence_hashes_a_real_file(tmp_path):
    image = tmp_path / "onion.jpg"
    image.write_bytes(b"not-a-real-jpeg-but-a-stable-bytestream")
    entry = hash_evidence("original_image", image)
    assert entry["sha256"].startswith("sha256:")
    assert entry["bytes"] == image.stat().st_size

    verdict = verify_evidence([entry])
    assert verdict["valid"] is True
    assert verdict["counts"]["ok"] == 1


def test_swapped_evidence_file_is_detected(tmp_path):
    image = tmp_path / "onion.jpg"
    image.write_bytes(b"original")
    entry = hash_evidence("original_image", image)
    image.write_bytes(b"replaced")              # someone swaps the artefact
    verdict = verify_evidence([entry])
    assert verdict["valid"] is False
    assert verdict["counts"]["modified"] == 1


def test_missing_evidence_is_not_treated_as_verified(tmp_path):
    entry = hash_evidence("original_image", tmp_path / "gone.jpg")
    assert entry["sha256"] is None
    verdict = verify_evidence([entry])
    assert verdict["counts"]["missing"] == 1
    assert verdict["valid"] is False


def test_evidence_without_a_path_is_never_a_valid_hash():
    entry = hash_evidence("acoustic_recording", None)
    assert entry["sha256"] is None
    assert entry["note"]


# --------------------------------------------------------------------- QR
def test_qr_payload_carries_the_report_hash():
    from src.reporting.qr import decode_verify_payload

    payload = QrPayload(report_id="REPORT-C-1", report_hash="sha256:deadbeef")
    decoded = decode_verify_payload(payload.encode())
    assert decoded == {"t": "ONIONQ-REPORT", "id": "REPORT-C-1",
                       "h": "sha256:deadbeef", "v": "/report/verify"}
    assert payload.verify_url("http://127.0.0.1:8000") == \
        "http://127.0.0.1:8000/report/verify/REPORT-C-1"


def test_qr_payload_round_trips_the_real_report_hash(report):
    from src.reporting.qr import decode_verify_payload

    decoded = decode_verify_payload(report["qr_payload"])
    assert decoded["h"] == report["integrity"]["canonical_hash"]
    assert decoded["id"] == report["report_id"]
