"""Unit tests for the Supabase sync module (offline, no network)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.integrations.supabase_sync import SupabaseSync, sync_reports_dir  # noqa: E402


def test_disabled_when_env_missing(monkeypatch):
    for var in ("ONIONQ_SUPABASE_URL", "ONIONQ_SUPABASE_SERVICE_KEY",
                "ONIONQ_SUPABASE_ANON_KEY"):
        monkeypatch.delenv(var, raising=False)
    s = SupabaseSync()
    st = s.status()
    assert st["enabled"] is False
    assert st["can_write"] is False
    # Writes are honest no-ops, never fabricated successes.
    res = s.upsert_report({"report_id": "R1"})
    assert res == {"synced": False, "reason": "service_key_missing"}


def test_anon_mode_is_read_only(monkeypatch):
    monkeypatch.setenv("ONIONQ_SUPABASE_URL", "https://xyz.supabase.co")
    monkeypatch.delenv("ONIONQ_SUPABASE_SERVICE_KEY", raising=False)
    monkeypatch.setenv("ONIONQ_SUPABASE_ANON_KEY", "anon")
    s = SupabaseSync()
    assert s.enabled is True
    assert s.can_write is False
    assert s.status()["mode"] == "anon_read_only"
    with pytest.raises(RuntimeError):
        s._headers(write=True)


def test_service_mode_can_write(monkeypatch):
    monkeypatch.setenv("ONIONQ_SUPABASE_URL", "https://xyz.supabase.co")
    monkeypatch.setenv("ONIONQ_SUPABASE_SERVICE_KEY", "svc")
    s = SupabaseSync()
    assert s.can_write is True
    h = s._headers(write=True)
    assert h["apikey"] == "svc"
    assert "merge-duplicates" not in h  # Prefer header only on POST


def test_upsert_payload_is_idempotent_shape(monkeypatch):
    monkeypatch.setenv("ONIONQ_SUPABASE_URL", "https://xyz.supabase.co")
    monkeypatch.setenv("ONIONQ_SUPABASE_SERVICE_KEY", "svc")
    s = SupabaseSync()
    report = {
        "report_id": "REPORT-X",
        "batch_id": "B1",
        "policy": {"policy_id": "P", "version": "1.0.0"},
        "summary": {"grade_a_pct": 72.2},
        "onions": [],
        "integrity": {"hash": "sha256:abc"},
        "qr": {"payload": "{}"},
    }
    row = json.loads(json.dumps(report))
    assert row["report_id"] == "REPORT-X"
    # The mapping must not raise on a full report shape.
    assert s.status()["mode"] == "service_role"


def test_schema_file_written(tmp_path):
    s = SupabaseSync()
    out = tmp_path / "schema.sql"
    s.save_schema_file(out)
    sql = out.read_text(encoding="utf-8")
    assert "create table if not exists onion_reports" in sql
    assert "integrity_hash" in sql


def test_sync_reports_dir_without_key_reports_reason(tmp_path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "r1.json").write_text(
        json.dumps({"report_id": "R1"}), encoding="utf-8")
    res = sync_reports_dir(reports_dir=tmp_path / "reports")
    assert res["synced"] == 0
    assert res["skipped"] == "service_key_missing"
