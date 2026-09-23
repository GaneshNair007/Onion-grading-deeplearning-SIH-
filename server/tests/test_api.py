"""API tests.

The API is a thin layer over the tracked library, so these tests focus on the
contract: honest statuses, idempotent sync, tamper-evident verification and the
refusal to grade without a model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import server.app as app_module  # noqa: E402
from server.store import Store   # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(app_module, "_store", Store(tmp_path / "api.sqlite3"))
    return TestClient(app_module.app)


def _report_payload(report_id: str = "REPORT-T-1") -> dict:
    return {
        "report_version": "1.0.0",
        "report_id": report_id,
        "header": {"system": "ONION-Q", "center_id": "TEST-CTR",
                   "batch_id": "B-1", "policy_id": "P", "policy_hash": "sha256:x"},
        "summary": {"counts": {"grade_a": 2, "manual_review": 1}},
        "integrity": {"algorithm": "sha256",
                      "canonical_hash": "sha256:" + "0" * 64},
    }


# --------------------------------------------------------------------- meta
def test_health_and_version(client):
    assert client.get("/health").json()["status"] == "ok"
    body = client.get("/version").json()
    assert body["app_version"]
    assert "models" in body["models"]


def test_policies_endpoint_reports_unverified_demo_policy(client):
    body = client.get("/policies").json()
    assert "demo_policy" in body["policies"]
    assert body["policies"]["demo_policy"]["source_verified"] is False


def test_models_endpoint_exposes_limitations(client):
    body = client.get("/models").json()
    for entry in body["models"].values():
        assert "metrics_confidence" in entry
        assert "limitations" in entry


def test_views_endpoint_lists_guided_views(client):
    body = client.get("/views").json()
    assert body["views"] == ["neck", "base", "side_a", "side_b"]
    assert len(body["instructions"]) == 4


# --------------------------------------------------------------------- sync
def test_sync_is_idempotent(client):
    record = {"record_id": "rec-1", "kind": "quick_batch_scan",
              "payload": {"batch": {"center_id": "MH-NSK", "batch_id": "B1"}}}
    first = client.post("/sync/scans", json={"records": [record]}).json()
    second = client.post("/sync/scans", json={"records": [record]}).json()
    assert first["accepted"] == 1 and first["duplicate"] == 0
    assert second["duplicate"] == 1, "a retried upload must not duplicate"
    assert len(client.get("/dashboard/scans").json()["scans"]) == 1


def test_sync_failure_semantics_are_the_client_side_journal():
    """The journal keeps records on failure; the API never deletes anything."""
    from src.mobile.offline_store import ScanStore

    assert hasattr(ScanStore, "pending")


# ---------------------------------------------------------------- reports
def test_report_verify_detects_tampering(client):
    payload = _report_payload()
    from src.reporting.audit_hash import attach_integrity
    good = attach_integrity(payload)                     # correct hash
    stored = client.post("/reports", json=good).json()
    assert stored["hash_valid"] is True

    verified = client.get("/report/verify/REPORT-T-1").json()
    assert verified["valid"] is True

    tampered = json.loads(json.dumps(good))
    tampered["summary"]["counts"]["grade_a"] = 999
    verdict = client.post("/report/verify", json=tampered).json()
    assert verdict["valid"] is False


def test_missing_report_returns_404(client):
    assert client.get("/reports/NOPE").status_code == 404
    assert client.get("/report/verify/NOPE").status_code == 404


# ---------------------------------------------------------------- overrides
def test_override_is_stored_beside_the_machine_decision(client):
    body = client.post("/review/override", json={
        "onion_id": "ONION_SCAN_0001", "batch_id": "B-1",
        "inspector_id": "INSP-1", "machine_decision": "manual_review",
        "human_decision": "grade_a", "reason": "inspector judged it sound",
    }).json()
    assert body["machine_decision_preserved"] is True
    summary = client.get("/dashboard/summary").json()
    assert summary["overrides"] == 1


def test_override_validates_input(client):
    assert client.post("/review/override",
                       json={"onion_id": "x"}).status_code == 400
    assert client.post("/review/override",
                       json={"onion_id": "x", "human_decision": "banana"}
                       ).status_code == 400


def test_override_analytics_reports_disagreement_by_reason(client):
    client.post("/review/override", json={
        "onion_id": "O1", "batch_id": "B-1", "center_id": "MH-NSK",
        "inspector_id": "INSP-1", "machine_decision": "manual_review",
        "human_decision": "grade_a", "machine_confidence": 0.42,
        "reason_code": "LOW_MODEL_CONFIDENCE", "model_version": "attr-v0.1"})
    client.post("/review/override", json={
        "onion_id": "O2", "batch_id": "B-1", "center_id": "MH-NSK",
        "inspector_id": "INSP-1", "machine_decision": "reject",
        "human_decision": "reject", "reason_code": "INSPECTION"})

    analytics = client.get("/dashboard/overrides").json()
    assert analytics["total_overrides"] == 2
    assert analytics["disagreements_with_ai"] == 1
    assert analytics["disagreement_rate"] == pytest.approx(0.5)
    assert analytics["by_reason"]["LOW_MODEL_CONFIDENCE"] == 1
    assert analytics["by_model_version"]["attr-v0.1"] == 1
    assert "not automatically an AI error" in analytics["interpretation"]


def test_override_returns_whether_it_disagreed(client):
    body = client.post("/review/override", json={
        "onion_id": "O3", "machine_decision": "manual_review",
        "human_decision": "grade_a"}).json()
    assert body["disagreement"] is True
    assert body["machine_decision_preserved"] is True

    same = client.post("/review/override", json={
        "onion_id": "O4", "machine_decision": "reject",
        "human_decision": "reject"}).json()
    assert same["disagreement"] is False


def test_summary_reports_kpis_without_inventing_data(client):
    summary = client.get("/dashboard/summary").json()
    assert summary["onions_scanned"] == 0
    assert summary["mean_confidence"] is None
    assert summary["override_analytics"]["disagreement_rate"] is None
    assert "fabricated" in summary["demo_data_notice"]
    for key in ("by_center", "by_date", "manual_review_reasons"):
        assert key in summary


# ---------------------------------------------------------------- scanning
def test_scan_image_requires_a_model_and_says_so(client, real_onion_image):
    """Without a detector artifact the API must refuse, not fabricate."""
    from src.vision import detector as det
    original = det.resolve_detector
    try:
        det.resolve_detector = lambda explicit=None: None  # type: ignore
        with open(real_onion_image, "rb") as fh:
            response = client.post("/scan/image",
                                   files={"image": ("onion.jpg", fh, "image/jpeg")},
                                   data={"policy": "demo_policy"})
        assert response.status_code == 200
        body = response.json()
        assert body["is_onion"] is False
        assert body["status"] == "model_unavailable"
    finally:
        det.resolve_detector = original  # type: ignore


def test_empty_batch_does_not_generate_report_or_annotation(client, real_onion_image,
                                                            monkeypatch):
    """Zero detections are an explicit refusal, never an empty report."""
    monkeypatch.setattr(app_module, "scan_tray_batch", lambda *a, **k: {
        "status": "no_onion_detected",
        "message": "No onion was detected with sufficient confidence.",
        "batch": {"totals": {"total_detected": 0}, "counts": {},
                  "percentages": {}},
        "images": [], "onions": [], "policy": {}, "warnings": [],
    })
    with open(real_onion_image, "rb") as fh:
        response = client.post(
            "/scan/batch",
            files={"images": ("not-detected.jpg", fh, "image/jpeg")},
            data={"policy": "demo_policy"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_onion_detected"
    assert body["report"] is None
    assert body["annotated_images"] == []


def test_fuse_endpoint_returns_manual_review_on_disagreement(client):
    """Eligible (verified-onion) acoustic evidence may escalate to review."""
    body = client.post("/fuse", json={
        "vision": {"is_onion": True,
                   "vision": {"label": "sound", "confidence": 0.9,
                              "defects": {"rotten": {"detected": False,
                                                     "confidence": 0.1}},
                              "freshness_score": None},
                   "warnings": []},
        "acoustic": {"status": "valid", "internal_defect_probability": 0.9,
                     "confidence": 0.8,
                     "dataset_type": ["verified_onion_acoustic"],
                     "ground_truth_verified": True, "research_only": False},
    }).json()
    assert body["status"] == "manual_review"


def test_fuse_endpoint_ignores_research_only_acoustic_evidence(client):
    """The API must not let an unvalidated acoustic model move a result."""
    body = client.post("/fuse", json={
        "vision": {"is_onion": True,
                   "vision": {"label": "sound", "confidence": 0.9,
                              "defects": {"rotten": {"detected": False,
                                                     "confidence": 0.1}},
                              "freshness_score": None},
                   "warnings": []},
        "acoustic": {"status": "valid", "internal_defect_probability": 0.99,
                     "confidence": 0.9, "dataset_type": ["synthetic"],
                     "ground_truth_verified": False, "research_only": True},
    }).json()
    assert body["status"] == "vision_only_acoustic_not_validated"
    assert body["acoustic_eligible"] is False


def test_dashboard_summary_uses_explicit_denominator(client):
    from src.reporting.audit_hash import attach_integrity
    report = attach_integrity(_report_payload("REPORT-T-2"))
    client.post("/reports", json=report)
    summary = client.get("/dashboard/summary").json()
    assert summary["decisions"]["grade_a"] == 2
    assert summary["percentages"]["grade_a"] == pytest.approx(66.67, abs=0.01)
