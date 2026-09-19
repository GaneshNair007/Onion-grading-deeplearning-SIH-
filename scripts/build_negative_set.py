#!/usr/bin/env python3
"""Build the non-onion negative set from locally supplied photographs.

Non-onion rejection cannot be validated without real negatives, and no
licence-clean negative image dataset is bundled with this repository. So the
negatives must be collected — normally by photographing them yourself.

Usage:
    python scripts/build_negative_set.py --source ~/negatives_photos \
        --label potato --consent "Self-photographed by the project team, 2026-09-18" \
        --dry-run
    python scripts/build_negative_set.py --source ~/negatives_photos --label potato \\
        --consent "Self-photographed by the project team, 2026-09-18"

Rules enforced by this script:

* every image needs a `--consent` statement before it is copied;
* nothing is deleted or moved — files are copied;
* a SHA-256 per image is recorded and exact duplicates are skipped;
* a provenance sidecar is written next to the set, so a reviewer can see where
  every negative came from.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEST_ROOT = PROJECT_ROOT / "dataset-negatives"
ALLOWED_LABELS = ["potato", "tomato", "apple", "garlic", "ball", "hand",
                  "empty_tray", "bag", "basket", "brown_object", "other"]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(source: Path) -> List[Path]:
    if source.is_file():
        return [source] if source.suffix.lower() in IMAGE_SUFFIXES else []
    return sorted(p for p in source.rglob("*")
                  if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--label", required=True, choices=ALLOWED_LABELS)
    ap.add_argument("--consent", required=True,
                    help="provenance statement, e.g. who photographed what and when")
    ap.add_argument("--notes", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.source.exists():
        print(f"source not found: {args.source}", file=sys.stderr)
        return 2

    images = collect(args.source)
    if not images:
        print("no images found", file=sys.stderr)
        return 2

    dest = DEST_ROOT / args.label
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    known: Dict[str, str] = {}
    manifest_path = DEST_ROOT / "negatives_manifest.json"
    if manifest_path.exists():
        try:
            known = {e["sha256"]: e["stored_as"]
                     for e in json.loads(manifest_path.read_text(encoding="utf-8"))
                     ["images"]}
        except (json.JSONDecodeError, KeyError):
            known = {}

    entries, skipped = [], 0
    for src in images:
        digest = sha256_of(src)
        if digest in known:
            skipped += 1
            continue
        stored_as = f"{args.label}/{src.name}"
        if not args.dry_run:
            target = DEST_ROOT / stored_as
            if not target.exists():
                shutil.copy2(src, target)
        entries.append({
            "label": args.label,
            "stored_as": stored_as,
            "sha256": digest,
            "bytes": src.stat().st_size,
            "original_path": str(src),
            "consent": args.consent,
            "notes": args.notes,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"label={args.label}  found={len(images)}  new={len(entries)}  "
          f"exact_duplicates_skipped={skipped}")
    for entry in entries[:10]:
        print(f"  {entry['stored_as']}  {entry['bytes']} bytes")
    if len(entries) > 10:
        print(f"  … {len(entries) - 10} more")

    if args.dry_run:
        print("\n(dry run: nothing written)")
        return 0

    existing = []
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))["images"]
        except (json.JSONDecodeError, KeyError):
            existing = []
    manifest = {
        "kind": "onion_negative_set",
        "statement": (
            "Locally collected non-onion photographs. Each entry records the "
            "operator's consent/provenance statement. These images are for the "
            "rejection gate only and are never treated as onions."),
        "images": existing + entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote {manifest_path} ({len(manifest['images'])} entries total)")
    print("Next: document the set in docs/DATASETS.md and re-run the rejection tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
