"""Self-contained onion attribute model.

Replaces the previous version that imported `app.vision.model` from the
untracked local `backend/` directory (audit finding P0.1). This module has no
dependency outside `torch`/`torchvision`.

Task design is driven strictly by labels that actually exist in the tracked
dataset (audit §7):

* ``quality_class`` — 4-class single-label head from the Roboflow *Onion
  Grading v7* categories (extra_class / class_1 / class_2 / reject).
* ``rotten`` — binary head from Roboflow *onions v1* ("rotten").
* ``sprout`` — binary head from Roboflow *onions v1* ("sprout").
* ``embedding`` — pooled backbone features, used for OOD/non-onion gating.

Labels that no tracked dataset supports (``damaged``, ``undersized``,
``bruising``, shelf-life/decay) are deliberately **absent**: the previous
implementation fabricated them as constants (audit finding P0.2).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import torch
import torch.nn as nn
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

EMBEDDING_DIM = 576
QUALITY_CLASSES: List[str] = ["extra_class", "class_1", "class_2", "reject"]
BINARY_HEADS: List[str] = ["rotten", "sprout"]
# Convenience list used by generic callers/UI. Does NOT imply trainability.
ATTRIBUTE_TASKS: List[str] = ["quality_class"] + BINARY_HEADS


class OnionAttributeNet(nn.Module):
    """MobileNetV3-Small backbone with three honest task heads."""

    def __init__(self, pretrained: bool = True, dropout: float = 0.2) -> None:
        super().__init__()
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        base = mobilenet_v3_small(weights=weights)
        self.features = base.features
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

        self.quality_classifier = nn.Sequential(
            nn.Linear(EMBEDDING_DIM, 128), nn.Hardswish(),
            nn.Dropout(p=dropout), nn.Linear(128, len(QUALITY_CLASSES)),
        )
        self.binary_classifier = nn.Sequential(
            nn.Linear(EMBEDDING_DIM, 128), nn.Hardswish(),
            nn.Dropout(p=dropout), nn.Linear(128, len(BINARY_HEADS)),
        )

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        return torch.flatten(self.pool(self.features(x)), 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        emb = self.embed(x)
        return self.quality_classifier(emb), self.binary_classifier(emb)


def load_checkpoint_state(path: str | Path, map_location: str = "cpu"):
    """Load a weights file, accepting both on-disk formats.

    Training scripts save ``{"model": state_dict, "epoch": n, "history": [...]}``
    so an interrupted run can resume; older artifacts are bare state dicts. An
    inference loader that understands only one of the two breaks the moment a
    fresh checkpoint appears — which is exactly what happened here (the batch
    scan tests failed with 'unexpected key(s): model, epoch, ...'). Both formats
    are therefore handled in one place.
    """
    state = torch.load(str(path), map_location=map_location, weights_only=False)
    if isinstance(state, dict) and isinstance(state.get("model"), dict):
        return state["model"]
    return state


def load_attribute_model(path: str | None = None, pretrained: bool = False,
                         map_location: str = "cpu") -> OnionAttributeNet:
    """Load weights if a path is given (and exists), else return a fresh net."""
    net = OnionAttributeNet(pretrained=pretrained)
    if path:
        net.load_state_dict(load_checkpoint_state(path, map_location))
    net.eval()
    return net


def describe() -> Dict[str, object]:
    """Model card facts that are true without any training run."""
    return {
        "architecture": "MobileNetV3-Small + quality_class head + binary head",
        "embedding_dim": EMBEDDING_DIM,
        "quality_classes": QUALITY_CLASSES,
        "binary_heads": BINARY_HEADS,
        "unsupported_attributes": [
            "damaged", "undersized", "bruising", "cleanliness",
            "open_neck", "shelf_life_days",
        ],
        "input_size": [224, 224],
        "notes": [
            "Only heads with real labels in the tracked dataset are exposed.",
            "Uses torchvision MobileNetV3-Small weights (BSD-3-Clause).",
        ],
    }
