#!/usr/bin/env python3
"""Detect train↔valid near-duplicate leakage using model embeddings.

Motivation: `training/train_attribute_model.py` scored 0.938 accuracy on the
official Roboflow `valid` split but only 0.168 on the official `test` split.
That gap is far too large to be ordinary overfitting, so this script measures
how close valid/test images are to the nearest *training* image in embedding
space. Near-duplicate leakage in `valid` would explain the gap.

Method: for each image, compute the MobileNetV3 embedding from the trained
attribute model, then the cosine similarity to the nearest training embedding.
Reports the similarity distribution and an estimated duplicate rate at a
configurable threshold. This is a *diagnostic*, not a proof of provenance.

Usage:
    python scripts/diagnose_split_leakage.py [--threshold 0.98] [--per-split 300]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.dataset_registry import default_registry  # noqa: E402

QUALITY_SOURCE = "onion-grading-coco-segmentation"
ARTIFACT = PROJECT_ROOT / "models" / "vision" / "attributes" / "attributes_v0.1_128px.pt"


def embed_paths(net, paths: List[Path], input_size: int, batch: int = 32):
    import torch
    from PIL import Image
    from torchvision import transforms

    tf = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    out = []
    with torch.no_grad():
        for i in range(0, len(paths), batch):
            chunk = paths[i:i + batch]
            tensors = torch.stack([tf(Image.open(p).convert("RGB")) for p in chunk])
            out.append(net.embed(tensors).numpy())
    return np.vstack(out) if out else np.zeros((0, 576))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=float, default=0.98,
                    help="cosine similarity above which images count as near-duplicates")
    ap.add_argument("--per-split", type=int, default=300)
    ap.add_argument("--out", type=Path,
                    default=PROJECT_ROOT / "evaluation" / "split_leakage.json")
    args = ap.parse_args()

    import torch
    from src.vision.model import OnionAttributeNet

    if not ARTIFACT.exists():
        print(f"ERROR: attribute artifact missing: {ARTIFACT}", file=sys.stderr)
        return 1

    from src.vision.model import load_checkpoint_state
    net = OnionAttributeNet(pretrained=False)
    net.load_state_dict(load_checkpoint_state(ARTIFACT))
    net.eval()
    input_size = 128
    card = ARTIFACT.parent / "model_card.json"
    if card.exists():
        input_size = int(json.loads(card.read_text(encoding="utf-8"))["input_size"][0])

    reg = default_registry()
    paths_by_split: Dict[str, List[Path]] = {}
    for src in reg.sources():
        if src.source_group != QUALITY_SOURCE:
            continue
        ps = [r["image_path"] for r in reg.records(src)]
        paths_by_split[src.split] = ps[: args.per_split]

    if "train" not in paths_by_split:
        print("ERROR: no train split found", file=sys.stderr)
        return 1

    train_emb = embed_paths(net, paths_by_split["train"], input_size)
    train_norm = train_emb / (np.linalg.norm(train_emb, axis=1, keepdims=True) + 1e-9)

    result: Dict[str, object] = {
        "artifact": str(ARTIFACT.relative_to(PROJECT_ROOT)),
        "threshold": args.threshold,
        "n_train_reference": int(train_norm.shape[0]),
        "splits": {},
        "interpretation": (
            "A near-duplicate rate far above chance in 'valid' while 'test' is low "
            "indicates the official valid split shares content with train - which "
            "makes valid-set metrics optimistic and test-set metrics the honest "
            "reference."),
    }

    for split, paths in sorted(paths_by_split.items()):
        if split == "train":
            continue
        emb = embed_paths(net, paths, input_size)
        norm = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
        sims = norm @ train_norm.T           # (n_split, n_train)
        nn = sims.max(axis=1)
        rate = float((nn >= args.threshold).mean())
        result["splits"][split] = {
            "n": int(len(paths)),
            "nn_similarity_mean": round(float(nn.mean()), 4),
            "nn_similarity_median": round(float(np.median(nn)), 4),
            "nn_similarity_p90": round(float(np.percentile(nn, 90)), 4),
            "near_duplicate_rate": round(rate, 4),
            "example_near_duplicates": int((nn >= args.threshold).sum()),
        }
        print(f"{split:6} n={len(paths):4}  mean NN sim={nn.mean():.4f}  "
              f"median={np.median(nn):.4f}  p90={np.percentile(nn, 90):.4f}  "
              f"near-dup rate={rate:.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
