"""Non-onion rejection.

Two independent gates, in priority order:

1. **Detector gate** (preferred): when a trained onion instance detector is
   available, an image is "onion" iff at least one onion instance passes the
   confidence threshold. This is the only gate that can be trusted in the
   field.
2. **Embedding OOD gate** (fallback, clearly weaker): a one-class Mahalanobis
   distance of the attribute model's 576-d embedding against a reference
   distribution of *real onion* images. Images far from that distribution are
   flagged as "probably not onion".

Honesty about the fallback: a one-class gate calibrated only on onion images
cannot prove "not onion" — it can only say "out of distribution". It is
validated here against programmatically generated **artificial** negatives
(noise / flat colour / geometric shapes), because no licensed non-onion photo
dataset is present in the repository. A real negative set (potato, tomato,
apple, garlic, hands, empty tray, brown objects) is required before any field
claim; see docs/LIMITATIONS.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REFERENCE_NAME = "rejection_reference.npz"


@dataclass
class ReferenceStats:
    mean: np.ndarray
    inv_var: np.ndarray
    threshold: float
    n_samples: int

    def score(self, embedding: np.ndarray) -> float:
        d = embedding - self.mean
        return float(np.sqrt(np.sum((d * d) * self.inv_var)))

    def is_inlier(self, embedding: np.ndarray) -> bool:
        return self.score(embedding) <= self.threshold


def build_reference(embeddings: Sequence[np.ndarray],
                    percentile: float = 99.0) -> ReferenceStats:
    """Fit the one-class reference from real onion embeddings."""
    X = np.asarray(embeddings, dtype=np.float64)
    if X.ndim != 2 or X.shape[0] < 10:
        raise ValueError("need at least 10 embeddings to fit the reference")
    mean = X.mean(axis=0)
    var = X.var(axis=0) + 1e-8
    inv_var = 1.0 / var
    d = X - mean
    dist = np.sqrt(np.sum((d * d) * inv_var, axis=1))
    return ReferenceStats(mean=mean, inv_var=inv_var,
                          threshold=float(np.percentile(dist, percentile)),
                          n_samples=int(X.shape[0]))


def save_reference(stats: ReferenceStats, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, mean=stats.mean, inv_var=stats.inv_var,
                        threshold=stats.threshold, n_samples=stats.n_samples)
    return out


def load_reference(path: str | Path) -> Optional[ReferenceStats]:
    p = Path(path)
    if not p.exists():
        return None
    data = np.load(p)
    return ReferenceStats(mean=data["mean"], inv_var=data["inv_var"],
                          threshold=float(data["threshold"]),
                          n_samples=int(data["n_samples"]))


def make_artificial_negatives(size: int = 224, n: int = 12,
                              seed: int = 7) -> List[np.ndarray]:
    """Deterministic artificial non-onion images (H, W, 3) uint8.

    Explicitly artificial: flat colours, gradients, noise, geometric shapes.
    Used only to sanity-check the OOD gate, never as training data.
    """
    rng = np.random.default_rng(seed)
    imgs: List[np.ndarray] = []
    # flat colours + gradient
    for colour in [(245, 245, 245), (20, 20, 20), (30, 90, 200), (200, 60, 60)]:
        imgs.append(np.full((size, size, 3), colour, dtype=np.uint8))
    grad = np.tile(np.linspace(0, 255, size, dtype=np.uint8)[None, :, None],
                   (size, 1, 3))
    imgs.append(grad)
    # noise
    imgs.append(rng.integers(0, 256, (size, size, 3), dtype=np.uint8))
    # geometric shapes and lines
    for _ in range(3):
        canvas = np.full((size, size, 3), 230, dtype=np.uint8)
        y, x = rng.integers(50, size - 50, 2)
        r = int(rng.integers(20, 60))
        yy, xx = np.ogrid[:size, :size]
        mask = (yy - y) ** 2 + (xx - x) ** 2 <= r * r
        canvas[mask] = rng.integers(0, 256, 3).astype(np.uint8)
        imgs.append(canvas)
    for _ in range(3):
        canvas = np.full((size, size, 3), 245, dtype=np.uint8)
        for _ in range(6):
            y0, x0 = rng.integers(0, size - 80, 2)
            canvas[y0:y0 + 6, x0:x0 + int(rng.integers(40, 80))] = 40
        imgs.append(canvas)
    return imgs[:n]


def detect_with_gate(detector_outputs: Optional[List[dict]],
                     embedding: np.ndarray,
                     reference: Optional[ReferenceStats],
                     detector_threshold: float = 0.5,
                     detector_available: bool = True) -> Dict[str, object]:
    """Combine the two gates into one decision with an explicit reason."""
    reasons: List[str] = []
    if detector_available and detector_outputs is not None:
        strong = [d for d in detector_outputs if d.get("confidence", 0.0) >= detector_threshold]
        decision = bool(strong)
        reasons.append("detector_gate")
        if not decision:
            reasons.append("no_onion_instance_above_threshold")
        return {"is_onion": decision, "gate": "detector", "reasons": reasons,
                "instances": len(strong)}

    if reference is None:
        return {"is_onion": None, "gate": "none", "reasons": ["no_gate_available"],
                "instances": 0}

    inlier = reference.is_inlier(embedding)
    reasons.append("embedding_ood_gate")
    if not inlier:
        reasons.append("out_of_distribution")
    return {"is_onion": bool(inlier), "gate": "embedding_ood",
            "ood_score": round(reference.score(embedding), 3),
            "threshold": round(reference.threshold, 3),
            "reasons": reasons, "instances": 0}
