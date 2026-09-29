#!/usr/bin/env python3
"""Build `models/registry.json` from the artifacts that actually exist.

The registry is generated, never hand-written, so it cannot drift from the
files: an entry appears only when its artifact and model card are present, and
its metrics are copied verbatim from the training run's metrics file.

Usage:
    python scripts/build_model_registry.py
    python scripts/build_model_registry.py --check   # verify, do not write
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

REGISTRY_PATH = PROJECT_ROOT / "models" / "registry.json"

#: Model directory → (model_id, task, metrics filename)
#: `artifact_preference` is an ordered list: a training run writes both
#: `best.pt` (selected by validation) and `last.pt` (crash recovery), and the
#: registry must record the SELECTED one, not whichever sorts last.
MODEL_SPECS = [
    {
        "model_id": "vision-attributes-v0.1",
        "dir": PROJECT_ROOT / "models" / "vision" / "attributes",
        "task": "onion_visible_attribute_classification",
        "artifact_glob": "*.pt",
        "artifact_preference": ["attributes_*.pt"],
        "entry_point": "inference/vision_inference.py::classify_vision",
        "status": "validated_baseline",
    },
    {
        "model_id": "vision-detector-v0.2",
        "dir": PROJECT_ROOT / "models" / "vision" / "detector",
        "task": "onion_instance_detection",
        "artifact_glob": "*.pt",
        "artifact_preference": ["best.pt", "detector_*.pt"],
        "entry_point": "src/vision/detector.py::detect_onions",
        "status": "experimental",
    },
    {
        # The pre-improvement detector is kept and registered separately: a new
        # model may only replace it after beating it on the same held-out split,
        # and the comparison needs both entries to exist.
        "model_id": "vision-detector-baseline-v1",
        "dir": PROJECT_ROOT / "models" / "vision" / "detector-baseline-v1",
        "task": "onion_instance_detection",
        "artifact_glob": "*.pt",
        "artifact_preference": ["detector_*.pt", "best.pt"],
        "entry_point": "src/vision/detector.py::detect_onions",
        "status": "deprecated",
    },
    {
        "model_id": "acoustic-v1-synthetic-demo",
        "dir": PROJECT_ROOT / "models" / "acoustic",
        "task": "impact_acoustic_internal_condition_PROVISIONAL",
        "artifact_glob": "*.joblib",
        "artifact_preference": [],
        "entry_point": "inference/acoustic_inference.py::classify_acoustic",
        "status": "research_only",
    },
]

#: Split strategies that support unqualified metric claims.
LEAK_FREE_SPLIT_MODES = {"grouped", "grouped_leak_safe", "leak_free_grounded"}
#: Split strategies known to be leakage-prone (kept for comparison only).
LEAKY_SPLIT_MODES = {"official", "official_leak_prone"}


def _select_artifact(directory: Path, spec: dict) -> Path | None:
    """Pick the artifact the run itself selected, deterministically."""
    candidates: list[Path] = []
    for pattern in spec.get("artifact_preference") or []:
        candidates = sorted(directory.glob(pattern))
        if candidates:
            break
    if not candidates:
        candidates = sorted(directory.glob(spec["artifact_glob"]))
    return candidates[-1] if candidates else None


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True, check=False)
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_entry(spec: dict, commit: str) -> dict | None:
    directory: Path = spec["dir"]
    artifact = _select_artifact(directory, spec) if directory.exists() else None
    card = _load_json(directory / "model_card.json")
    if artifact is None or card is None:
        return None
    metrics_file = directory / "metrics.json"
    metrics = _load_json(metrics_file)
    # A model card produced by a run that did not use the leak-free split is
    # still listed, but its metrics are flagged as leakage-affected.
    split_mode = (card.get("split_mode")
                  or card.get("split_strategy")
                  or (card.get("split") or {}).get("mode")
                  or ((metrics or {}).get("split") or {}).get("mode")
                  or ("official" if (card.get("training_data") or {}).get("splits")
                      else "unknown"))
    # Metrics confidence is a three-state fact, not a boolean: only a grouped
    # (near-duplicate-aware) split supports unqualified metric claims.
    if split_mode in LEAK_FREE_SPLIT_MODES:
        metrics_confidence = "leak_free"
    elif split_mode in LEAKY_SPLIT_MODES:
        metrics_confidence = "source_split_may_leak"
    else:
        metrics_confidence = "unknown"
    status = spec.get("status", "experimental")
    if _is_synthetic(card):
        metrics_confidence = "synthetic_demo_no_real_ground_truth"
        status = "research_only"
    leakage_safe = metrics_confidence == "leak_free"

    return {
        "model_id": spec["model_id"],
        "task": spec["task"],
        "status": status,
        "architecture": card.get("architecture", "see model_card.json"),
        "artifact_path": str(artifact.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "model_card": str((directory / "model_card.json").relative_to(PROJECT_ROOT))
            .replace("\\", "/"),
        "metrics_file": (str(metrics_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
                         if metrics_file.exists() else None),
        "input_size": card.get("input_size") or _input_size_from_metrics(metrics),
        "dataset_fingerprint": card.get("dataset_fingerprint"),
        "dataset_type": card.get("dataset_type"),
        "trained_at": card.get("trained_at"),
        "git_commit": commit,
        "split_mode": split_mode,
        "split_strategy": card.get("split_strategy"),
        "metrics_confidence": metrics_confidence,
        "metrics_trustworthy": bool(leakage_safe),
        "entry_point": spec["entry_point"],
        "license_notes": card.get("license_notes",
                                  "Training data licences: dataset/LICENSES_AND_SOURCES.md"),
        "limitations": card.get("limitations", []),
        "metrics": _compact_metrics(metrics),
    }


#: Metric blocks copied verbatim when present in a run's metrics file.
METRIC_BLOCKS = ("quality_test", "quality_valid", "defects_test",
                 "defects_val_mmdet_carveout", "detection_test",
                 "detection_valid", "test", "validation")


def _input_size_from_metrics(metrics):
    training = (metrics or {}).get("training") or {}
    for key in ("input_size", "min_size"):
        value = training.get(key)
        if value:
            return [value, value]
    return None


def _is_synthetic(card: dict) -> bool:
    blob = json.dumps(card).lower()
    return "synthetic" in blob or "demo" in blob and "onion ground truth" in blob


def _compact_metrics(metrics):
    """Copy the reportable metric blocks; never invent a missing number."""
    if not isinstance(metrics, dict):
        return None
    out: dict = {}
    split = metrics.get("split")
    if isinstance(split, dict):
        out["split_mode"] = split.get("mode")
        out["split_counts"] = split.get("counts")

    for name in METRIC_BLOCKS:
        block = metrics.get(name)
        if not isinstance(block, dict):
            continue
        flat = {k: v for k, v in block.items()
                if isinstance(v, (int, float, str))}
        per_head = {k: {kk: vv for kk, vv in v.items()
                        if isinstance(vv, (int, float, str))}
                    for k, v in block.items() if isinstance(v, dict)}
        if per_head:
            flat["per_head"] = per_head
        out[name] = flat

    return out or {"note": "see metrics_file"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=REGISTRY_PATH)
    args = ap.parse_args()

    commit = git_commit()
    models = {}
    absent = []
    for spec in MODEL_SPECS:
        entry = build_entry(spec, commit)
        if entry is None:
            absent.append({"model_id": spec["model_id"],
                           "reason": "artifact or model_card.json not present",
                           "expected_dir": str(spec["dir"].relative_to(PROJECT_ROOT))})
        else:
            models[entry["model_id"]] = entry

    registry = {
        "registry_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "statement": (
            "Generated from on-disk artifacts and model cards. An absent entry "
            "means the artifact is genuinely missing (for example because it is "
            "not committed or has not been trained yet) — never that it exists."),
        "models": models,
        "not_available": absent,
    }

    if args.check:
        current = _load_json(args.out)
        same = (current is not None
                and {k: v for k, v in current.items() if k != "generated_at"}
                == {k: v for k, v in registry.items() if k != "generated_at"})
        print(json.dumps({"up_to_date": same,
                          "models": sorted(models),
                          "not_available": [a["model_id"] for a in absent]},
                         indent=2))
        return 0 if same else 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    for model_id, entry in models.items():
        print(f"  {model_id:<28} {entry['artifact_path']}  "
              f"metrics_confidence={entry['metrics_confidence']}")
    for item in absent:
        print(f"  {item['model_id']:<28} ABSENT ({item['reason']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
