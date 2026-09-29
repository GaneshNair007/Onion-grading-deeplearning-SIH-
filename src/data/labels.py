"""Explicit category → model-label mapping. No invented labels.

Every mapping below is traceable to a dataset category string that exists in
the tracked COCO annotations (audit §7). Unmapped categories become
``unknown`` and are excluded from training rather than guessed.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set

UNKNOWN = "unknown"

#: Per source_group: source category name → task targets.
CATEGORY_MAPPING: Dict[str, Dict[str, Dict[str, object]]] = {
    # Roboflow "Onion Grading" v7 (CC BY 4.0) — commercial quality classes.
    "onion-grading-coco-segmentation": {
        "Onions": {"is_onion": True},
        "Class 1": {"is_onion": True, "quality_class": "class_1"},
        "Class 2": {"is_onion": True, "quality_class": "class_2"},
        "Extra Class": {"is_onion": True, "quality_class": "extra_class"},
        # NOTE: "Reject" is a commercial grade label. It is NOT documented by
        # the source as "rotten", so it maps only to the reject class and is
        # never silently treated as rot.
        "Reject": {"is_onion": True, "quality_class": "reject"},
    },
    # Roboflow "onions" v1 (Public Domain) — defect classes.
    "onion-coco-mmdetection": {
        "rotten": {"is_onion": True, "rotten": 1},
        "sprout": {"is_onion": True, "sprout": 1},
    },
}

#: Per source_group licence status. `unresolved` sources are excluded from
#: training manifests by the registry.
LICENSE_STATUS: Dict[str, Dict[str, object]] = {
    "onion-grading-coco-segmentation": {
        "license": "CC BY 4.0",
        "license_status": "verified",
        "training_allowed": True,
        "source": "Roboflow README.dataset.txt (tracked in dataset/)",
    },
    "onion-coco-mmdetection": {
        "license": "Public Domain",
        "license_status": "verified",
        "training_allowed": True,
        "source": "Roboflow README.dataset.txt (tracked in dataset/)",
    },
    "onion-leaves-and-bulb": {
        "license": "License not detected",
        "license_status": "unresolved",
        "training_allowed": False,
        "source": "No licence file in source dataset (dataset/README.md)",
    },
}


def map_categories(source_group: str,
                   category_names: List[str]) -> Dict[str, object]:
    """Map a set of source category names to model targets.

    Returns ``{"targets": {...}, "unknown": [...]}``. Absent targets are
     omitted: callers must not substitute zeros for "no label" when the image
    simply was not annotated for that task.
    """
    mapping = CATEGORY_MAPPING.get(source_group, {})
    targets: Dict[str, object] = {}
    unknown: List[str] = []
    for name in category_names:
        entry = mapping.get(name)
        if entry is None:
            unknown.append(name)
            continue
        for key, value in entry.items():
            # Explicit label outranks the implicit presence flag.
            if key == "is_onion" and targets.get("is_onion") is True:
                continue
            targets[key] = value
    return {"targets": targets, "unknown": unknown}


def supported_tasks(source_group: str) -> Set[str]:
    """Task keys this source can actually supervise."""
    tasks: Set[str] = set()
    for entry in CATEGORY_MAPPING.get(source_group, {}).values():
        tasks.update(k for k in entry if k != "is_onion")
    return tasks


def quality_class_index(name: str) -> Optional[int]:
    from src.vision.model import QUALITY_CLASSES
    return QUALITY_CLASSES.index(name) if name in QUALITY_CLASSES else None
