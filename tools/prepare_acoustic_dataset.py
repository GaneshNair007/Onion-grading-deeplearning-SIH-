#!/usr/bin/env python3
"""Prepare GitHub-safe parts for dataset-acoustic.

Packs the files under dataset-acoustic/ into deterministic part directories
(dataset-acoustic/parts/part-NNN) where every part stays under 100,000,000
bytes (decimal). Whole files only — nothing is ever split.

Safety rules enforced:
- never deletes or moves source data (copies only);
- refuses files whose metadata records redistribution_allowed=false;
- refuses raw/processed files without a sidecar metadata JSON;
- refuses any single file larger than 100,000,000 bytes (reports it, exits
  nonzero, and suggests alternatives — never splits WAV/ZIP/JPG/JSON);
- skips ignored caches/weights/credentials;
- detects exact duplicates by SHA-256 and stores each content once;
- generates MANIFEST.csv, checksums.sha256, and a deterministic part report;
- supports --dry-run and deterministic sorting (same inputs -> same parts).

Usage:
    python tools/prepare_acoustic_dataset.py [--dry-run] [--quiet]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE = PROJECT_ROOT / "dataset-acoustic"
PARTS_DIR = BASE / "parts"

PART_LIMIT = 100_000_000          # hard ceiling (decimal bytes)
SOFT_LIMIT = 95_000_000           # report threshold for "large" files

# Source subdirectories packed into parts (deterministic order).
SOURCE_SUBDIRS = ["raw", "processed", "research", "auxiliary", "synthetic"]

# Top-level metadata/docs shipped alongside (deterministic order).
TOP_FILES = [
    "README.md", "SOURCES.md", "LICENSES.md", "collection_protocol.md",
    "metadata_schema.json",
]

IGNORE_DIRS = {"__pycache__", ".venv", "venv", "node_modules", "parts", ".git"}
IGNORE_EXTS = {".pyc", ".pt", ".pth", ".onnx", ".h5", ".tflite", ".joblib",
               ".env", ".pem", ".key", ".secret", ".tmp", ".log", ".db"}
IGNORE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def is_ignored(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return True
    if path.name in IGNORE_NAMES:
        return True
    suffixes = {s.lower() for s in path.suffixes}
    return bool(suffixes & IGNORE_EXTS)


def collect_files() -> List[Path]:
    """Deterministically list packable files (top docs first, then subdirs)."""
    files: List[Path] = []
    for name in TOP_FILES:
        p = BASE / name
        if p.is_file():
            files.append(p)
    for sub in SOURCE_SUBDIRS:
        d = BASE / sub
        if d.is_dir():
            files.extend(p for p in sorted(d.rglob("*")) if p.is_file())
    files = [p for p in files if not is_ignored(p)]
    # Extra safety: MANIFEST/checksums of a previous run are regenerated, not packed.
    files = [p for p in files if p.name not in {"MANIFEST.csv", "checksums.sha256"}]
    return files


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_redistribution(files: List[Path]) -> List[str]:
    """Return a list of policy violations (empty list = safe)."""
    problems: List[str] = []
    for p in files:
        rel = p.relative_to(BASE)
        size = p.stat().st_size
        if size > PART_LIMIT:
            problems.append(
                f"OVERSIZE: {rel.as_posix()} is {size:,} bytes (> {PART_LIMIT:,}). "
                "It will NOT be packed or split. Alternatives: exclude it and "
                "redistribute via an external host, or (if the format is a plain "
                "container like XLSX/ZIP with lossless members) extract members "
                "<100 MB with a script — only with the licensor's permission."
            )
        top = rel.parts[0] if len(rel.parts) > 1 else ""
        if top in {"raw", "processed"}:
            sidecar = p.with_suffix(".json")
            meta_exists = sidecar.exists() or (p.parent / f"{p.stem}.json").exists()
            if not meta_exists and p.suffix.lower() in {".wav", ".flac", ".mp3", ".m4a"}:
                problems.append(
                    f"NO_METADATA: {rel.as_posix()} has no sidecar metadata JSON. "
                    "Files in raw/processed require metadata per metadata_schema.json."
                )
        if top == "auxiliary":
            for meta_candidate in [p.parent / "metadata.json", p.parent.parent / "metadata.json"]:
                if meta_candidate.exists():
                    try:
                        meta = json.loads(meta_candidate.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        continue
                    if meta.get("redistribution_allowed") is False and p != meta_candidate:
                        problems.append(
                            f"NOT_REDISTRIBUTABLE: {rel.as_posix()} belongs to a "
                            "source recorded with redistribution_allowed=false; "
                            "only its metadata may be committed."
                        )
                    break
    return problems


def pack(files: List[Path]) -> List[List[Path]]:
    parts: List[List[Path]] = []
    current: List[Path] = []
    current_bytes = 0
    for p in files:  # deterministic order preserved
        size = p.stat().st_size
        if current and current_bytes + size > PART_LIMIT:
            parts.append(current)
            current, current_bytes = [], 0
        current.append(p)
        current_bytes += size
    if current:
        parts.append(current)
    return parts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    files = collect_files()
    total_bytes = sum(p.stat().st_size for p in files)
    print(f"Packing {len(files)} files, {total_bytes:,} bytes from {BASE}")

    problems = check_redistribution(files)
    if problems:
        for msg in problems:
            print(f"POLICY VIOLATION: {msg}", file=sys.stderr)
        print("Aborting: fix the violations above (nothing was written).",
              file=sys.stderr)
        return 2

    # Duplicate detection by SHA-256.
    seen: Dict[str, Path] = {}
    dup_count = 0
    unique: List[Path] = []
    for p in files:
        if not args.quiet:
            print(f"  hashing {p.name}", end="\r")
        digest = sha256_of(p)
        if digest in seen:
            dup_count += 1
        else:
            seen[digest] = p
            unique.append(p)
    print()

    parts = pack(unique)
    big = [p for p in unique if p.stat().st_size > SOFT_LIMIT]

    print(f"Unique files: {len(unique)} (duplicates skipped: {dup_count})")
    print(f"Parts planned: {len(parts)}")
    for i, part in enumerate(parts, 1):
        pb = sum(p.stat().st_size for p in part)
        print(f"  part-{i:03d}: {len(part):5d} files  {pb:>13,} bytes")
    if big:
        print(f"Files larger than {SOFT_LIMIT:,} bytes: {len(big)}")
        for p in big:
            print(f"  {p.relative_to(BASE).as_posix()}  {p.stat().st_size:,}")
    if not args.dry_run:
        if PARTS_DIR.exists():
            print(f"ERROR: {PARTS_DIR} already exists; remove it manually for a "
                  "fresh run (the script never deletes data).", file=sys.stderr)
            return 4
        PARTS_DIR.mkdir(parents=True)
        manifest_rows = []
        checksum_lines = []
        for i, part in enumerate(parts, 1):
            pdir = PARTS_DIR / f"part-{i:03d}"
            pdir.mkdir()
            pbytes = 0
            for p in part:
                rel = p.relative_to(BASE)
                dest = pdir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
                pbytes += p.stat().st_size
                digest = sha256_of(p)
                manifest_rows.append([f"part-{i:03d}", rel.as_posix(),
                                      p.stat().st_size, digest])
                checksum_lines.append(f"{digest}  dataset-acoustic/parts/part-{i:03d}/{rel.as_posix().replace(' ', '%20')}")
            print(f"  wrote part-{i:03d}: {pbytes:,} bytes")

        with open(PARTS_DIR / "MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["part", "path_in_repo", "bytes", "sha256"])
            w.writerows(manifest_rows)
        (PARTS_DIR / "checksums.sha256").write_text(
            "\n".join(checksum_lines) + "\n", encoding="utf-8")

        # Top-level MANIFEST.csv / checksums.sha256 covering everything packed.
        with open(BASE / "MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["part", "path_in_repo", "source_path", "bytes", "sha256"])
            for (part_name, rel, size, digest) in manifest_rows:
                w.writerow([part_name,
                            f"dataset-acoustic/parts/{part_name}/{rel}",
                            f"dataset-acoustic/{rel}", size, digest])
        (BASE / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n",
                                               encoding="utf-8")
        print(f"Wrote {PARTS_DIR / 'MANIFEST.csv'}, checksums.sha256")
        print(f"Wrote {BASE / 'MANIFEST.csv'} and {BASE / 'checksums.sha256'}")
    else:
        print("DRY RUN — nothing was written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
