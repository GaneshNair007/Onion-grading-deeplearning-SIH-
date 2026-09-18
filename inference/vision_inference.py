"""Vision inference wrapper exposing the project-standard result contract.

Loads the existing OnionVisionNet (backend/app/vision/model.py) weights and
returns the shared interface used by fusion and the demo:

    {
      "is_onion": bool,
      "vision": {"label", "confidence", "defects", "model_version"},
      "warnings": [...]
    }

Honesty note: the currently committed artifact (vision_mobilenet_v1.0.0.pt in
backend/models/artifacts/) was trained on SYNTHETIC PIL-drawn onion images
(backend/scripts/seed_dataset.py), not real photos. It is NOT validated on
real onions. Real COCO-labelled data (Class 1/2/Extra Class/Reject; rotten /
sprout) exists on the `dataset` branch for proper retraining via
training/train_vision.py. No accuracy numbers are claimed here.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
for p in (str(BACKEND_DIR), str(PROJECT_ROOT / "src")):
    if p not in sys.path:
        sys.path.append(p)

MODEL_PATH = BACKEND_DIR / "models" / "artifacts" / "vision_mobilenet_v1.0.0.pt"
MODEL_VERSION = "vision-v1 (synthetic-trained, NOT validated on real onions)"
UNCERTAIN_THRESHOLD = 0.60

try:
    import torch
    from PIL import Image
    from torchvision import transforms
    from app.vision.model import OnionVisionNet, DEFECT_CLASSES
    _TORCH_OK = True
except Exception as _exc:  # torch/PIL optional at import time
    _TORCH_OK = False
    _IMPORT_ERROR = str(_exc)
    transforms = None


def _load_model(model_path: Optional[str] = None):
    if not _TORCH_OK:
        raise RuntimeError(f"torch/PIL unavailable: {_IMPORT_ERROR}")
    net = OnionVisionNet(pretrained=False)
    path = Path(model_path) if model_path else MODEL_PATH
    state = torch.load(str(path), map_location="cpu")
    net.load_state_dict(state)
    net.eval()
    return net


_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]
if _TORCH_OK:
    TRANSFORMS = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


def classify_vision(image_path: str, model_path: Optional[str] = None) -> Dict[str, Any]:
    """Run the vision model and return the shared contract with is_onion."""
    net = _load_model(model_path)
    img = Image.open(image_path).convert("RGB")
    tensor = TRANSFORMS(img).unsqueeze(0)

    with torch.no_grad():
        defect_logits, decay_params = net(tensor)
        probs = torch.sigmoid(defect_logits)[0]

    defects: Dict[str, Dict[str, Any]] = {}
    for name, p in zip(DEFECT_CLASSES, probs.tolist()):
        defects[name] = {"confidence": round(float(p), 4),
                         "is_detected": bool(p >= 0.5)}

    # is_onion heuristic: a synthetic-trained gate. Replacing this with a
    # dedicated onion/non-onion classifier is tracked in models/vision/README.md.
    max_defect = max(probs.tolist())
    is_onion = bool(max_defect < 0.70 or any(d["is_detected"] for d in defects.values()))

    top_name = max(defects, key=lambda k: defects[k]["confidence"])
    top_conf = defects[top_name]["confidence"]
    label = top_name if defects[top_name]["is_detected"] else "sound"
    if top_conf < UNCERTAIN_THRESHOLD and label != "sound":
        label = "uncertain"

    days_mean, days_logvar = [float(v) for v in decay_params[0].tolist()]
    freshness = max(0.0, min(1.0, days_mean / 14.0))

    return {
        "is_onion": is_onion,
        "vision": {
            "label": label,
            "confidence": round(top_conf, 4),
            "defects": defects,
            "freshness_score": round(freshness, 3),
            "model_version": MODEL_VERSION,
        },
        "warnings": [
            "Vision model trained on synthetic images only; not validated on real onions.",
        ],
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image_path")
    args = ap.parse_args()
    import json
    print(json.dumps(classify_vision(args.image_path), indent=2))
