"""Acoustic inference: DSP features + baseline model, honest statuses.

Return contract (mirrors the shared fusion interface):

    {
      "status": "valid" | "retest_required" | "model_not_trained",
      "internal_defect_probability": float | None,
      "confidence": float | None,
      "audio_quality": {...quality report...},
      "features": {...} | None,
      "model_version": str,
      "warnings": [...]
    }

The model shipped/trained today is a SYNTHETIC demo; the status text and
model card never describe it as an onion internal-defect model.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.acoustic.features import analyze_file, FEATURE_ORDER  # noqa: E402

MODEL_PATH = PROJECT_ROOT / "models" / "acoustic" / "acoustic_baseline.joblib"
MODEL_VERSION = "acoustic-v1-synthetic-demo"
CONFIDENCE_FLOOR = 0.55
HIGH_QUALITY_SNR_DB = 12.0


def _load_model(model_path: Optional[str] = None):
    path = Path(model_path) if model_path else MODEL_PATH
    if not path.exists():
        return None
    import joblib
    return joblib.load(path)


def classify_acoustic(audio_path: str, model_path: Optional[str] = None) -> Dict[str, Any]:
    """Run quality gates + feature extraction + baseline model on one WAV."""
    artifact = _load_model(model_path)
    warnings: list[str] = []

    result = analyze_file(audio_path)
    quality = result["quality"]
    if result["features"] is None:
        return {
            "status": "retest_required",
            "internal_defect_probability": None,
            "confidence": None,
            "audio_quality": quality,
            "features": None,
            "model_version": MODEL_VERSION,
            "warnings": warnings + [result.get("error", "quality gates failed")],
        }

    if artifact is None:
        return {
            "status": "model_not_trained",
            "internal_defect_probability": None,
            "confidence": None,
            "audio_quality": quality,
            "features": result["features"],
            "model_version": "none",
            "warnings": warnings + [
                "No trained acoustic model found; run training/train_acoustic.py. "
                "No prediction is made."],
        }

    import numpy as np
    model = artifact["model"]
    if artifact.get("metadata", {}).get("dataset_type") == ["synthetic"]:
        warnings.append(
            "Model was trained on SYNTHETIC audio (demo). Its internal-defect "
            "probability is not an onion measurement.")

    x = np.asarray([[result["features"][k] for k in artifact["feature_order"]]],
                   dtype=np.float32)
    prob = float(model.predict_proba(x)[0][1])
    snr = float(quality["snr_db"])

    # Confidence: model margin dampened by recording quality.
    margin = abs(prob - 0.5) * 2.0
    quality_factor = min(1.0, snr / HIGH_QUALITY_SNR_DB) * float(quality["quality_score"])
    confidence = round(min(1.0, 0.5 * margin + 0.5 * quality_factor), 3)

    if confidence < CONFIDENCE_FLOOR:
        return {
            "status": "retest_required",
            "internal_defect_probability": round(prob, 4),
            "confidence": confidence,
            "audio_quality": quality,
            "features": result["features"],
            "model_version": MODEL_VERSION,
            "warnings": warnings + [
                f"confidence {confidence} below floor {CONFIDENCE_FLOOR}; "
                "retest required rather than a confident guess"],
        }

    return {
        "status": "valid",
        "internal_defect_probability": round(prob, 4),
        "confidence": confidence,
        "audio_quality": quality,
        "features": result["features"],
        "model_version": MODEL_VERSION,
        "warnings": warnings,
    }


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audio_path")
    args = ap.parse_args()
    print(json.dumps(classify_acoustic(args.audio_path), indent=2))
