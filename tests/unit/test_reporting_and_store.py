"""Reporting integrity, batch aggregation and offline-store tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.grading.batch import OnionResult, aggregate, batch_id_for
from src.grading.engine import Decision
from src.reporting.audit_hash import (AuditChain, attach_integrity, canonical_hash,
                                      verify_integrity)
from src.reporting.generator import build_report, finalize, write_report
from src.reporting.qr import QrPayload, decode_verify_payload


def _decision(kind: str, codes=None) -> Decision:
    return Decision(decision=kind, reason_codes=codes or ["MEETS_POLICY"],
                    policy_id="TEST", policy_version="1", policy_hash="sha256:x",
                    policy_verified=False, measurements={})


def _batch(counts: dict) -> dict:
    results = []
    for kind, n in counts.items():
        results.extend(OnionResult(onion_id=f"{kind}_{i}",
                                   decision=_decision(kind),
                                   is_onion=True, confidence=0.9)
                       for i in range(n))
    return aggregate("BATCH-1", "MH-NSK", "INSP-1", results,
                     policy_summary={"policy_id": "TEST", "version": "1",
                                     "policy_hash": "sha256:x",
                                     "source_verified": False},
                     model_versions={"detector": "d", "attributes": "a"})


# ------------------------------------------------------------- aggregation
def test_batch_percentages_use_total_detected_and_keep_manual_review():
    batch = _batch({"grade_a": 91, "relaxed": 20, "reject": 11, "manual_review": 4})
    assert batch["totals"]["total_detected"] == 126
    assert batch["percentages"]["grade_a"] == pytest.approx(72.22, abs=0.01)
    assert batch["percentages"]["relaxed"] == pytest.approx(15.87, abs=0.01)
    assert batch["percentages"]["reject"] == pytest.approx(8.73, abs=0.01)
    assert batch["percentages"]["manual_review"] == pytest.approx(3.17, abs=0.01)
    assert "denominator" in batch["denominator_note"].lower()


def test_batch_id_is_deterministic_for_a_given_sequence():
    assert batch_id_for("MH-NSK", seq=182).endswith("-0182")
    assert batch_id_for("MH-NSK").startswith("MH-NSK-")


def test_aggregate_records_reason_histogram():
    batch = _batch({"reject": 3})
    assert batch["reason_histogram"]["MEETS_POLICY"] == 3


# --------------------------------------------------------------- integrity
def test_integrity_hash_is_detected_after_modification():
    report = attach_integrity({"report_id": "R1", "summary": {"grade_a": 5}})
    assert verify_integrity(report)["valid"] is True
    report["summary"]["grade_a"] = 6
    verdict = verify_integrity(report)
    assert verdict["valid"] is False
    assert "modified" in verdict["reason"]


def test_canonical_hash_is_key_order_independent():
    assert canonical_hash({"a": 1, "b": [2, 3]}) == canonical_hash(
        {"b": [2, 3], "a": 1})


def test_audit_chain_detects_tampering():
    chain = AuditChain()
    chain.append({"batch": "B1"}, "evt-1")
    chain.append({"batch": "B2"}, "evt-2")
    assert chain.verify()["valid"] is True
    chain.events[0].payload["batch"] = "TAMPERED"
    assert chain.verify()["valid"] is False


def test_report_records_model_and_policy_versions():
    batch = _batch({"grade_a": 2})
    report = build_report(batch, onion_results=[], demo_mode=True)
    header = report["header"]
    assert header["policy_id"] == "TEST"
    assert header["policy_hash"] == "sha256:x"
    assert header["model_versions"] == {"detector": "d", "attributes": "a"}
    assert header["policy_verified"] is False


def test_report_has_farmer_view_and_writes_markdown(tmp_path: Path):
    report = finalize(build_report(_batch({"grade_a": 5, "reject": 2}), []))
    written = write_report(report, tmp_path)
    assert Path(written["json"]).exists()
    md = Path(written["farmer_markdown"]).read_text(encoding="utf-8")
    assert "Lot" in md and "Rejected" in md
    payload = json.loads(Path(written["json"]).read_text(encoding="utf-8"))
    assert verify_integrity(payload)["valid"] is True


def test_qr_payload_round_trips_and_rejects_foreign_codes():
    payload = QrPayload(report_id="R1", report_hash="sha256:abc")
    decoded = decode_verify_payload(payload.encode())
    assert decoded["id"] == "R1" and decoded["h"] == "sha256:abc"
    assert decode_verify_payload("https://example.com") is None


# ----------------------------------------------------------- offline store
def test_offline_store_appends_reads_and_marks(tmp_path: Path):
    from src.mobile.offline_store import ScanStore, sync_records

    store = ScanStore("MH-NSK", root=tmp_path, device_id="dev-1")
    first = store.save_scan_result({"mode": "quick_batch_scan", "batch": {}})
    store.save_scan_result({"mode": "deep_scan"})
    assert len(store.read_all()) == 2
    assert len(store.pending()) == 2

    result = sync_records(store, lambda record: "sha256:" + record["record_id"])
    assert result == {"sent": 2, "failed": 0, "remaining": 0}
    assert len(store.read_all()) == 2, "syncing must never delete evidence"
    assert store.read_all()[0].record_id == first.record_id


def test_offline_store_keeps_records_when_upload_fails(tmp_path: Path):
    from src.mobile.offline_store import ScanStore, sync_records

    store = ScanStore("MH-NSK", root=tmp_path)

    def failing_sender(record):
        raise ConnectionError("offline")

    store.save_scan_result({"mode": "deep_scan"})
    result = sync_records(store, failing_sender)
    assert result["sent"] == 0 and result["failed"] == 1
    record = store.read_all()[0]
    assert record.sync_state == "failed"
    assert "offline" in record.last_error


def test_truncated_journal_line_does_not_hide_earlier_records(tmp_path: Path):
    from src.mobile.offline_store import ScanStore

    store = ScanStore("MH-NSK", root=tmp_path)
    store.save_scan_result({"mode": "quick_batch_scan"})
    with open(store.journal, "a", encoding="utf-8") as fh:
        fh.write('{"record_id": "broken", "kind": "deep_sc')   # crash mid-write
    assert len(store.read_all()) == 1
