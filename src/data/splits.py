"""Leak-free dataset splitting.

Motivation (measured, see `evaluation/split_leakage.json`): the official
Roboflow `valid` split is **85.2 % near-duplicate** with `train`
(median nearest-neighbour cosine similarity 0.9986), while `test` is only
1.0 %. Training against the official `valid` split therefore reports ~0.94
accuracy for a model that scores 0.17 on `test`. This module removes that
failure mode.

Method
------
1. Embed every image with an **ImageNet-pretrained** MobileNetV3-Small
   (no fine-tuned weights, so grouping cannot be circular with the labels).
2. Union-find clustering: two images join a group when cosine similarity
   ≥ ``threshold`` (default 0.98).
3. Assign whole groups to train/validation/test so that no near-duplicate
   family ever spans two splits. Groups are ordered deterministically and
   filled to hit the requested ratios as closely as possible.

Acoustic recordings must be split by `onion_id` (see
`src/acoustic/splits.py`); this module handles images.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

DEFAULT_THRESHOLD = 0.98


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, a: int) -> int:
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def embed_images(paths: Sequence[Path], input_size: int = 128,
                 batch_size: int = 32, pretrained: bool = True) -> np.ndarray:
    """Embed images with ImageNet weights (label-agnostic)."""
    import torch
    from PIL import Image
    from torchvision import transforms

    from src.vision.model import OnionAttributeNet

    net = OnionAttributeNet(pretrained=pretrained)
    net.eval()
    tf = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    chunks = []
    with torch.no_grad():
        for i in range(0, len(paths), batch_size):
            batch = paths[i:i + batch_size]
            tensors = torch.stack([tf(Image.open(p).convert("RGB")) for p in batch])
            chunks.append(net.embed(tensors).numpy())
    return np.vstack(chunks) if chunks else np.zeros((0, 576))


def cluster_near_duplicates(embeddings: np.ndarray,
                            threshold: float = DEFAULT_THRESHOLD,
                            chunk: int = 256) -> List[int]:
    """Return a group id per row (0..k-1), grouping near-duplicate images."""
    X = np.asarray(embeddings, dtype=np.float32)
    if X.ndim != 2:
        raise ValueError("embeddings must be 2-D")
    norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    n = norm.shape[0]
    uf = _UnionFind(n)
    for start in range(0, n, chunk):
        block = norm[start:start + chunk]
        sims = block @ norm.T
        for i in range(block.shape[0]):
            hits = np.where(sims[i] >= threshold)[0]
            for j in hits:
                if j > start + i:
                    uf.union(start + i, int(j))
    roots: Dict[int, int] = {}
    groups: List[int] = []
    for i in range(n):
        r = uf.find(i)
        if r not in roots:
            roots[r] = len(roots)
        groups.append(roots[r])
    return groups


@dataclass
class GroupedSplit:
    assignment: Dict[str, str]          # image path str → split
    group_sizes: Dict[int, int]
    n_groups: int
    threshold: float

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {"train": 0, "validation": 0, "test": 0}
        for split in self.assignment.values():
            out[split] = out.get(split, 0) + 1
        return out


def grouped_split(paths: Sequence[Path], embeddings: np.ndarray,
                  ratios: Tuple[float, float, float] = (0.7, 0.15, 0.15),
                  threshold: float = DEFAULT_THRESHOLD,
                  seed: int = 42) -> GroupedSplit:
    """Assign whole near-duplicate groups to splits."""
    if len(paths) != len(embeddings):
        raise ValueError("paths and embeddings must be the same length")
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("ratios must sum to 1.0")

    groups = cluster_near_duplicates(embeddings, threshold=threshold)
    by_group: Dict[int, List[int]] = {}
    for idx, g in enumerate(groups):
        by_group.setdefault(g, []).append(idx)

    # Deterministic order: largest groups first, ties broken by first index.
    ordered = sorted(by_group.items(),
                     key=lambda kv: (-len(kv[1]), kv[1][0]))
    rng = random.Random(seed)
    # Shuffle within the same size class to avoid systematic bias, then restable.
    ordered = sorted(ordered, key=lambda kv: (-len(kv[1]), rng.random()))

    n = len(paths)
    targets = [ratios[0] * n, ratios[1] * n, ratios[2] * n]
    names = ["train", "validation", "test"]
    filled = [0, 0, 0]
    assignment: Dict[str, str] = {}
    for gid, idxs in ordered:
        # Put the group where it best matches the remaining target deficit.
        deficits = [targets[i] - filled[i] for i in range(3)]
        choice = int(np.argmax(deficits))
        for i in idxs:
            assignment[str(paths[i])] = names[choice]
        filled[choice] += len(idxs)

    return GroupedSplit(assignment=assignment,
                        group_sizes={g: len(v) for g, v in by_group.items()},
                        n_groups=len(by_group), threshold=threshold)


def split_summary(split: GroupedSplit) -> dict:
    sizes = list(split.group_sizes.values())
    return {
        "n_images": len(split.assignment),
        "n_groups": split.n_groups,
        "counts": split.counts(),
        "singleton_groups": int(sum(1 for s in sizes if s == 1)),
        "largest_group": int(max(sizes) if sizes else 0),
        "threshold": split.threshold,
    }
