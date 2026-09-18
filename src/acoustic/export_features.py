"""CLI: batch feature extraction for a directory tree of WAVs.

Usage:
    python -m src.acoustic.export_features --in dataset-acoustic/synthetic/demo_chirp_responses \
        --out dataset-acoustic/processed/demo_features.csv

Only files that pass the quality gates are exported; failures are listed on
stdout with their reasons.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .features import analyze_file, export_features_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_dir", type=Path, required=True)
    ap.add_argument("--out", dest="out_csv", type=Path, required=True)
    args = ap.parse_args()

    wavs = sorted(args.in_dir.rglob("*.wav"))
    if not wavs:
        print(f"No WAV files found under {args.in_dir}")
        return 1

    rows, failures = [], []
    for wav in wavs:
        try:
            result = analyze_file(wav)
            if result["features"] is None:
                failures.append((wav.name, result["error"]))
            else:
                rows.append(result)
        except ValueError as exc:
            failures.append((wav.name, str(exc)))

    out = export_features_csv(rows, args.out_csv)
    print(f"Extracted features for {len(rows)}/{len(wavs)} files -> {out}")
    for name, why in failures:
        print(f"  FAILED: {name}: {why}")
    return 0 if rows else 2


if __name__ == "__main__":
    import sys
    sys.exit(main())
