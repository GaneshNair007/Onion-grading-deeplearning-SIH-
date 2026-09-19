"""Offline-first scan store (mobile sync boundary).

Field inspectors work without connectivity, so every scan and report is
written locally first and synchronised later. The store is:

* **append-only** — a JSONL journal per center, so a crash mid-write cannot
  corrupt earlier records;
* **idempotent** — every record carries a client-generated UUID; the server
  must treat a repeated UUID as the same record;
* **honest about conflict** — records keep their `sync_state` and a
  `server_hash` (filled at sync time) so a modified-server copy is detectable
  rather than silently overwritten;
* **non-destructive** — nothing is ever deleted; synced records are only
  marked.

This module stores data on disk only. It performs no network I/O.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_ROOT = Path(os.environ.get("ONIONQ_DATA_DIR", "local_data")) / "scans"

SYNC_PENDING = "pending"
SYNC_SENT = "sent"
SYNC_FAILED = "failed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScanRecord:
    kind: str                      # "batch_scan" | "deep_scan" | "report"
    payload: Dict[str, Any]
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(default_factory=_now)
    device_id: str = ""
    sync_state: str = SYNC_PENDING
    attempts: int = 0
    last_error: Optional[str] = None
    server_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": self.kind,
            "created_at": self.created_at,
            "device_id": self.device_id,
            "sync_state": self.sync_state,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "server_hash": self.server_hash,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanRecord":
        return cls(kind=data["kind"], payload=data["payload"],
                   record_id=data["record_id"],
                   created_at=data.get("created_at", _now()),
                   device_id=data.get("device_id", ""),
                   sync_state=data.get("sync_state", SYNC_PENDING),
                   attempts=int(data.get("attempts", 0)),
                   last_error=data.get("last_error"),
                   server_hash=data.get("server_hash"))


class ScanStore:
    """Append-only local journal for scan results and reports."""

    def __init__(self, center_id: str, root: str | Path = DEFAULT_ROOT,
                 device_id: str = "") -> None:
        self.center_id = center_id
        self.device_id = device_id
        self.root = Path(root) / center_id
        self.journal = self.root / "scans.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)

    # -- writes ------------------------------------------------------------
    def append(self, kind: str, payload: Dict[str, Any]) -> ScanRecord:
        record = ScanRecord(kind=kind, payload=payload, device_id=self.device_id)
        with open(self.journal, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return record

    def save_scan_result(self, result: Dict[str, Any],
                         kind: Optional[str] = None) -> ScanRecord:
        """Convenience wrapper matching the app contract `saveScanResult`."""
        return self.append(kind or result.get("mode", "scan"), result)

    def mark(self, record_id: str, state: str,
             error: Optional[str] = None,
             server_hash: Optional[str] = None) -> bool:
        """Update a record's sync state (rewrites the journal atomically).

        Marking is not a delete: the record stays in the journal and is
        re-read on the next sync pass, so a lost device never loses evidence.
        """
        records = self.read_all()
        found = False
        for record in records:
            if record.record_id == record_id:
                record.sync_state = state
                record.attempts += 1
                record.last_error = error
                if server_hash:
                    record.server_hash = server_hash
                found = True
        if not found:
            return False
        tmp = self.journal.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.journal)
        return True

    # -- reads -------------------------------------------------------------
    def read_all(self) -> List[ScanRecord]:
        if not self.journal.exists():
            return []
        records: List[ScanRecord] = []
        with open(self.journal, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(ScanRecord.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    # A truncated final line must not hide the earlier records.
                    continue
        return records

    def pending(self) -> List[ScanRecord]:
        return [r for r in self.read_all() if r.sync_state != SYNC_SENT]

    def stats(self) -> Dict[str, Any]:
        records = self.read_all()
        by_state: Dict[str, int] = {}
        by_kind: Dict[str, int] = {}
        for r in records:
            by_state[r.sync_state] = by_state.get(r.sync_state, 0) + 1
            by_kind[r.kind] = by_kind.get(r.kind, 0) + 1
        return {"center_id": self.center_id, "journal": str(self.journal),
                "total": len(records), "by_state": by_state, "by_kind": by_kind,
                "pending": len(self.pending())}

    def export_pending(self) -> List[Dict[str, Any]]:
        """The payloads a sync client should PUT to the server."""
        return [r.to_dict() for r in self.pending()]


def sync_records(store: ScanStore, sender: "callable") -> Dict[str, Any]:
    """Push pending records through `sender(record_dict) -> server_hash`.

    `sender` is supplied by the platform layer (HTTP client). Exceptions are
    caught per record so one failed upload never blocks the queue.
    """
    sent, failed = 0, 0
    for record in store.pending():
        try:
            server_hash = sender(record.to_dict())
        except Exception as exc:  # pragma: no cover - network dependent
            store.mark(record.record_id, SYNC_FAILED, error=str(exc))
            failed += 1
            continue
        store.mark(record.record_id, SYNC_SENT, server_hash=server_hash)
        sent += 1
    return {"sent": sent, "failed": failed, "remaining": len(store.pending())}
