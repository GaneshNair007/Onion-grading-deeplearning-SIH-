"""Vision inference — self-contained, real-model based.

No import from the untracked `backend/` directory (audit finding P0.1). Uses
`src/vision/model.py` (`OnionAttributeNet`), whose heads exist only for tasks
with real labels: 4-class commercial quality + rotten/sprout binaries.

Deliberately absent (no labels exist, so nothing is claimed):
`damaged`, `undersized`, `bruising`, `shelf_life_days` / freshness.

Artifact resolution order:
1. `models/registry.json` entry `vision-attributes-v0.1` (artifact_path)
2. newest `models/vision/attributes/*.pt`
3. `--model` override

If no artifact is present the call returns an explicit `model_unavailable`
status instead of guessing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

ATTRIBUTE_DIR = PROJECT_ROOT / "models" / "vision" / "attributes"
REGISTRY_PATH = PROJECT_ROOT / "models" / "registry.json"
REFERENCE_PATH = PROJECT_ROOT / "models" / "vision" / "rejection_reference.npz"

# Config-driven (config/models.yaml); the literals are only load-time fallbacks.
from src.common.config import get_setting  # noqa: E402

UNCERTAIN_THRESHOLD = float(get_setting("vision_confidence_threshold", 0.55))
DEFECT_THRESHOLD = float(get_setting("vision_defect_threshold", 0.50))
MODEL_ID = "vision-attributes-v0.1"

try:
    import torch
    from PIL import Image
    from torchvision import transforms

    from src.vision.model import (BINARY_HEADS, OnionAttributeNet,
                                  QUALITY_CLASSES)
    from src.vision.rejection import load_reference
    _TORCH_OK = True
    _IMPORT_ERROR = ""
except Exception as _exc:  # pragma: no cover - environment dependent
    _TORCH_OK = False
    _IMPORT_ERROR = str(_exc)


def resolve_artifact(explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    if REGISTRY_PATH.exists():
        try:
            registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            entry = registry.get("models", {}).get(MODEL_ID)
            if entry:
                p = PROJECT_ROOT / entry["artifact_path"]
                if p.exists():
                    return p
        except (json.JSONDecodeError, KeyError):
            pass
    candidates = sorted(ATTRIBUTE_DIR.glob("*.pt")) if ATTRIBUTE_DIR.exists() else []
    return candidates[-1] if candidates else None


def _model_version(artifact: Optional[Path]) -> str:
    if artifact is None:
        return "none"
    card = artifact.parent / "model_card.json"
    if card.exists():
        try:
            return json.loads(card.read_text(encoding="utf-8")).get("model_id", MODEL_ID)
        except json.JSONDecodeError:
            pass
    return MODEL_ID


def _transforms(input_size: int):
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def _derive_label(quality_class: str, q_conf: float,
                  defects: Dict[str, Dict[str, Any]]) -> str:
    """Map model outputs to one visible-condition label + reason codes."""
    if defects["rotten"]["detected"]:
        return "visibly_rotten"
    if defects["sprout"]["detected"]:
        return "sprouted"
    if quality_class == "reject" and q_conf >= UNCERTAIN_THRESHOLD:
        return "reject_grade"
    if q_conf < UNCERTAIN_THRESHOLD:
        return "uncertain"
    return "sound"


_NET_CACHE: Dict[str, Any] = {}


def _load_net(artifact: Path):
    """Cache the loaded network: batch scanning calls this per onion."""
    key = str(artifact)
    if key not in _NET_CACHE:
        from src.vision.model import load_checkpoint_state
        net = OnionAttributeNet(pretrained=False)
        # Accepts both a raw state dict and a training checkpoint dict.
        net.load_state_dict(load_checkpoint_state(key))
        net.eval()
        _NET_CACHE[key] = net
    return _NET_CACHE[key]


def _input_size_for(artifact: Path) -> int:
    card_path = artifact.parent / "model_card.json"
    if card_path.exists():
        try:
            return int(json.loads(card_path.read_text(encoding="utf-8"))
                       .get("input_size", [128, 128])[0])
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return 128


def classify_pil_image(img: "Image.Image",
                       model_path: Optional[str] = None,
                       detector_instances: Optional[list] = None,
                       artifact: Optional[Path] = None) -> Dict[str, Any]:
    """Classify an in-memory image (used for per-onion crops in batch scan)."""
    if not _TORCH_OK:
        return _unavailable_result(
            f"torch/PIL unavailable in this environment: {_IMPORT_ERROR}")
    artifact = artifact or resolve_artifact(model_path)
    if artifact is None:
        return _unavailable_result(
            "No attribute-model artifact found. Train it with "
            "`python training/train_attribute_model.py` (real labels only).")
    return _run_net(img, artifact, detector_instances)


def _unavailable_result(reason: str) -> Dict[str, Any]:
    return {
        "is_onion": None,
        "vision": {"label": "unavailable", "confidence": 0.0, "defects": {},
                   "model_version": "none"},
        "research_outputs": {"quality_class": None, "quality_confidence": None,
                            "note": "RESEARCH-ONLY HEAD, NOT USED BY PROCUREMENT ENGINE"},
        "status": "model_unavailable",
        "warnings": [reason],
    }


def _run_net(img: "Image.Image", artifact: Path,
             detector_instances: Optional[list]) -> Dict[str, Any]:
    input_size = _input_size_for(artifact)
    net = _load_net(artifact)
    tensor = _transforms(input_size)(img.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        emb = net.embed(tensor)
        q_logits, b_logits = net(tensor)
        q_probs = torch.softmax(q_logits, dim=1)[0]
        b_probs = torch.sigmoid(b_logits)[0]

    quality_class = QUALITY_CLASSES[int(q_probs.argmax())]
    q_conf = float(q_probs.max())
    defects = {
        name: {"detected": bool(b_probs[i] >= DEFECT_THRESHOLD),
               "confidence": round(float(b_probs[i]), 4)}
        for i, name in enumerate(BINARY_HEADS)
    }

    reference = load_reference(REFERENCE_PATH)
    embedding = emb[0].cpu().numpy().astype(np.float64)
    if detector_instances is not None:
        from src.vision.rejection import detect_with_gate
        gate = detect_with_gate(detector_instances, embedding, reference)
    elif reference is not None:
        from src.vision.rejection import detect_with_gate
        gate = detect_with_gate(None, embedding, reference,
                                detector_available=False)
    else:
        gate = {"is_onion": None, "gate": "none",
                "reasons": ["no_rejection_gate_available"]}

    label = _derive_label(quality_class, q_conf, defects)
    confidence = max(q_conf, max(d["confidence"] for d in defects.values()))

    warnings = [
        "Attribute model trained on Roboflow-labelled photographs; "
        "not field-validated. Shelf-life/decay is NOT predicted (no labels).",
    ]
    if gate.get("gate") == "embedding_ood":
        warnings.append(
            "Onion/non-onion decision uses the embedding OOD fallback "
            "(calibrated on real onion images only; artificial negatives only).")
    if gate.get("gate") == "none":
        warnings.append(
            "No rejection gate available: install an onion detector artifact "
            "or build the embedding reference.")
    if label == "uncertain":
        warnings.append(
            f"quality confidence {q_conf:.2f} below threshold {UNCERTAIN_THRESHOLD}")

    return {
        "is_onion": gate.get("is_onion"),
        "vision": {
            "label": label,
            "confidence": round(float(confidence), 4),
            "defects": defects,
            "freshness_score": None,  # not modelled: no longitudinal labels
            "model_version": _model_version(artifact),
            "artifact": str(artifact),
            "embedding_dim": int(embedding.shape[0]),
        },
        # RESEARCH-ONLY HEAD -- NOT USED BY THE PROCUREMENT ENGINE.
        # The 4-class commercial head scores macro-F1 ~0.31 on leak-free data
        # (docs/MODEL_CARDS.md). It is kept for comparison and isolated here so
        # no production path can read it by accident; a test enforces that the
        # grading and scan modules never reference it.
        "research_outputs": {
            "quality_class": quality_class,
            "quality_confidence": round(q_conf, 4),
            "note": ("RESEARCH-ONLY HEAD, NOT USED BY PROCUREMENT ENGINE "
                     "(macro-F1 ~0.31 on the leak-free split)"),
        },
        "rejection": gate,
        "status": "success",
        "warnings": warnings,
    }


def classify_vision(image_path: str, model_path: Optional[str] = None,
                    detector_instances: Optional[list] = None) -> Dict[str, Any]:
    """Run the real attribute model on one image file.

    `detector_instances` (optional) is the output of the onion detector for
    this image; when supplied, the detector gate decides `is_onion`.
    """
    if not _TORCH_OK:
        return {
            "is_onion": None,
            "vision": {"label": "unavailable", "confidence": 0.0, "defects": {},
                       "model_version": "none"},
            "research_outputs": {
                "quality_class": None, "quality_confidence": None,
                "note": "RESEARCH-ONLY HEAD, NOT USED BY PROCUREMENT ENGINE"},
            "status": "model_unavailable",
            "warnings": [f"torch/PIL unavailable in this environment: {_IMPORT_ERROR}"],
        }

    artifact = resolve_artifact(model_path)
    if artifact is None:
        return _unavailable_result(
            "No attribute-model artifact found. Train it with "
            "`python training/train_attribute_model.py` (real labels only).")

    img = Image.open(image_path)
    return classify_pil_image(img, model_path=model_path,
                              detector_instances=detector_instances,
                              artifact=artifact)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image_path")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    print(json.dumps(classify_vision(args.image_path, args.model), indent=2))
