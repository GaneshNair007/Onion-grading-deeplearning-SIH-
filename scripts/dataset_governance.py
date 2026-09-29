#!/usr/bin/env python3
"""Regenerate the training manifest and the dataset governance report.

Writes:
    dataset/training_manifest.csv      per-image governance rows (tracked)
    evaluation/dataset_governance.json machine-readable governance summary
    docs/DATASET_GOVERNANCE.md         human-readable twin of the above

Never modifies dataset content. Sources with an unresolved licence are listed
under ``excluded_sources``/``unresolved_sources`` and never appear in the
training manifest.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.dataset_registry import DatasetRegistry  # noqa: E402
from src.data.provenance import (  # noqa: E402
    build_training_manifest,
    verify_manifest,
    write_governance_report,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=None,
                    help="dataset manifest path (default: dataset/MANIFEST.csv)")
    ap.add_argument("--split-mode", default="grouped",
                    choices=["grouped", "official"])
    ap.add_argument("--no-write-manifest", action="store_true",
                    help="only refresh the governance report")
    args = ap.parse_args(argv)

    registry = DatasetRegistry(manifest_path=Path(args.manifest)
                               if args.manifest else None)
    if not args.no_write_manifest:
        summary = build_training_manifest(registry, split_mode=args.split_mode)
        print(json.dumps(summary, indent=2))
        check = verify_manifest(Path(summary["manifest"]))
        print(json.dumps(check, indent=2))
        if not check["valid"]:
            print("REFUSING: manifest contains disallowed rows", file=sys.stderr)
            return 2

    report = write_governance_report(registry)
    print(json.dumps({
        "governance_json": report["json_path"],
        "governance_md": report["markdown_path"],
        "categories": report["categories"],
        "dataset_fingerprint": report["dataset_fingerprint"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
