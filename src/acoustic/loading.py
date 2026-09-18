"""Audio loading, sample-rate inspection, mono conversion, normalization."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import scipy.io.wavfile as wavfile

SUPPORTED_FORMATS = {".wav"}


class AudioLoadError(ValueError):
    """Raised when an audio file cannot be loaded safely."""


def inspect_format(path: str | Path) -> dict:
    """Return basic file metadata without fully decoding the samples."""
    p = Path(path)
    if not p.exists():
        raise AudioLoadError(f"File not found: {p}")
    if p.suffix.lower() not in SUPPORTED_FORMATS:
        raise AudioLoadError(
            f"Unsupported format '{p.suffix}'. Supported: {sorted(SUPPORTED_FORMATS)}")
    sample_rate, data = wavfile.read(str(p))
    return {
        "path": str(p),
        "sample_rate_hz": int(sample_rate),
        "channels": 1 if data.ndim == 1 else int(data.shape[1]),
        "frames": int(data.shape[0] if data.ndim == 1 else data.shape[0]),
        "duration_seconds": round(len(data) / sample_rate, 4),
        "dtype": str(data.dtype),
    }


def load_wav(path: str | Path) -> Tuple[int, np.ndarray]:
    """Load a WAV file as mono float32 in [-1, 1]."""
    p = Path(path)
    if not p.exists():
        raise AudioLoadError(f"File not found: {p}")
    sample_rate, data = wavfile.read(str(p))
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        data = (data.astype(np.float32) - 128.0) / 128.0
    else:
        data = data.astype(np.float32)
    return int(sample_rate), data


def resample_linear(signal: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Deterministic linear-interpolation resampler (no external deps).

    For analysis pipelines prefer recording at the target rate; this exists
    for robustness when comparing recordings across devices.
    """
    if orig_sr == target_sr:
        return signal
    duration = len(signal) / orig_sr
    target_len = int(round(duration * target_sr))
    if target_len < 2:
        return signal
    x_old = np.linspace(0.0, duration, num=len(signal), endpoint=False)
    x_new = np.linspace(0.0, duration, num=target_len, endpoint=False)
    return np.interp(x_new, x_old, signal).astype(np.float32)


def normalize_peak(signal: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Peak-normalize to target_peak; silent signals are returned unchanged."""
    peak = float(np.max(np.abs(signal))) if len(signal) else 0.0
    if peak <= 1e-9:
        return signal
    return (signal / peak) * target_peak


def estimate_ambient_noise(signal: np.ndarray, sr: int, lead_seconds: float = 0.1) -> float:
    """RMS of the lead-in segment as an ambient-noise estimate."""
    n = min(int(sr * lead_seconds), max(1, len(signal) // 4))
    if n < 16:
        return 0.0
    lead = signal[:n]
    return float(np.sqrt(np.mean(lead ** 2)))
