#!/usr/bin/env python3
"""Fit the embedding OOD rejection reference from real onion bulb images.

Background
----------
``models/vision/rejection_reference.npz`` never existed, so the embedding
fallback gate (used when no detector artifact is available — e.g. ONNX-only
mobile builds) had no data behind it. This script fits it from **real onion
bulb images** and validates it against negatives.

License handling (important)
----------------------------
The bulbs come from the ``onion-leaves-and-bulb`` source, whose license is
unresolved and which is EXCLUDED from training and redistribution
(see docs/DATASET_GOVERNANCE.md). Fitting a reference computes embeddings
(background-only use); nothing is redistributed. The artifact is
machine-local (gitignored) and rebuildable in about a minute.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import List

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.rejection import build_reference, save_reference  # noqa: E402

SOURCE_DIR = PROJECT_ROOT / "Onion Leaves and Bulb Dataset" / "New Onion - Copy"
BULB_DIR = SOURCE_DIR / "2. Bulb"
LEAVES_DIR = SOURCE_DIR / "1. Leaves"
NEG_DIR = PROJECT_ROOT / "local_data" / "ood_negatives"
OUT_PATH = PROJECT_ROOT / "models" / "vision" / "rejection_reference.npz"
REPORT = PROJECT_ROOT / "evaluation" / "rejection_reference_report.json"


def _embeddings(paths: List[Path], max_images: int) -> np.ndarray:
    from PIL import Image
    import torch
    from inference import vision_inference as vi

    artifact = vi.resolve_artifact(None)
    net = vi._load_net(artifact)
    tfm = vi._transforms(vi._input_size_for(artifact))
    embs = []
    for p in paths[:max_images]:
        img = Image.open(p).convert("RGB")
        x = tfm(img).unsqueeze(0)
        with torch.no_grad():
            embs.append(net.embed(x)[0].cpu().numpy().astype(np.float64))
    return np.asarray(embs)


def _images(folder: Path) -> List[Path]:
    out: List[Path] = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        out.extend(folder.rglob(ext))
    return sorted(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-bulbs", type=int, default=1500,
                    help="number of bulb images to embed (default 1500)")
    ap.add_argument("--max-leaves", type=int, default=300,
                    help="leaf images for the far-negative sanity check")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)

    if not BULB_DIR.exists():
        print(f"bulb directory not found: {BULB_DIR}")
        return 2

    bulbs = _images(BULB_DIR)
    leaves = _images(LEAVES_DIR)
    rng = random.Random(args.seed)
    rng.shuffle(bulbs)
    rng.shuffle(leaves)

    n_bulbs = min(len(bulbs), args.max_bulbs)
    n_leaves = min(len(leaves), args.max_leaves)
    print(f"embedding {n_bulbs} bulbs, {n_leaves} leaves (sanity check)...")
    bulb_emb = _embeddings(bulbs, n_bulbs)
    leaf_emb = _embeddings(leaves, n_leaves) if n_leaves else None

    stats = build_reference(bulb_emb, percentile=99.0)
    save_reference(stats, OUT_PATH)
    print(f"reference saved: {OUT_PATH} (n={stats.n_samples}, "
          f"threshold={stats.threshold:.3f})")

    def distances(embs: np.ndarray) -> np.ndarray:
        d = embs - stats.mean
        return np.sqrt(np.sum(d * d * stats.inv_var, axis=1))

    report = {
        "n_bulb_embeddings": int(stats.n_samples),
        "percentile": 99.0,
        "threshold": float(stats.threshold),
        "bulb_median_distance": float(np.median(distances(bulb_emb))),
    }
    print(f"  bulbs: median distance {report['bulb_median_distance']:.3f} "
          f"vs threshold {stats.threshold:.3f}")

    if leaf_emb is not None and len(leaf_emb):
        leaf_rate = float((distances(leaf_emb) <= stats.threshold).mean())
        report["leaf_inlier_rate"] = leaf_rate
        print(f"  onion LEAVES inlier rate (should be low): {leaf_rate:.1%}")

    negs = _images(NEG_DIR) if NEG_DIR.exists() else []
    if negs:
        neg_emb = _embeddings(negs, 200)
        report["negatives"] = {
            "n": len(negs),
            "inlier_rate": float((distances(neg_emb) <= stats.threshold).mean()),
        }
        print(f"  real negatives: {report['negatives']}")

    report["license_note"] = ("Source license unresolved: background-only "
                              "embedding use; artifact is machine-local "
                              "(gitignored) and rebuildable.")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
