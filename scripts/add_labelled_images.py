#!/usr/bin/env python3
"""Register new labelled onion images with provenance (Phase AN).

Copies (never moves) photographs into a verified-data directory, hashes each
file, refuses duplicates, and appends a provenance row so a later training run
can prove where every image came from.

Why a script instead of "just add the folder": a training set whose origin
cannot be named is unusable in a procurement argument. This writes the
provenance at the moment of collection, when the collector still knows the
answers.

Usage:
    python scripts/add_labelled_images.py \
        --source ./new_photos --label rotten \
        --dataset-type verified_onion_image \
        --license "self-collected (team-owned)" \
        --collector "A. Inspector" \
        --notes "Nashik APMC 2026-09-20, N-53, photographed on the calibration mat"
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.audit_hash import hash_file  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_LABELS = ("rotten", "sprout", "sound", "damaged", "undersized", "unknown")
DATASET_TYPES = ("verified_onion_image", "auxiliary_image",
                 "generic_pretraining_image")
DEFAULT_OUT = PROJECT_ROOT / "dataset-verified"
PROVENANCE_LOG = PROJECT_ROOT / "dataset" / "image_provenance.json"


def _existing_hashes(provenance: Dict) -> set:
    return {row["sha256"] for row in provenance.get("images", [])}


def load_provenance(path: Path) -> Dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"images": [], "statement": (
        "Provenance for every added onion photograph. A row exists only for a "
        "file a human registered with a stated source and label.")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True,
                    help="folder of photographs to register")
    ap.add_argument("--label", required=True, choices=ALLOWED_LABELS)
    ap.add_argument("--dataset-type", default="verified_onion_image",
                    choices=DATASET_TYPES)
    ap.add_argument("--license", required=True,
                    help="licence or ownership statement, e.g. 'self-collected'")
    ap.add_argument("--collector", required=True)
    ap.add_argument("--variety", default="")
    ap.add_argument("--location", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--provenance", type=Path, default=PROVENANCE_LOG)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not args.source.exists():
        print(f"ERROR: source folder not found: {args.source}", file=sys.stderr)
        return 1
    if "not detected" in args.license.lower() or not args.license.strip():
        print("ERROR: a licence/ownership statement is required. Never register "
              "images whose rights you cannot state.", file=sys.stderr)
        return 2

    images: List[Path] = sorted(
        p for p in args.source.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        print(f"ERROR: no images found under {args.source}", file=sys.stderr)
        return 1

    provenance = load_provenance(args.provenance)
    known = _existing_hashes(provenance)

    target_dir = args.out / args.dataset_type / args.label
    added, skipped = 0, 0
    for image in images:
        digest = hash_file(image)
        if digest in known:
            skipped += 1
            continue
        destination = target_dir / image.name
        if destination.exists() and hash_file(destination) != digest:
            destination = target_dir / f"{image.stem}_{digest[-8:]}{image.suffix}"
        if not args.dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image, destination)     # copy: the source is never touched
            # --out may point outside the repository (tests, external drives);
            # record a repo-relative path when possible and an absolute one
            # otherwise, rather than failing the whole run.
            try:
                recorded = str(destination.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except ValueError:
                recorded = str(destination)
            provenance["images"].append({
                "file": recorded,
                "source_file": str(image),
                "sha256": digest,
                "label": args.label,
                "dataset_type": args.dataset_type,
                "license": args.license,
                "collector": args.collector,
                "variety": args.variety,
                "location": args.location,
                "notes": args.notes,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "group_id": f"{args.dataset_type}:{args.collector}:{image.stem}",
            })
        known.add(digest)
        added += 1

    if not args.dry_run:
        args.provenance.parent.mkdir(parents=True, exist_ok=True)
        args.provenance.write_text(json.dumps(provenance, indent=2),
                                   encoding="utf-8")

    print(json.dumps({
        "source": str(args.source),
        "label": args.label,
        "dataset_type": args.dataset_type,
        "images_found": len(images),
        "added": added,
        "duplicates_skipped": skipped,
        "destination": str(target_dir),
        "provenance": str(args.provenance),
        "dry_run": args.dry_run,
        "next_step": ("run python scripts/dataset_governance.py to refresh the "
                      "manifest, then retrain with training/train_attribute_model.py"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
