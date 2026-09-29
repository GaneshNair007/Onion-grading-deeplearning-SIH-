"""Recording quality gates for the acoustic pipeline.

A recording must pass every applicable gate before it may be used for
feature extraction or model input. Phones are inconsistent between devices;
these checks exist so unreliable audio yields "retest required" instead of a
confident false decision.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .loading import estimate_ambient_noise

CLIP_ABS_THRESHOLD = 0.995
CLIP_MIN_RUN = 3          # consecutive samples at/above threshold
SILENCE_RMS = 1e-4
MIN_SNR_DB = 6.0
DEFAULT_MIN_DURATION_S = 0.3
DEFAULT_MAX_DURATION_S = 30.0
SUPPORTED_RATES = {8000, 16000, 22050, 32000, 44100, 48000}


def calculate_snr_db(signal: np.ndarray, sr: int,
                     frame_seconds: float = 0.05) -> float:
    """Frame-energy SNR estimate: peak frame vs 15th-percentile frame."""
    frame_len = max(int(sr * frame_seconds), 16)
    n_frames = len(signal) // frame_len
    if n_frames < 2:
        return 0.0
    energies = np.array([
        float(np.mean(signal[i * frame_len:(i + 1) * frame_len] ** 2))
        for i in range(n_frames)
    ])
    noise_energy = float(np.percentile(energies, 15))
    peak_energy = float(np.max(energies))
    if noise_energy <= 1e-12:
        return 40.0
    return float(10.0 * np.log10(max(peak_energy / noise_energy, 1.0)))


def _longest_clip_run(signal: np.ndarray) -> int:
    clipped = np.abs(signal) >= CLIP_ABS_THRESHOLD
    best = run = 0
    for flag in clipped:
        run = run + 1 if flag else 0
        best = max(best, run)
    return best


def check_quality(signal: np.ndarray, sr: int,
                  expected_duration_s: float | None = None,
                  min_duration_s: float = DEFAULT_MIN_DURATION_S,
                  max_duration_s: float = DEFAULT_MAX_DURATION_S,
                  expected_sample_rate: int | None = None) -> Dict[str, object]:
    """Run all quality gates; returns a structured report (never raises)."""
    issues: List[Dict[str, str]] = []

    duration = len(signal) / sr if sr > 0 else 0.0
    peak = float(np.max(np.abs(signal))) if len(signal) else 0.0
    rms = float(np.sqrt(np.mean(signal ** 2))) if len(signal) else 0.0
    noise = estimate_ambient_noise(signal, sr)
    snr_db = calculate_snr_db(signal, sr) if len(signal) else 0.0

    if _longest_clip_run(signal) >= CLIP_MIN_RUN:
        issues.append({"code": "clipping", "severity": "high",
                       "detail": f"peak={peak:.4f} with sustained clipping run"})
    if rms < SILENCE_RMS:
        issues.append({"code": "silence", "severity": "high",
                       "detail": f"rms={rms:.6f} below silence threshold"})
    if duration < min_duration_s:
        issues.append({"code": "too_short", "severity": "high",
                       "detail": f"duration={duration:.3f}s < {min_duration_s}s"})
    if duration > max_duration_s:
        issues.append({"code": "too_long", "severity": "medium",
                       "detail": f"duration={duration:.3f}s > {max_duration_s}s"})
    if expected_duration_s is not None and abs(duration - expected_duration_s) > 0.25 * max(expected_duration_s, 1e-6):
        issues.append({"code": "inconsistent_duration", "severity": "medium",
                       "detail": f"duration={duration:.3f}s, expected ~{expected_duration_s:.3f}s"})
    if sr not in SUPPORTED_RATES:
        issues.append({"code": "invalid_sample_rate", "severity": "medium",
                       "detail": f"{sr} Hz not in supported set {sorted(SUPPORTED_RATES)}"})
    if expected_sample_rate is not None and sr != expected_sample_rate:
        issues.append({"code": "sample_rate_mismatch", "severity": "medium",
                       "detail": f"{sr} Hz != expected {expected_sample_rate} Hz"})
    if snr_db < MIN_SNR_DB:
        issues.append({"code": "low_snr", "severity": "high",
                       "detail": f"snr={snr_db:.1f} dB < {MIN_SNR_DB} dB"})

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    blocking = any(i["severity"] == "high" for i in issues)
    quality_score = max(0.0, min(1.0, 1.0 - 0.25 * len(issues) - (0.15 if blocking else 0.0)))
    return {
        "passed": not blocking,
        "quality_score": round(quality_score, 3),
        "snr_db": round(snr_db, 2),
        "peak_amplitude": round(peak, 4),
        "rms": round(rms, 6),
        "ambient_noise_rms": round(noise, 6),
        "duration_seconds": round(duration, 4),
        "sample_rate_hz": sr,
        "issues": issues,
        "recommendation": "retest_required" if blocking else "ok",
    }


def filter_bandpass(signal: np.ndarray, sr: int, low_hz: float = 100.0,
                    high_hz: float | None = None, order: int = 4) -> np.ndarray:
    """Optional Butterworth band-pass; returns the filtered signal."""
    high = high_hz if high_hz is not None else min(8000.0, sr / 2 * 0.95)
    nyq = sr / 2
    low_n = max(low_hz / nyq, 1e-4)
    high_n = min(high / nyq, 0.999)
    if low_n >= high_n:
        return signal
    from scipy.signal import butter, sosfiltfilt
    sos = butter(order, [low_n, high_n], btype="bandpass", output="sos")
    return sosfiltfilt(sos, signal).astype(np.float32)
