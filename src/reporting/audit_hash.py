"""Tamper-**evident** integrity: canonical hashing and an append-only chain.

Wording matters: these mechanisms make modification *detectable*. They do not
make a report unforgeable, and no cryptographic claim is made about the
absence of tampering. No blockchain is used, because no requirement here
needs distributed consensus.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def canonical_json(payload: Any) -> str:
    """Deterministic serialisation: sorted keys, tight separators, UTF-8."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_hash(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def hash_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


#: Fields derived FROM the hash, so they cannot be part of the hash target
#: (`qr_payload` encodes the hash itself; including it would be circular).
DERIVED_FIELDS = ("integrity", "qr_payload")


def strip_integrity(report: Dict[str, Any]) -> Dict[str, Any]:
    """Return the report without its derived blocks (the hash target)."""
    return {k: v for k, v in report.items() if k not in DERIVED_FIELDS}


def attach_integrity(report: Dict[str, Any]) -> Dict[str, Any]:
    """Add/replace the integrity block with the canonical report hash."""
    payload = strip_integrity(report)
    out = dict(report)
    out["integrity"] = {
        "algorithm": "sha256",
        "canonical_hash": canonical_hash(payload),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "statement": (
            "Tamper-EVIDENT: any modification to the report content changes "
            "this hash. This is an integrity check, not proof against forgery."),
    }
    return out


def verify_integrity(report: Dict[str, Any]) -> Dict[str, Any]:
    """Check a report against its own integrity block."""
    integrity = report.get("integrity")
    if not integrity or "canonical_hash" not in integrity:
        return {"valid": False, "reason": "no integrity block present"}
    expected = integrity["canonical_hash"]
    actual = canonical_hash(strip_integrity(report))
    return {
        "valid": expected == actual,
        "expected": expected,
        "actual": actual,
        "reason": "hash matches" if expected == actual else "hash mismatch — report was modified",
    }


@dataclass
class AuditEvent:
    event_id: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str = ""
    created_at: str = ""

    def compute(self) -> str:
        self.event_hash = canonical_hash({
            "event_id": self.event_id,
            "previous_hash": self.previous_hash,
            "payload": self.payload,
        })
        return self.event_hash


GENESIS = "sha256:" + "0" * 64


@dataclass
class AuditChain:
    """Append-only hash chain for inspection events."""

    events: List[AuditEvent] = field(default_factory=list)

    @property
    def head(self) -> str:
        return self.events[-1].event_hash if self.events else GENESIS

    def append(self, payload: Dict[str, Any], event_id: str) -> AuditEvent:
        event = AuditEvent(
            event_id=event_id,
            payload=payload,
            previous_hash=self.head,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        event.compute()
        self.events.append(event)
        return event

    def verify(self) -> Dict[str, Any]:
        prev = GENESIS
        for i, event in enumerate(self.events):
            expected = canonical_hash({
                "event_id": event.event_id,
                "previous_hash": prev,
                "payload": event.payload,
            })
            if expected != event.event_hash or event.previous_hash != prev:
                return {"valid": False, "broken_at": i, "event_id": event.event_id}
            prev = event.event_hash
        return {"valid": True, "length": len(self.events), "head": self.head}

    def to_json(self) -> str:
        return json.dumps(
            [{"event_id": e.event_id, "previous_hash": e.previous_hash,
              "event_hash": e.event_hash, "created_at": e.created_at,
              "payload": e.payload} for e in self.events], indent=2)

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(), encoding="utf-8")
        return p

    @classmethod
    def load(cls, path: str | Path) -> "AuditChain":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        chain = cls()
        for item in raw:
            event = AuditEvent(event_id=item["event_id"], payload=item["payload"],
                               previous_hash=item["previous_hash"],
                               event_hash=item["event_hash"],
                               created_at=item.get("created_at", ""))
            chain.events.append(event)
        return chain
