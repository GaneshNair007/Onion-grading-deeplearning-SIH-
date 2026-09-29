"""Procurement policy loading, validation and hashing.

The neural network predicts *measurements*; this module converts them into
procurement decisions using a versioned, hashed policy document. No
government threshold is hard-coded in model weights or in code.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GRADING_DIR = PROJECT_ROOT / "config" / "grading"

DECISIONS = ("grade_a", "relaxed", "reject", "manual_review")


class PolicyError(ValueError):
    """Raised when a policy document is missing or malformed."""


@dataclass(frozen=True)
class Policy:
    policy_id: str
    version: str
    effective_from: str
    source: str
    source_verified: bool
    grades: Dict[str, Dict[str, Any]]
    manual_review: Dict[str, Any] = field(default_factory=dict)
    size: Dict[str, Any] = field(default_factory=dict)
    context_urls: List[str] = field(default_factory=list)
    access_date: str = ""
    notes: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)
    # --- provenance fields that make "verified" auditable ------------------
    source_type: str = "unknown"      # official_document | tender | news_context | demo
    source_url: str = ""
    verification_date: str = ""
    effective_to: Optional[str] = None

    @property
    def canonical(self) -> str:
        """Canonical JSON used for hashing (sorted keys, tight separators)."""
        return json.dumps(self.raw, sort_keys=True, separators=(",", ":"))

    @property
    def policy_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical.encode("utf-8")).hexdigest()

    def grade_named(self, name: str) -> Dict[str, Any]:
        if name not in self.grades:
            raise PolicyError(f"policy {self.policy_id} has no grade '{name}'")
        return self.grades[name]

    def summary(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "policy_hash": self.policy_hash,
            "source": self.source,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_verified": self.source_verified,
            "verification_date": self.verification_date,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "decisions": list(self.grades),
            "manual_review": self.manual_review,
            "display_label": ("Verified procurement standard"
                              if self.source_verified else
                              "Demonstration grading configuration"),
        }


REQUIRED_FIELDS = ("policy_id", "version", "effective_from", "source",
                   "source_verified")


def validate_policy(raw: Dict[str, Any]) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in raw]
    if missing:
        raise PolicyError(f"policy is missing required fields: {missing}")
    if not isinstance(raw["source_verified"], bool):
        raise PolicyError("source_verified must be a boolean")
    # A policy may only claim to be verified when it can name the document and
    # the date it was checked. This stops a news article (which is context, not
    # a standard) from being promoted to an official source by editing one
    # boolean — the exact overclaiming the project forbids.
    if raw["source_verified"]:
        required_for_verification = ("source_url", "verification_date",
                                     "source_type")
        absent = [f for f in required_for_verification if not raw.get(f)]
        if absent:
            raise PolicyError(
                "source_verified=true requires an auditable provenance: "
                f"missing {absent}")
        if str(raw.get("source_type", "")).lower() in {"news", "news_context",
                                                        "demo", "unknown"}:
            raise PolicyError(
                f"source_type={raw.get('source_type')!r} cannot be verified; "
                "obtain an official document/tender first")
    grades = raw.get("grades")
    if grades is not None and not isinstance(grades, dict):
        raise PolicyError("grades must be an object")
    for name, rules in (grades or {}).items():
        if not isinstance(rules, dict):
            raise PolicyError(f"grade '{name}' must be an object")
        lo, hi = rules.get("min_diameter_mm"), rules.get("max_diameter_mm")
        if lo is not None and hi is not None and lo > hi:
            raise PolicyError(f"grade '{name}': min_diameter_mm > max_diameter_mm")


def load_policy(path_or_name: str | Path) -> Policy:
    """Load a policy by path or by stem inside config/grading/."""
    candidate = Path(path_or_name)
    if candidate.suffix != ".json":
        candidate = GRADING_DIR / f"{candidate}.json"
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate if candidate.exists() else candidate
    if not candidate.exists():
        raise PolicyError(f"policy not found: {candidate}")
    raw = json.loads(candidate.read_text(encoding="utf-8"))
    validate_policy(raw)
    return Policy(
        policy_id=raw["policy_id"],
        version=raw["version"],
        effective_from=raw["effective_from"],
        source=raw["source"],
        source_verified=raw["source_verified"],
        grades=raw.get("grades", {}),
        manual_review=raw.get("manual_review", {}),
        size=raw.get("size", {}),
        context_urls=raw.get("context_urls", []),
        access_date=raw.get("access_date", ""),
        notes=raw.get("notes", []),
        raw=raw,
        source_type=raw.get("source_type", "unknown"),
        source_url=raw.get("source_url", ""),
        verification_date=raw.get("verification_date", ""),
        effective_to=raw.get("effective_to"),
    )


def available_policies() -> List[str]:
    if not GRADING_DIR.exists():
        return []
    return sorted(p.stem for p in GRADING_DIR.glob("*.json")
                  if p.name != "schema.json")


def active_policy(name: Optional[str] = None) -> Policy:
    """Return the requested policy, or the default demo policy."""
    if name:
        return load_policy(name)
    import os
    env = os.environ.get("ONIONQ_POLICY")
    if env:
        return load_policy(env)
    return load_policy("demo_policy")
