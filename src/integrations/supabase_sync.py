"""Supabase sync for ONION-Q inspection reports and scans.

Design (honest, minimal, no SDK lock-in):
- Uses the Supabase REST endpoint (PostgREST) directly over HTTPS with the
  service-role key from the environment. `supabase-py` is NOT required.
- Anon-key mode is supported for reads only (dashboard polling); writes
  require the service key because RLS blocks anonymous writes.
- Nothing here fabricates data: if the env vars are missing, `enabled` is
  False and every method is a no-op that reports the reason.
- Conflict-free: upserts on the report id (primary key), so mobile/offline
  retries and double-syncs cannot create duplicates (idempotent, mirrors
  the local server's idempotent /sync/scans).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

DEFAULT_TIMEOUT_S = 20


class SupabaseSync:
    """Thin PostgREST client for the ONION-Q Supabase project."""

    def __init__(
        self,
        url: Optional[str] = None,
        service_key: Optional[str] = None,
        anon_key: Optional[str] = None,
        table: str = "onion_reports",
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.url = (url or os.environ.get("ONIONQ_SUPABASE_URL", "")).rstrip("/")
        self.service_key = service_key or os.environ.get(
            "ONIONQ_SUPABASE_SERVICE_KEY", ""
        )
        self.anon_key = anon_key or os.environ.get("ONIONQ_SUPABASE_ANON_KEY", "")
        self.table = table
        self.timeout_s = timeout_s

    # ---------------------------------------------------------------- state
    @property
    def enabled(self) -> bool:
        return bool(self.url and (self.service_key or self.anon_key))

    @property
    def can_write(self) -> bool:
        return bool(self.url and self.service_key)

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "can_write": self.can_write,
            "url_configured": bool(self.url),
            "table": self.table,
            "mode": (
                "service_role"
                if self.can_write
                else ("anon_read_only" if self.enabled else "disabled")
            ),
        }

    # -------------------------------------------------------------- headers
    def _headers(self, write: bool = False) -> Dict[str, str]:
        if write and not self.can_write:
            raise RuntimeError(
                "Supabase write requires ONIONQ_SUPABASE_SERVICE_KEY in the "
                "environment (RLS blocks anonymous writes by design)."
            )
        key = self.service_key if write else (self.service_key or self.anon_key)
        if not self.url or not key:
            raise RuntimeError("Supabase URL/key not configured.")
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    # ---------------------------------------------------------------- reads
    def fetch_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        r = requests.get(
            f"{self.url}/rest/v1/{self.table}",
            headers=self._headers(write=False),
            params={
                "select": "*",
                "order": "created_at.desc",
                "limit": str(limit),
            },
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        return r.json()

    # --------------------------------------------------------------- writes
    def upsert_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Idempotent upsert of one inspection report (PK: report id)."""
        if not self.can_write:
            return {"synced": False, "reason": "service_key_missing"}
        row = {
            "report_id": report.get("report_id"),
            "batch_id": report.get("batch_id"),
            "center_id": report.get("center_id"),
            "inspector_id": report.get("inspector_id"),
            "policy_id": (report.get("policy") or {}).get("policy_id"),
            "policy_version": (report.get("policy") or {}).get("version"),
            "model_versions": json.dumps(report.get("model_versions") or {}),
            "summary": json.dumps(report.get("summary") or {}),
            "onions": json.dumps(report.get("onions") or []),
            "integrity_hash": report.get("integrity", {}).get("hash")
            or report.get("hash"),
            "qr_payload": report.get("qr", {}).get("payload"),
            "payload": json.dumps(report),
        }
        r = requests.post(
            f"{self.url}/rest/v1/{self.table}",
            headers={**self._headers(write=True),
                     "Prefer": "resolution=merge-duplicates,return=representation"},
            data=json.dumps([row]),
            timeout=self.timeout_s,
        )
        if r.status_code >= 400:
            return {"synced": False, "status_code": r.status_code,
                    "error": r.text[:500]}
        return {"synced": True, "status_code": r.status_code}

    # --------------------------------------------------------------- setup
    SQL_SCHEMA = """-- ONION-Q Supabase schema (run once in the SQL editor)
create table if not exists onion_reports (
  report_id      text primary key,
  batch_id       text,
  center_id      text,
  inspector_id   text,
  policy_id      text,
  policy_version text,
  model_versions jsonb,
  summary        jsonb,
  onions         jsonb,
  integrity_hash text,
  qr_payload     text,
  payload        jsonb,
  created_at     timestamptz not null default now()
);
alter table onion_reports enable row level security;

-- Public read for dashboards; writes ONLY via the service key.
create policy "public read reports" on onion_reports
  for select using (true);

-- Optional: audit trail of inspector overrides
create table if not exists onion_overrides (
  id            uuid primary key default gen_random_uuid(),
  report_id     text,
  inspector_id  text,
  original      jsonb,
  final         jsonb,
  reason_code   text,
  note          text,
  created_at    timestamptz not null default now()
);
alter table onion_overrides enable row level security;
create policy "public read overrides" on onion_overrides for select using (true);
"""

    def push_schema(self) -> str:
        """Return the SQL to paste into the Supabase SQL editor."""
        return self.SQL_SCHEMA

    def save_schema_file(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.SQL_SCHEMA, encoding="utf-8")
        return p


def sync_reports_dir(reports_dir: str | Path = "reports",
                     url: Optional[str] = None,
                     service_key: Optional[str] = None) -> Dict[str, Any]:
    """Push every local report JSON to Supabase (idempotent)."""
    s = SupabaseSync(url=url, service_key=service_key)
    if not s.can_write:
        return {"synced": 0, "skipped": "service_key_missing",
                "status": s.status()}
    pushed, failed = 0, []
    for p in sorted(Path(reports_dir).glob("*.json")):
        if p.name.endswith("_farmer.md") or "_farmer" in p.stem:
            continue
        try:
            report = json.loads(p.read_text(encoding="utf-8"))
            res = s.upsert_report(report)
            pushed += 1 if res.get("synced") else 0
            if not res.get("synced"):
                failed.append({"file": p.name, "error": res.get("error")})
        except Exception as exc:  # noqa: BLE001 - report and continue
            failed.append({"file": p.name, "error": str(exc)[:200]})
    return {"synced": pushed, "failed": failed, "status": s.status()}
