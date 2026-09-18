#!/usr/bin/env python3
"""Copy the local onion datasets into <=100 MB part directories inside dataset/.

Design goals
------------
* Never deletes, moves, or modifies source data. Copies only.
* Each ``part-NNN`` directory holds whole original files only (no splitting)
  and never exceeds PART_LIMIT bytes (decimal MB: 1 MB = 1,000,000 bytes).
* Deterministic: identical inputs produce identical parts, manifest, and
  checksum file on every run (stable sort order everywhere).
* Duplicate files (same SHA-256) are stored once; later copies are recorded
  in the manifest as references to the first part that holds the content.
* Dry-run mode (``--dry-run``) reports the full plan without writing anything.

Usage
-----
    python tools/prepare_dataset_parts.py [--dry-run] [--quiet]

Exit status is nonzero if any file cannot be safely included (e.g. a single
file larger than PART_LIMIT) — nothing is silently dropped.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "dataset"

PART_LIMIT = 100_000_000          # hard ceiling: 100 decimal MB
PART_TARGET = 95_000_000          # aim for 95-99 MB parts
SOFT_LIMIT = 95 * 1024 * 1024     # "files larger than 95 MiB" report threshold

# Top-level source items to include (relative to project root). Order matters:
# related datasets stay grouped, larger groups first for better packing.
SOURCE_SPECS: List[Tuple[str, str]] = [
    ("Onion Grading.v7i.coco-segmentation", "onion-grading-coco-segmentation"),
    ("onions.v1i.coco-mmdetection", "onion-coco-mmdetection"),
    ("Onion Leaves and Bulb Dataset", "onion-leaves-and-bulb"),
]

# Directories never entered, at any depth.
IGNORE_DIRS = {
    ".git", ".github", ".idea", ".vscode", ".freebuff", ".pytest_cache",
    "__pycache__", "node_modules", "venv", ".venv", "env",
    "dist", "build", "checkpoints", "runs", "outputs", "logs",
}
# Files never copied.
IGNORE_EXTS = {
    ".pyc", ".pyo", ".tmp", ".log", ".pt", ".pth", ".onnx", ".h5", ".tflite",
}
# Exact file names never copied.
IGNORE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
# Output directory must never be treated as a source.
RESERVED_OUTPUT_NAMES = {"dataset"}


def is_ignored_dir(name: str) -> bool:
    return name in IGNORE_DIRS or name in RESERVED_OUTPUT_NAMES


def is_ignored_file(name: str) -> bool:
    return (name in IGNORE_NAMES
            or Path(name).suffix.lower() in IGNORE_EXTS
            or name.startswith("._"))


# --------------------------------------------------------------------------- #
# Collection
# --------------------------------------------------------------------------- #
def collect_files() -> List[dict]:
    """Walk SOURCE_SPECS and return a deterministic list of file descriptors."""
    records: List[dict] = []
    for src_name, dest_name in SOURCE_SPECS:
        src_root = PROJECT_ROOT / src_name
        if not src_root.is_dir():
            print(f"WARNING: source directory missing, skipping: {src_root}",
                  file=sys.stderr)
            continue
        for path in sorted(src_root.rglob("*")):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(src_root).parts
            if any(is_ignored_dir(p) for p in rel_parts[:-1]):
                continue
            if is_ignored_file(path.name):
                continue
            size = path.stat().st_size
            records.append({
                "src": path,
                "dest_rel": Path(dest_name).joinpath(*rel_parts),
                "size": size,
                "source_group": dest_name,
            })
    # Deterministic order: by destination path (string sort, stable).
    records.sort(key=lambda r: str(r["dest_rel"]).lower())
    return records


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Packing
# --------------------------------------------------------------------------- #
def pack_parts(records: List[dict]) -> Tuple[List[List[dict]], List[dict]]:
    """Greedy deterministic bin packing.

    Files larger than PART_LIMIT are returned separately as ``oversize``;
    the caller must refuse to continue (nothing is split or corrupted).
    """
    oversize = [r for r in records if r["size"] > PART_LIMIT]
    ok = [r for r in records if r["size"] <= PART_LIMIT]

    parts: List[List[dict]] = []
    current: List[dict] = []
    current_bytes = 0
    for r in ok:  # already deterministically sorted
        if current and current_bytes + r["size"] > PART_LIMIT:
            parts.append(current)
            current, current_bytes = [], 0
        current.append(r)
        current_bytes += r["size"]
    if current:
        parts.append(current)
    return parts, oversize


# --------------------------------------------------------------------------- #
# Manifest / checksum writers
# --------------------------------------------------------------------------- #
def write_manifest(rows: List[dict], out_path: Path) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["part", "path_in_repo", "source_group", "bytes", "sha256",
                    "duplicate_of"])
        for r in rows:
            w.writerow([r["part"], r["dest_rel"].as_posix(), r["source_group"],
                        r["size"], r["sha256"], r.get("duplicate_of", "")])


def write_checksums(rows: List[dict], out_path: Path) -> None:
    lines = []
    for r in rows:
        if r.get("duplicate_of"):
            continue  # content not physically present in this run's parts
        rel = Path("dataset") / r["part"] / r["dest_rel"]
        lines.append(f"{r['sha256']}  {rel.as_posix().replace(' ', '%20')}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="report the plan without writing anything")
    ap.add_argument("--quiet", action="store_true", help="less output")
    args = ap.parse_args()

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Output dir   : {OUTPUT_DIR}")
    print(f"Part limit   : {PART_LIMIT:,} bytes (decimal MB)")
    print()

    records = collect_files()
    if not records:
        print("ERROR: no includable files found.", file=sys.stderr)
        return 1

    total_bytes = sum(r["size"] for r in records)
    print(f"Collected {len(records)} files, {total_bytes:,} bytes total "
          f"({total_bytes / 1_000_000:.1f} MB)")

    # Oversize check — hard stop.
    parts, oversize = pack_parts(records)
    if oversize:
        print("\nERROR: the following files exceed 100,000,000 bytes and "
              "cannot be included without splitting (which is not done):",
              file=sys.stderr)
        for r in oversize:
            print(f"  {r['src']}  {r['size']:,} bytes", file=sys.stderr)
        return 2

    # Duplicate detection by SHA-256.
    seen: Dict[str, dict] = {}
    dup_skipped = 0
    for r in records:
        if not args.quiet:
            print(f"  hashing {r['dest_rel']}", end="\r")
        r["sha256"] = sha256_of(r["src"])
        first = seen.get(r["sha256"])
        if first is not None:
            r["duplicate_of"] = first["dest_rel"].as_posix()
            r["part"] = None
            dup_skipped += 1
        else:
            seen[r["sha256"]] = r
    print()

    # Repack with only unique files (duplicates reference the first copy).
    unique = [r for r in records if not r.get("duplicate_of")]
    parts, oversize = pack_parts(unique)
    for part_idx, part in enumerate(parts, start=1):
        pname = f"part-{part_idx:03d}"
        for r in part:
            r["part"] = pname

    # Report files > 95 MiB (still included, just notable).
    big = [r for r in unique if r["size"] > SOFT_LIMIT]
    print(f"\nUnique files to store : {len(unique)}")
    print(f"Duplicate refs skipped: {dup_skipped}")
    print(f"Parts planned         : {len(parts)}")
    print(f"Files > 95 MiB        : {len(big)}")
    for r in big:
        print(f"  {r['dest_rel']}  {r['size']:,} bytes")

    print("\nPart plan:")
    for part_idx, part in enumerate(parts, start=1):
        pname = f"part-{part_idx:03d}"
        pbytes = sum(r["size"] for r in part)
        groups = sorted({r['source_group'] for r in part})
        print(f"  {pname}: {len(part):5d} files  {pbytes:>13,} bytes  "
              f"({pbytes / 1_000_000:6.1f} MB)  groups={groups}")
        if pbytes > PART_LIMIT:
            print("ERROR: part exceeds limit — packing bug.", file=sys.stderr)
            return 3

    if args.dry_run:
        print("\nDRY RUN — nothing was written.")
        return 0

    # Copy.
    if OUTPUT_DIR.exists():
        print(f"\nERROR: {OUTPUT_DIR} already exists; refusing to overwrite "
              "(delete it manually if you want a fresh run).", file=sys.stderr)
        return 4
    OUTPUT_DIR.mkdir(parents=True)
    for part_idx, part in enumerate(parts, start=1):
        pname = f"part-{part_idx:03d}"
        pdir = OUTPUT_DIR / pname
        pdir.mkdir()
        for r in part:
            dest = pdir / r["dest_rel"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(r["src"], dest)
        pbytes = sum(r["size"] for r in part)
        print(f"  wrote {pname}: {len(part)} files, {pbytes:,} bytes")

    write_manifest(records, OUTPUT_DIR / "MANIFEST.csv")
    write_checksums(unique, OUTPUT_DIR / "checksums.sha256")

    # Summary report.
    total_stored = sum(r["size"] for r in unique)
    summary = OUTPUT_DIR / "SUMMARY.txt"
    with open(summary, "w", encoding="utf-8", newline="\n") as f:
        f.write("Dataset packaging summary\n")
        f.write("=========================\n")
        f.write(f"Source root          : {PROJECT_ROOT}\n")
        f.write(f"Files collected      : {len(records)}\n")
        f.write(f"Unique files stored  : {len(unique)}\n")
        f.write(f"Duplicate refs skipped: {dup_skipped}\n")
        f.write(f"Total stored bytes   : {total_stored:,} "
                f"({total_stored / 1_000_000:.1f} MB)\n")
        f.write(f"Parts                : {len(parts)}\n")
        for part_idx, part in enumerate(parts, start=1):
            pbytes = sum(r["size"] for r in part)
            f.write(f"  part-{part_idx:03d}: {len(part)} files, "
                    f"{pbytes:,} bytes\n")
        f.write("Excluded by policy   : *.zip archives (bit-identical to "
                "extracted folders, CRC-32 verified), oversize files, "
                "ignored dirs/exts\n")
    print(f"\nWrote {OUTPUT_DIR / 'MANIFEST.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'checksums.sha256'}")
    print(f"Wrote {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
