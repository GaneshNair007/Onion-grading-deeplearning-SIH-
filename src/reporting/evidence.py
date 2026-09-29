"""Evidence hashing for inspection reports.

A report claims *what* was inspected. Without a hash of each input artifact the
claim cannot be re-checked later: someone could swap the photograph and the
report would still "verify". Every evidence entry therefore carries the SHA-256
of the file it describes.

Scope note: this makes an input's *identity* verifiable. It says nothing about
the file's origin, and it is not a signature — the report remains tamper
*evident*, not tamper-proof.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.reporting.audit_hash import hash_file

#: kinds that are realistic inputs to an inspection
EVIDENCE_KINDS = ("original_image", "derived_overlay", "acoustic_recording",
                  "cut_open_photograph", "capture_quality")


def hash_evidence(kind: str, path: Optional[str | Path],
                  extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """One evidence entry: kind + file identity + hash.

    A missing or unreadable file yields ``sha256: None`` with an explicit
    reason — never a placeholder hash that would look like a real fingerprint.
    """
    entry: Dict[str, Any] = {
        "kind": kind,
        "path": str(path) if path is not None else None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if path is None:
        entry["sha256"] = None
        entry["note"] = "no artifact supplied"
    else:
        p = Path(path)
        if p.exists() and p.is_file():
            entry["sha256"] = hash_file(p)
            entry["bytes"] = p.stat().st_size
            entry["file_name"] = p.name
        else:
            entry["sha256"] = None
            entry["note"] = "artifact not found at report time"
    if extra:
        entry.update(extra)
    return entry


def hash_evidence_many(kind: str, paths: List[str | Path]) -> List[Dict[str, Any]]:
    return [hash_evidence(kind, p) for p in paths]


#: Per-image capture metadata worth keeping next to the hash (never the image).
_CAPTURE_KEYS = ("capture_quality", "detector", "markers_detected",
                 "onion_count", "status", "warnings")


def capture_evidence(images: List[Dict[str, Any]],
                     kind: str = "original_image") -> List[Dict[str, Any]]:
    """Evidence entries for the tray/onion images an inspection was based on.

    Call sites used to attach only the capture-quality block, which recorded
    *that* an image was used but not *which* image. The SHA-256 makes the input
    identifiable, so a later swap is detectable.
    """
    entries: List[Dict[str, Any]] = []
    for image in images or []:
        path = image.get("image") or image.get("image_path")
        extra = {k: image[k] for k in _CAPTURE_KEYS if k in image}
        entries.append(hash_evidence(kind, path, extra=extra))
    return entries


def audio_evidence(paths: List[str | Path],
                   kind: str = "acoustic_recording") -> List[Dict[str, Any]]:
    return hash_evidence_many(kind, paths)


def verify_evidence(entries: List[Dict[str, Any]],
                    root: Optional[Path] = None) -> Dict[str, Any]:
    """Re-hash each entry against the file on disk.

    Returns a per-entry verdict plus a summary. An entry whose file is gone is
    reported as ``missing`` — not as passing.
    """
    results: List[Dict[str, Any]] = []
    for entry in entries or []:
        path = entry.get("path")
        recorded = entry.get("sha256")
        if not path:
            results.append({"path": None, "status": "no_path"})
            continue
        p = Path(path)
        if not p.is_absolute() and root is not None:
            p = Path(root) / p
        if not p.exists():
            results.append({"path": str(path), "status": "missing"})
            continue
        actual = hash_file(p)
        results.append({
            "path": str(path),
            "status": "ok" if actual == recorded else "modified",
            "recorded": recorded,
            "actual": actual,
        })
    counts: Dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {
        "valid": all(r["status"] == "ok" for r in results) if results else None,
        "entries": results,
        "counts": counts,
        "statement": ("Evidence hashes make each input's identity re-checkable. "
                      "'missing' means the artifact could not be found now — it "
                      "is not treated as verified."),
    }
