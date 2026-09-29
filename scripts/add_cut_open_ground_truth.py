#!/usr/bin/env python3
"""Record destructive (cut-open) ground truth for one onion.

This is the single most important data step in the project. Every acoustic or
internal-quality claim depends on it: without a cut-open label, an onion
recording has no ground truth, and no model trained on it can be called an
internal-defect classifier.

The script writes ``dataset-acoustic/raw/<ONION_ID>/ground_truth.json`` and
copies the cut-surface photograph next to the recording. It refuses labels it
does not recognise, requires a named labeller, and asks for a photograph —
because "trust me, it was rotten" is not evidence.

Usage:
    python scripts/add_cut_open_ground_truth.py \
        --onion-id ONION_000123 --internal-label soft_rot \
        --photograph cut_surface.jpg --labelled-by "A. Inspector" \
        --notes "outer scales sound; neck soft and watery"
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

#: Shared vocabulary: the master plan §32 rot terms UNION the project-spec
#: labels (sound / internal_defect / external_defect_only / sprouted /
#: hollow_or_abnormal / uncertain). Kept in one place (src/acoustic/collection)
#: so the CLI tool and the live ground-truth endpoint accept identical labels.
from src.acoustic.collection import INTERNAL_LABELS  # noqa: E402
GROUND_TRUTH_METHODS = ("cut_open", "expert_inspection", "paper_label",
                        "unknown")
RAW_DIR = PROJECT_ROOT / "dataset-acoustic" / "raw"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--onion-id", required=True)
    ap.add_argument("--internal-label", required=True, choices=INTERNAL_LABELS)
    ap.add_argument("--photograph", type=Path, required=True,
                    help="photograph of the cut surface (evidence)")
    ap.add_argument("--labelled-by", required=True,
                    help="person who cut and labelled the onion")
    ap.add_argument("--method", default="cut_open", choices=GROUND_TRUTH_METHODS)
    ap.add_argument("--second-opinion", default="",
                    help="second labeller when the call was not obvious")
    ap.add_argument("--notes", default="")
    ap.add_argument("--raw", type=Path, default=RAW_DIR)
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing ground_truth.json (never the audio)")
    args = ap.parse_args(argv)

    onion_dir = args.raw / args.onion_id
    if not onion_dir.exists():
        print(f"ERROR: no capture directory for {args.onion_id}: {onion_dir}\n"
              "Collect the recordings first: "
              "python scripts/collect_acoustic_sample.py --help", file=sys.stderr)
        return 1
    metadata_path = onion_dir / "metadata.json"
    metadata: Dict[str, Any] = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    if not args.photograph.exists():
        print(f"ERROR: cut-surface photograph not found: {args.photograph}",
              file=sys.stderr)
        return 2

    ground_truth_path = onion_dir / "ground_truth.json"
    if ground_truth_path.exists() and not args.force:
        print(f"ERROR: {ground_truth_path} already exists. Re-cutting the same "
              "onion is not possible; use --force only to correct a mislabel, "
              "and note why in --notes.", file=sys.stderr)
        return 3

    destination = onion_dir / f"cut_surface{args.photograph.suffix.lower()}"
    shutil.copy2(args.photograph, destination)

    payload = {
        "onion_id": args.onion_id,
        "ground_truth_method": args.method,
        "internal_label": args.internal_label,
        "labelled_by": args.labelled_by,
        "second_opinion": args.second_opinion,
        "labelled_at": datetime.now(timezone.utc).isoformat(),
        "evidence": {
            "cut_surface_photograph": destination.name,
            "notes": args.notes,
        },
        "recording_reference": {
            "taps": glob_names(onion_dir, "*.wav"),
            "metadata": metadata_path.name if metadata_path.exists() else None,
            "repeatability_status": (metadata.get("repeatability") or {}).get("status"),
        },
        "warning": ("A single onion is one sample. Do not report classifier "
                    "metrics from a handful of cut-open labels."),
    }
    ground_truth_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Mirror the label into the capture metadata so training can find it without
    # guessing, and record that ground truth now exists.
    if metadata:
        metadata["internal_label"] = args.internal_label
        metadata["external_label"] = metadata.get("external_label", "")
        metadata["ground_truth_method"] = args.method
        metadata["ground_truth_verified"] = True
        metadata["warning"] = ("Internal label verified by cut-open inspection "
                               f"({args.labelled_by}).")
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Propagate the label into every per-WAV sidecar: training/train_acoustic.py
    # reads <recording>.json for labels, not metadata.json. Shared helper with
    # the live collection path so both produce the identical format.
    from src.acoustic.collection import (binary_internal_class,   # noqa: E402
                                         propagate_label_to_sidecars)
    sidecars_updated = propagate_label_to_sidecars(
        onion_dir, args.onion_id, args.internal_label,
        binary_internal_class(args.internal_label), args.method,
        args.labelled_by)

    print(json.dumps({
        "onion_id": args.onion_id,
        "internal_label": args.internal_label,
        "binary_internal_class": binary_internal_class(args.internal_label),
        "ground_truth_file": str(ground_truth_path),
        "photograph": str(destination),
        "metadata_updated": bool(metadata),
        "sidecars_updated": sidecars_updated,
        "next_step": ("python training/train_acoustic.py --data "
                      "dataset-acoustic/raw --require-verified-onion-data "
                      "(refuses until enough labelled onions exist)"),
    }, indent=2))
    return 0


def glob_names(directory: Path, pattern: str) -> list:
    return sorted(p.name for p in directory.glob(pattern))


if __name__ == "__main__":
    raise SystemExit(main())
