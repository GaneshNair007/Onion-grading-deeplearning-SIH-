"""Dataset splits at onion level (never at recording level).

Splitting by recording would leak information across days of the same bulb.
This module assigns 'train'/'validation'/'test' per onion_id and propagates
the value to every recording of that onion.
"""
from __future__ import annotations

import random
from typing import Dict, Iterable, List

VALID_SPLITS = ("train", "validation", "test")


def split_by_onion(onion_ids: Iterable[str],
                   ratios: tuple = (0.6, 0.2, 0.2),
                   seed: int = 42) -> Dict[str, str]:
    """Deterministically map each onion_id to a split.

    ratios must sum to ~1.0; assignment is sorted-then-shuffled for
    reproducibility with any fixed seed.
    """
    ids = sorted(set(onion_ids))
    if not ids:
        return {}
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError(f"ratios must sum to 1.0, got {ratios}")
    rng = random.Random(seed)
    order = ids[:]
    rng.shuffle(order)

    n = len(order)
    n_train = int(round(ratios[0] * n))
    n_val = int(round(ratios[1] * n))
    n_test = max(n - n_train - n_val, 1 if n >= 3 else 0)

    assignment: Dict[str, str] = {}
    for i, oid in enumerate(order):
        if i < n_train:
            assignment[oid] = "train"
        elif i < n_train + n_val:
            assignment[oid] = "validation"
        elif i < n_train + n_val + n_test:
            assignment[oid] = "test"
        else:
            assignment[oid] = "train"  # overflow from rounding: keep in train
    return assignment
