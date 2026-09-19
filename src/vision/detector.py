"""Onion instance detector — inference wrapper.

Single class: `onion`. Architecture is defined here so training and inference
cannot drift apart (`training/train_detector.py` imports `build_detector`).

Documented accuracy limitation: Faster R-CNN produces **boxes, not masks**,
so the pipeline cannot yet compute per-onion defect *area* percentages. The
grading engine treats `damage_surface_pct` as an unavailable measurement and
escalates to manual review when a policy requires it (see
src/grading/engine.py) instead of inventing a number.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DETECTOR_DIR = PROJECT_ROOT / "models" / "vision" / "detector"
REGISTRY_PATH = PROJECT_ROOT / "models" / "registry.json"
MODEL_ID = "vision-detector-v0.1"
SCORE_THRESHOLD = 0.5
MIN_SIZE = 480


def build_detector(num_classes: int = 2, pretrained: bool = True):
    """Construct the detector (single source of truth for architecture)."""
    from torchvision.models.detection import (
        FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
        fasterrcnn_mobilenet_v3_large_320_fpn)
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    weights = (FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.COCO_V1
               if pretrained else None)
    model = fasterrcnn_mobilenet_v3_large_320_fpn(weights=weights)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


def resolve_detector(explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    if REGISTRY_PATH.exists():
        try:
            entry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")) \
                .get("models", {}).get(MODEL_ID)
            if entry:
                p = PROJECT_ROOT / entry["artifact_path"]
                if p.exists():
                    return p
        except (json.JSONDecodeError, KeyError):
            pass
    candidates = sorted(DETECTOR_DIR.glob("*.pt")) if DETECTOR_DIR.exists() else []
    return candidates[-1] if candidates else None


_cache: Dict[str, Any] = {}


def _load(artifact: Path):
    """Load the detector, accepting both checkpoint formats.

    Training writes ``{"model": state_dict, "epoch": ...}``; older artifacts are
    bare state dicts. See ``src.vision.model.load_checkpoint_state``.
    """
    from src.vision.model import load_checkpoint_state
    key = str(artifact)
    if key not in _cache:
        model = build_detector(pretrained=False)
        model.load_state_dict(load_checkpoint_state(key))
        model.eval()
        _cache[key] = model
    return _cache[key]


def detect_onions(image_path: str, model_path: Optional[str] = None,
                  score_threshold: float = SCORE_THRESHOLD,
                  max_long_side: int = MIN_SIZE) -> Dict[str, Any]:
    """Detect onion instances in one image.

    Returns ``{"status", "instances": [{bbox, confidence, instance_id}], ...}``.
    ``status`` is ``model_unavailable`` when no detector artifact is present —
    the caller must not fabricate detections.
    """
    artifact = resolve_detector(model_path)
    if artifact is None:
        return {
            "status": "model_unavailable",
            "instances": [],
            "warnings": [
                "No detector artifact found. Train with "
                "`python training/train_detector.py`.",
            ],
        }

    import torch
    from PIL import Image
    from torchvision.transforms import functional as F

    model = _load(artifact)
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    scale = 1.0
    if max(w, h) > max_long_side:
        scale = max_long_side / max(w, h)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))

    with torch.no_grad():
        outputs = model([F.to_tensor(img)])[0]

    instances: List[Dict[str, Any]] = []
    for i, (box, score, label) in enumerate(zip(outputs["boxes"].numpy(),
                                                outputs["scores"].numpy(),
                                                outputs["labels"].numpy())):
        if float(score) < score_threshold or int(label) != 1:
            continue
        bx1, by1, bx2, by2 = [float(v) / scale for v in box]  # back to original scale
        instances.append({
            "instance_id": f"inst_{i:03d}",
            "bbox": [round(bx1, 1), round(by1, 1), round(bx2, 1), round(by2, 1)],
            "bbox_xywh": [round(bx1, 1), round(by1, 1),
                          round(bx2 - bx1, 1), round(by2 - by1, 1)],
            "confidence": round(float(score), 4),
            "mask": None,  # Faster R-CNN yields boxes only (documented limitation)
        })

    return {
        "status": "success",
        "image_size": [int(w), int(h)],
        "instances": instances,
        "onion_count": len(instances),
        "score_threshold": score_threshold,
        "model_version": MODEL_ID,
        "warnings": [
            "Detector returns boxes, not masks; defect-area percentages are "
            "therefore unavailable and marked as such downstream.",
        ],
    }


def estimate_occlusion(instances: List[Dict[str, Any]], image_size: List[int]) -> float:
    """Fraction of the image area covered by onion boxes (a crude density proxy).

    Not a true occlusion measure: overlapping boxes are counted once, and the
    value is reported only to trigger the 'spread the onions out' guidance.
    """
    if not instances or not image_size:
        return 0.0
    w, h = image_size
    if w <= 0 or h <= 0:
        return 0.0
    mask = np.zeros((int(h), int(w)), dtype=bool)
    for inst in instances:
        x, y, bw, bh = inst["bbox_xywh"]
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(int(w), int(x + bw)), min(int(h), int(y + bh))
        if x1 > x0 and y1 > y0:
            mask[y0:y1, x0:x1] = True
    return float(mask.mean())
