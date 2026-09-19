"""Acoustic inference: DSP features + baseline model, honest statuses.

Return contract (mirrors the shared fusion interface):

    {
      "status": "valid" | "retest_required" | "model_not_trained",
      "internal_defect_probability": float | None,
      "confidence": float | None,
      "audio_quality": {...quality report...},
      "features": {...} | None,
      "model_version": str,
      "dataset_type": [str],          # from the artifact's own metadata
      "ground_truth_verified": bool,  # True only for verified onion audio
      "research_only": bool,          # True whenever grading_eligible is False
      "grading_eligible": bool,       # the single gate used by fusion/grading
      "warnings": [...]
    }

The model shipped/trained today is a SYNTHETIC demo; the status text and
model card never describe it as an onion internal-defect model. Crucially,
``status: "valid"`` means **the recording was good enough to analyse** — it is
not a claim that the model is validated. ``grading_eligible`` is the only flag
that may let acoustic evidence influence a procurement decision, and it stays
``False`` until a model carries verified onion ground truth (see
``src/common/contracts.py::acoustic_grading_eligible``).
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


def _load_signal(audio_path: str) -> "np.ndarray":
    """Load the raw signal for the impact gate (features already extracted)."""
    from src.acoustic.loading import load_wav
    _, samples = load_wav(audio_path)
    return samples


def model_dataset_types(artifact: Optional[Dict[str, Any]]) -> list:
    """Dataset classes recorded **by the artifact itself** (never inferred)."""
    if not artifact:
        return []
    raw = (artifact.get("metadata") or {}).get("dataset_type") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(item) for item in raw] or ["unknown"]


def _status_block(status: str, quality: Dict[str, Any],
                  features: Optional[Dict[str, Any]],
                  dataset_types: list, model_version: str,
                  warnings: list, probability: Optional[float] = None,
                  confidence: Optional[float] = None) -> Dict[str, Any]:
    """One construction point, so every return carries the same flags."""
    from src.common.contracts import (VERIFIED_ONION_ACOUSTIC,
                                      acoustic_grading_eligible)
    ground_truth_verified = VERIFIED_ONION_ACOUSTIC in dataset_types
    payload = {
        "status": status,
        "internal_defect_probability": probability,
        "confidence": confidence,
        "audio_quality": quality,
        "features": features,
        "model_version": model_version,
        "dataset_type": dataset_types,
        "ground_truth_verified": ground_truth_verified,
        "research_only": not ground_truth_verified,
        "warnings": list(warnings),
    }
    payload["grading_eligible"] = acoustic_grading_eligible(payload)
    return payload


def classify_acoustic(audio_path: str, model_path: Optional[str] = None) -> Dict[str, Any]:
    """Run quality gates + feature extraction + baseline model on one WAV."""
    artifact = _load_model(model_path)
    warnings: list[str] = []
    dataset_types = model_dataset_types(artifact)

    result = analyze_file(audio_path)
    quality = result["quality"]
    if result["features"] is None:
        return _status_block(
            "retest_required", quality, None, dataset_types, MODEL_VERSION,
            warnings + [result.get("error", "quality gates failed")])

    # ------------------------------------------------------------------
    # IMPACT-PRESENCE GATE (runs BEFORE the model).
    # A prediction on audio containing no tap/chirp response is a false
    # answer — the model only describes impact-response audio, so it must
    # never see anything else. This is the fix for "room noise got a
    # defect prediction".
    # ------------------------------------------------------------------
    from src.acoustic.impact_gate import check_impact_present
    sr = int(result.get("sample_rate_hz", 0))
    sig = _load_signal(audio_path)
    gate = check_impact_present(sig, sr,
                                noise_floor_rms=(quality or {}).get(
                                    "ambient_noise_rms"))
    if not gate["passed"]:
        return _status_block(
            "no_impact_detected", quality, result["features"], dataset_types,
            MODEL_VERSION,
            warnings + ["no tap/chirp excitation found in recording: "
                        + "; ".join(gate["reasons"])])

    if artifact is None:
        return _status_block(
            "model_not_trained", quality, result["features"], dataset_types,
            "none",
            warnings + [
                "No trained acoustic model found; run training/train_acoustic.py. "
                "No prediction is made."])

    import numpy as np
    model = artifact["model"]
    if not warnings and "synthetic" in dataset_types:
        warnings.append(
            "Model was trained on SYNTHETIC audio (demo). Its internal-defect "
            "probability is not an onion measurement and cannot change a grade.")

    x = np.asarray([[result["features"][k] for k in artifact["feature_order"]]],
                   dtype=np.float32)
    prob = float(model.predict_proba(x)[0][1])
    snr = float(quality["snr_db"])

    # Confidence: model margin dampened by recording quality.
    margin = abs(prob - 0.5) * 2.0
    quality_factor = min(1.0, snr / HIGH_QUALITY_SNR_DB) * float(quality["quality_score"])
    confidence = round(min(1.0, 0.5 * margin + 0.5 * quality_factor), 3)

    if confidence < CONFIDENCE_FLOOR:
        return _status_block(
            "retest_required", quality, result["features"], dataset_types,
            MODEL_VERSION,
            warnings + [
                f"confidence {confidence} below floor {CONFIDENCE_FLOOR}; "
                "retest required rather than a confident guess"],
            probability=round(prob, 4), confidence=confidence)

    return _status_block(
        "valid", quality, result["features"], dataset_types, MODEL_VERSION,
        warnings, probability=round(prob, 4), confidence=confidence)


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audio_path")
    args = ap.parse_args()
    print(json.dumps(classify_acoustic(args.audio_path), indent=2))
