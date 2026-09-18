"""Phone-only acoustic capture: guided session logic and device metadata.

This module is the framework-neutral core of the mobile capture flow
(master plan Architecture A). A native app (Android/Kotlin, Flutter, React
Native) implements the actual audio I/O with platform APIs and calls these
functions; a plain web client cannot replicate native speaker/mic control,
so it uses the documented API boundary (backend FastAPI) instead — browser
microphone behaviour is explicitly NOT treated as native capture.

Session steps exposed here:
  1. ambient baseline recording (returned with an ambient noise score)
  2. chirp playback + recording, or guided standardized tap (fallback)
  3. immediate quality gate -> retest guidance if the signal is poor
  4. feature extraction -> acoustic model input

Device metadata (model, OS, sample rate, volume setting, ambient score,
capture method) is collected into the sidecar JSON per
dataset-acoustic/metadata_schema.json, because phone speakers/microphones
are NOT consistent across devices.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Chirp design shared with the synthetic generator and app playback.
CHIRP_F0_HZ = 100.0
CHIRP_F1_HZ = 8000.0
CHIRP_DURATION_S = 1.0
RECORDING_DURATION_S = 1.6
MAX_ATTEMPTS = 3
AMBIENT_SCORE_LIMIT = 0.02  # RMS of ambient baseline; above this, ask user to quiet down


REQUIRED_DEVICE_FIELDS = ["device_model", "os_version", "sample_rate_hz"]


def build_capture_metadata(device_model: str, os_version: str,
                           sample_rate_hz: int,
                           capture_method: str = "phone_chirp",
                           recorded_volume_setting: Optional[str] = None,
                           notes: str = "") -> Dict[str, Any]:
    """Device provenance block required for every phone recording."""
    return {
        "device_model": device_model,
        "os_version": os_version,
        "sample_rate_hz": sample_rate_hz,
        "capture_method": capture_method,
        "recorded_volume_setting": recorded_volume_setting,
        "ambient_noise_score": None,   # filled by begin_session
        "recorded_at": None,           # filled by the app at record time
        "notes": notes,
    }


def validate_device_metadata(meta: Dict[str, Any]) -> List[str]:
    missing = [f for f in REQUIRED_DEVICE_FIELDS if not meta.get(f)]
    return missing


def begin_session(ambient_signal: Optional[Any] = None,
                  ambient_rms: Optional[float] = None) -> Dict[str, Any]:
    """Step 1-2: accept an ambient baseline (samples or a precomputed RMS)
    and decide whether the room is quiet enough to continue."""
    if ambient_rms is None:
        if ambient_signal is None:
            return {"ok": False, "reason": "no ambient baseline provided",
                    "guidance": "record ~1 s of room silence first"}
        import numpy as np
        sig = ambient_signal if isinstance(ambient_signal, __import__("numpy").ndarray) \
            else __import__("numpy").array(ambient_signal)
        ambient_rms = float(np.sqrt(np.mean(sig ** 2))) if len(sig) else 0.0

    ok = ambient_rms <= AMBIENT_SCORE_LIMIT
    return {
        "ok": ok,
        "ambient_noise_score": round(ambient_rms, 6),
        "guidance": (None if ok else
                     "ambient noise too high — move to a quieter room or "
                     "move the phone away from appliances, then re-record "
                     "the baseline"),
    }


def measure_onion(record_response: "callable",
                  capture_metadata: Dict[str, Any],
                  use_chirp: bool = True) -> Dict[str, Any]:
    """Steps 3-7: run one controlled measurement.

    record_response(play_chirp: bool) -> (sample_rate, samples) is supplied
    by the platform layer: it must play the chirp (or wait for the guided
    tap) while recording RECORDING_DURATION_S of audio, and return raw mono
    samples. This function checks quality and requests up to MAX_ATTEMPTS
    retests before giving up honestly.
    """
    import numpy as np
    from src.acoustic.quality import check_quality
    from src.acoustic.features import extract_features

    attempts: List[Dict[str, Any]] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        sr, samples = record_response(play_chirp=use_chirp)
        quality = check_quality(samples, sr,
                                expected_duration_s=RECORDING_DURATION_S)
        attempts.append({"attempt": attempt, "recommendation": quality["recommendation"],
                         "snr_db": quality["snr_db"], "issues": quality["issues"]})
        if quality["passed"]:
            features = extract_features(samples, sr)
            return {
                "ok": True,
                "attempts": attempts,
                "sample_rate_hz": sr,
                "capture_metadata": {**capture_metadata,
                                     "ambient_noise_score": None,
                                     "capture_method": "phone_chirp" if use_chirp else "phone_tap"},
                "quality": quality,
                "features": features,
            }
        if not use_chirp:
            return {"ok": False, "attempts": attempts,
                    "reason": "tap measurement failed quality gates; "
                              "manual review of procedure required"}
        use_chirp = False  # fallback: try the standardized tap next
    return {"ok": False, "attempts": attempts,
            "reason": "recording failed quality gates after "
                      f"{MAX_ATTEMPTS} attempts; retest required"}
