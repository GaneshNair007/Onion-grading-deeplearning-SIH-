#!/usr/bin/env python3
"""Train the classical acoustic baseline on a labelled audio directory.

Current intended use: train the clearly-labelled SYNTHETIC demonstration
classifier on dataset-acoustic/synthetic/demo_chirp_responses to smoke-test
the pipeline. When real data exists in dataset-acoustic/raw/ with sidecar
metadata (dataset_type=verified_onion_acoustic, internal labels from
cut-open sessions), this same script trains on it and the model card will
say so.

Honesty rules enforced here:
- The model card records the dataset_type of every training file.
- Split is by source group / onion_id, never by recording.
- No metric is reported for data the script was not given.

Usage:
    python training/train_acoustic.py --data dataset-acoustic/synthetic/demo_chirp_responses
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.acoustic.features import analyze_file, FEATURE_ORDER  # noqa: E402

MODEL_DIR = PROJECT_ROOT / "models" / "acoustic"
SEED = 42


def infer_group(path: Path) -> str:
    """Group id used for the split (leakage rule applies to REAL data).

    Real recordings carry ONION_xxxxxx ids and are grouped by onion so no
    bulb appears in both train and test. Synthetic clips are independent
    oscillator samples, so each file is its own group.
    """
    m = re.search(r"ONION_\d+", path.name)
    if m:
        return m.group(0)
    return path.stem


def infer_label(path: Path, data_dir: Path) -> int:
    """Label lookup, in order of trust:
    1. sidecar metadata JSON with an internal/external label field,
    2. the synthetic class token in the filename (clearly labelled synthetic).
    Never infers a label from arbitrary filename text.
    """
    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        for key in ("internal_label", "label"):
            val = meta.get(key)
            if isinstance(val, str) and val:
                return 1 if any(w in val.lower()
                                for w in ("rot", "hollow", "defect", "unhealthy")) else 0
    m = re.search(r"synthetic_(firmlike|defectlike)", path.name)
    if m:
        return 1 if m.group(1) == "defectlike" else 0
    raise ValueError(
        f"No trusted label for {path.name}: no sidecar metadata and no "
        "explicitly-labelled synthetic class token.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True,
                    help="Directory tree of training WAVs")
    ap.add_argument("--out-dir", type=Path, default=MODEL_DIR)
    ap.add_argument("--with-logreg", action="store_true")
    args = ap.parse_args()

    try:
        import joblib
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
        from sklearn.model_selection import GroupShuffleSplit
    except Exception as exc:
        print(f"ERROR: scikit-learn/joblib/numpy required: {exc}", file=sys.stderr)
        return 1

    wavs = sorted(args.data.rglob("*.wav"))
    if not wavs:
        print(f"ERROR: no WAV files under {args.data}", file=sys.stderr)
        return 1

    rows, groups, labels, dataset_types = [], [], [], []
    for wav in wavs:
        result = analyze_file(wav)
        if result["features"] is None:
            print(f"  SKIPPED (quality): {wav.name}: {result['error']}")
            continue
        sidecar = wav.with_suffix(".json")
        dtype = "synthetic"
        if sidecar.exists():
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
            dtype = meta.get("dataset_type", dtype)
        rows.append([result["features"][k] for k in FEATURE_ORDER])
        groups.append(infer_group(wav))
        labels.append(infer_label(wav, args.data))
        dataset_types.append(dtype)

    if len(set(labels)) < 2:
        print("ERROR: need at least two classes to train.", file=sys.stderr)
        return 2

    X = np.asarray(rows, dtype=np.float32)
    y = np.asarray(labels)

    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=SEED)
    train_idx, test_idx = next(gss.split(X, y, groups))

    clf = RandomForestClassifier(n_estimators=200, random_state=SEED,
                                 class_weight="balanced")
    clf.fit(X[train_idx], y[train_idx])

    metrics: Dict[str, object] = {}
    y_pred = clf.predict(X[test_idx])
    metrics["random_forest"] = {
        "accuracy": round(float((y_pred == y[test_idx]).mean()), 4),
        "precision": round(float(precision_score(y[test_idx], y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y[test_idx], y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y[test_idx], y_pred, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y[test_idx], y_pred).tolist(),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
    }

    if args.with_logreg:
        lr = LogisticRegression(max_iter=1000, class_weight="balanced")
        lr.fit(X[train_idx], y[train_idx])
        y_pred_lr = lr.predict(X[test_idx])
        metrics["logistic_regression"] = {
            "accuracy": round(float((y_pred_lr == y[test_idx]).mean()), 4),
            "f1": round(float(f1_score(y[test_idx], y_pred_lr, zero_division=0)), 4),
        }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": clf,
        "feature_order": FEATURE_ORDER,
        "metadata": {
            "trained_date": date.today().isoformat(),
            "dataset_type": sorted(set(dataset_types)),
            "n_files": int(len(rows)),
            "data_root": str(args.data),
        },
    }
    if sorted(set(dataset_types)) == ["synthetic"]:
        artifact["metadata"]["warning"] = (
            "SYNTHETIC DEMO MODEL: trained only on oscillator-generated audio. "
            "NOT an onion internal-defect classifier. Not clinically or "
            "industrially validated.")

    joblib.dump(artifact, args.out_dir / "acoustic_baseline.joblib")
    (args.out_dir / "model_card.json").write_text(
        json.dumps({"metrics": metrics, "metadata": artifact["metadata"]},
                   indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"Saved {args.out_dir / 'acoustic_baseline.joblib'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
