"""Unified app-facing API (`combined_scan`).

The mobile app and the backend call exactly these functions, so the same code
path is exercised in the demo, the tests and the product:

    scan_onion_image(image)            -> detect + classify + policy decision
    classify_vision(image)             -> shared vision contract
    classify_acoustic(audio)           -> shared acoustic contract
    fuse_results(vision, acoustic)     -> shared fusion contract
    record_ambient_baseline(wav)       -> ambient noise score + guidance
    run_phone_acoustic_test(...)       -> guided capture (chirp, tap fallback)
    save_scan_result(result)           -> offline-first journal write

Aliases matching the app contract (`scanOnionImage`, `fuseResults`, ...) are
provided at the bottom for Kotlin/JS bridges that use camelCase.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.grading.policy import Policy, active_policy            # noqa: E402

__all__ = [
    "scan_onion_image", "scan_tray_batch", "deep_scan_onion",
    "classify_vision", "classify_acoustic", "fuse_results",
    "record_ambient_baseline", "run_phone_acoustic_test",
    "save_scan_result", "scanOnionImage", "fuseResults",
]


def _policy(policy: Optional[Any]) -> Policy:
    if policy is None:
        return active_policy()
    if isinstance(policy, Policy):
        return policy
    return active_policy(str(policy))


# --------------------------------------------------------------------------
# Mode A — batch
# --------------------------------------------------------------------------
def scan_tray_batch(image_paths: Sequence[str], policy: Optional[Any] = None,
                    center_id: str = "MH-NSK", inspector_id: str = "INSP-001",
                    batch_id: Optional[str] = None,
                    lot_id: Optional[str] = None,
                    **kwargs: Any) -> Dict[str, Any]:
    """Quick Batch Scan over one or more tray images."""
    from inference.batch_scan import scan_batch
    return scan_batch(list(image_paths), _policy(policy), center_id=center_id,
                      inspector_id=inspector_id, batch_id=batch_id,
                      lot_id=lot_id, **kwargs)


def scan_onion_image(image_path: str, policy: Optional[Any] = None,
                     **kwargs: Any) -> Dict[str, Any]:
    """Single-image scan: detect + classify + decide (no acoustic)."""
    from inference.batch_scan import scan_image
    result = scan_image(image_path, _policy(policy), **kwargs)
    if result.get("onions"):
        first = result["onions"][0]
        return {
            "status": result["status"],
            "is_onion": result["status"] == "success",
            "onion": first,
            "decision": first["decision"],
            "capture_quality": result.get("capture_quality"),
            "warnings": result.get("warnings", []),
        }
    return {
        "status": result["status"],
        "is_onion": False,
        "onion": None,
        "decision": None,
        "capture_quality": result.get("capture_quality"),
        "warnings": result.get("warnings", []),
    }


# --------------------------------------------------------------------------
# Mode B — deep scan
# --------------------------------------------------------------------------
def deep_scan_onion(views: Dict[str, str], policy: Optional[Any] = None,
                    audio_path: Optional[str] = None,
                    **kwargs: Any) -> Dict[str, Any]:
    from inference.deep_scan import scan_onion
    return scan_onion(views, _policy(policy), audio_path=audio_path, **kwargs)


def classify_vision(image_path: str, model_path: Optional[str] = None,
                    detector_instances: Optional[list] = None) -> Dict[str, Any]:
    from inference.vision_inference import classify_vision as _cv
    return _cv(image_path, model_path=model_path,
               detector_instances=detector_instances)


def classify_acoustic(audio_path: str,
                      model_path: Optional[str] = None,
                      capture_method: Optional[str] = None) -> Dict[str, Any]:
    from inference.acoustic_inference import classify_acoustic as _ca
    return _ca(audio_path, model_path=model_path,
               capture_method=capture_method)


def fuse_results(vision_result: Dict[str, Any],
                 acoustic_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from src.fusion.fusion import fuse_results as _fr
    return _fr(vision_result, acoustic_result)


# --------------------------------------------------------------------------
# Phone capture
# --------------------------------------------------------------------------
def record_ambient_baseline(wav_path: str) -> Dict[str, Any]:
    """Measure the room's noise floor from a short pre-measurement recording."""
    from src.acoustic.loading import load_wav
    from src.mobile.capture_protocol import begin_session

    try:
        sr, samples = load_wav(wav_path)
    except Exception as exc:
        return {"ok": False, "reason": f"could not read baseline: {exc}",
                "guidance": "record ~1 s of room silence and try again"}
    session = begin_session(ambient_signal=samples)
    session["sample_rate_hz"] = sr
    session["baseline_path"] = str(wav_path)
    return session


def run_phone_acoustic_test(record_response: "callable",
                            device_model: str, os_version: str,
                            sample_rate_hz: int,
                            use_chirp: bool = True,
                            recorded_volume_setting: Optional[str] = None,
                            model_path: Optional[str] = None) -> Dict[str, Any]:
    """Guided phone-only acoustic measurement (chirp, then tap fallback)."""
    from src.mobile.capture_protocol import (build_capture_metadata,
                                             measure_onion, validate_device_metadata)
    from inference.acoustic_inference import classify_acoustic

    metadata = build_capture_metadata(device_model, os_version, sample_rate_hz,
                                      capture_method="phone_chirp" if use_chirp
                                      else "phone_tap",
                                      recorded_volume_setting=recorded_volume_setting)
    missing = validate_device_metadata(metadata)
    if missing:
        return {"ok": False, "status": "invalid_input",
                "reason": f"missing device metadata: {missing}"}

    measurement = measure_onion(record_response, metadata, use_chirp=use_chirp)
    if not measurement.get("ok"):
        return {"ok": False, "status": "retest_required",
                "measurement": measurement,
                "audio_quality": measurement.get("attempts"),
                "reason": measurement.get("reason", "acoustic measurement failed")}

    audio_path = measurement.get("audio_path")
    acoustic = classify_acoustic(
        audio_path, model_path=model_path,
        capture_method=("phone_chirp" if use_chirp else "phone_tap")) \
        if audio_path else None
    return {"ok": True, "status": "valid", "measurement": measurement,
            "acoustic": acoustic, "device": metadata}


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------
def save_scan_result(result: Dict[str, Any], center_id: Optional[str] = None,
                     device_id: str = "",
                     store_root: Optional[str] = None) -> Dict[str, Any]:
    """Persist a scan synchronously to the offline journal (no network I/O)."""
    from src.mobile.offline_store import ScanStore

    center = center_id or (result.get("batch") or {}).get("center_id") or "UNKNOWN"
    kwargs: Dict[str, Any] = {"device_id": device_id}
    if store_root:
        kwargs["root"] = store_root
    store = ScanStore(center, **kwargs)
    record = store.save_scan_result(result)
    return {"record_id": record.record_id, "journal": str(store.journal),
            "sync_state": record.sync_state}


# camelCase aliases for native bridges.
scanOnionImage = scan_onion_image
fuseResults = fuse_results
