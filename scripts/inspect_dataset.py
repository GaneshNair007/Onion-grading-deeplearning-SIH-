#!/usr/bin/env python3
"""Inspect the tracked dataset through the registry (no manual unpacking).

Usage:
    python scripts/inspect_dataset.py [--verify-hashes N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.dataset_registry import DatasetRegistry, default_registry  # noqa: E402


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify-hashes", type=int, default=0,
                    help="verify SHA-256 of N annotation files against MANIFEST.csv")
    ap.add_argument("--json", action="store_true", help="emit raw JSON stats")
    args = ap.parse_args()

    reg: DatasetRegistry = default_registry()
    stats = reg.stats()

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print(f"dataset manifest : {reg.manifest_path}")
        print(f"dataset fingerprint: {reg.fingerprint()}")
        print(f"rows in manifest : {len(reg.rows())}")
        print(f"duplicate rows   : {stats['duplicates']} (not packed twice)\n")
        print(f"{'source_group':34} {'split':6} {'imgs':>6} {'anns':>6}  license")
        print("-" * 90)
        for s in stats["sources"]:
            print(f"{s['source_group']:34} {s['split']:6} {s['images']:>6} "
                  f"{s['annotations']:>6}  {s['license']} [{s['license_status']}]")
        print("-" * 90)
        print(f"TOTAL images: {stats['total_images']}  "
              f"annotations: {stats['total_annotations']}\n")
        for s in stats["sources"]:
            print(f"{s['source_group']}/{s['split']}: classes={s['class_counts']}")
            print(f"    supported_tasks={s['supported_tasks']} "
                  f"training_allowed={s['training_allowed']}")
            if s["unknown_categories"]:
                print(f"    UNMAPPED categories (excluded): {s['unknown_categories']}")

    if args.verify_hashes:
        checked = 0
        for row in reg.rows():
            if not row.path_in_repo.endswith(".json"):
                continue
            path = reg.absolute_path(row)
            if not path.exists():
                print(f"MISSING ON DISK: {row.repo_path}", file=sys.stderr)
                return 2
            if sha256_of(path) != row.sha256:
                print(f"HASH MISMATCH: {row.repo_path}", file=sys.stderr)
                return 3
            checked += 1
            if checked >= args.verify_hashes:
                break
        print(f"\nVerified SHA-256 for {checked} annotation files: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
