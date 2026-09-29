"""FFT/STFT, log-mel spectrograms, acoustic feature extraction, and export.

Extracts the physical descriptors used by the acoustic models. These features
describe the recorded signal; whether they correlate with onion internal
condition is an empirical question that requires labelled onion data (see
dataset-acoustic/README.md).
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from scipy.signal import stft

from .loading import load_wav
from .quality import check_quality, filter_bandpass

FRAME_SECONDS = 0.02
OVERLAP = 0.5
N_MELS = 64
FMIN, FMAX = 100.0, 8000.0


def compute_stft(signal: np.ndarray, sr: int):
    f, t, Z = stft(signal, fs=sr, nperseg=max(int(sr * FRAME_SECONDS), 256),
                   noverlap=int(int(sr * FRAME_SECONDS) * OVERLAP))
    return f, t, np.abs(Z)


def compute_log_mel(signal: np.ndarray, sr: int,
                    n_mels: int = N_MELS) -> np.ndarray:
    """Log-mel spectrogram with a deterministic triangular filterbank."""
    f, t, Z = compute_stft(signal, sr)
    power = (Z ** 2).T  # (frames, freq bins)
    n_fft_freqs = power.shape[1]
    fmax = min(FMAX, sr / 2)

    def hz_to_mel(hz):
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    mel_pts = np.linspace(hz_to_mel(FMIN), hz_to_mel(fmax), n_mels + 2)
    hz_pts = mel_to_hz(mel_pts)
    bins = np.floor((n_fft_freqs - 1) * hz_pts / (sr / 2)).astype(int)
    bins = np.clip(bins, 0, n_fft_freqs - 1)

    fbank = np.zeros((n_mels, n_fft_freqs), dtype=np.float32)
    for m in range(1, n_mels + 1):
        left, center, right = bins[m - 1], bins[m], bins[m + 1]
        if center == left or center == right:
            continue
        up = np.arange(left, center)
        fbank[m - 1, up] = (up - left) / max(center - left, 1)
        down = np.arange(center, right)
        fbank[m - 1, down] = (right - down) / max(right - center, 1)

    mel = power @ fbank.T
    return np.log(mel + 1e-10).T  # (frames, n_mels)


def extract_features(signal: np.ndarray, sr: int,
                     apply_bandpass: bool = True) -> Dict[str, float]:
    """Full acoustic feature set for one recording."""
    if apply_bandpass:
        signal = filter_bandpass(signal, sr)
    n = len(signal)
    if n < 256:
        raise ValueError("Signal too short for feature extraction.")

    window = np.hanning(n)
    spectrum = np.abs(np.fft.rfft(signal * window))
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    power = spectrum ** 2
    sum_power = float(np.sum(power)) + 1e-12
    norm_power = power / sum_power

    valid = (freqs >= FMIN) & (freqs <= min(FMAX, sr / 2))
    if np.any(valid):
        v_idx = np.where(valid)[0]
        peak_idx = v_idx[np.argmax(spectrum[v_idx])]
        dominant_frequency = float(freqs[peak_idx])
    else:
        dominant_frequency = float(freqs[np.argmax(spectrum)])

    centroid = float(np.sum(freqs * norm_power))
    bandwidth = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * norm_power)))
    cumulative = np.cumsum(power)
    rolloff_idx = int(np.searchsorted(cumulative, 0.85 * sum_power))
    rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)])
    p = norm_power[norm_power > 1e-12]
    entropy = float(-np.sum(p * np.log2(p)) / max(np.log2(len(norm_power)), 1e-12))
    zc = float(np.mean(np.abs(np.diff(np.sign(signal))) > 0))

    rms = float(np.sqrt(np.mean(signal ** 2)))
    peak_amp = float(np.max(np.abs(signal)))

    low_band = float(np.sum(power[(freqs >= 100) & (freqs < 1000)]) / sum_power)
    mid_band = float(np.sum(power[(freqs >= 1000) & (freqs < 4000)]) / sum_power)
    high_band = float(np.sum(power[(freqs >= 4000) & (freqs <= 8000)]) / sum_power)

    # Decay features from the smoothed envelope after the global peak.
    win = max(int(sr * 0.01), 16)
    env = np.convolve(np.abs(signal), np.ones(win) / win, mode="valid")
    decay_rate = 15.0
    decay_time_60db = 0.0
    if len(env) > 20:
        pk = int(np.argmax(env))
        tail = env[pk:]
        t = np.arange(len(tail)) / sr
        safe = np.maximum(tail, 1e-4)
        slope, _ = np.polyfit(t, np.log(safe), 1)
        decay_rate = float(max(-slope, 0.0))
        peak_env = float(tail[0]) if len(tail) else 0.0
        thresh = peak_env * (10 ** (-60 / 20))
        below = np.where(tail < thresh)[0]
        decay_time_60db = float(below[0] / sr) if len(below) else float(len(tail) / sr)

    # Resonance peak: prominent local maximum in the 100-8000 Hz band.
    from scipy.signal import find_peaks
    resonance_peak = dominant_frequency
    band_spec = np.where(valid, spectrum, 0.0)
    peaks, props = find_peaks(band_spec, prominence=float(np.max(band_spec)) * 0.1)
    if len(peaks):
        resonance_peak = float(freqs[peaks[int(np.argmax(props["prominences"]))]])

    return {
        "rms_energy": round(rms, 6),
        "peak_amplitude": round(peak_amp, 6),
        "dominant_frequency_hz": round(dominant_frequency, 1),
        "spectral_centroid_hz": round(centroid, 1),
        "spectral_bandwidth_hz": round(bandwidth, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "spectral_entropy": round(entropy, 4),
        "zero_crossing_rate": round(zc, 4),
        "energy_low_band": round(low_band, 4),
        "energy_mid_band": round(mid_band, 4),
        "energy_high_band": round(high_band, 4),
        "resonance_peak_hz": round(resonance_peak, 1),
        "decay_rate": round(decay_rate, 3),
        "decay_time_60db_s": round(decay_time_60db, 4),
    }


FEATURE_ORDER: List[str] = [
    "rms_energy", "peak_amplitude", "dominant_frequency_hz",
    "spectral_centroid_hz", "spectral_bandwidth_hz", "spectral_rolloff_hz",
    "spectral_entropy", "zero_crossing_rate", "energy_low_band",
    "energy_mid_band", "energy_high_band", "resonance_peak_hz",
    "decay_rate", "decay_time_60db_s",
]


def analyze_file(path: str | Path, expected_duration_s: Optional[float] = None,
                 apply_bandpass: bool = True) -> Dict[str, object]:
    """Load a WAV, run quality gates, and extract features.

    Returns {"quality": report, "features": dict, "path": str}.
    Raises ValueError if the file cannot be loaded.
    """
    sr, signal = load_wav(path)
    quality = check_quality(signal, sr, expected_duration_s=expected_duration_s)
    if not quality["passed"]:
        return {"path": str(path), "quality": quality, "features": None,
                "error": "quality gates failed: " + quality["recommendation"]}
    features = extract_features(signal, sr, apply_bandpass=apply_bandpass)
    return {"path": str(path), "quality": quality, "features": features,
            "sample_rate_hz": sr}


def export_features_csv(rows: List[Dict[str, object]], out_path: str | Path) -> Path:
    """Write feature rows (dicts) to CSV with a deterministic column order."""
    out = Path(out_path)
    fieldnames = ["path", "sample_rate_hz"] + FEATURE_ORDER + [
        "quality_passed", "snr_db", "recommendation"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            flat = dict(row)
            feat = flat.get("features") or {}
            qual = flat.get("quality") or {}
            for k, v in feat.items():
                flat[k] = v
            flat["quality_passed"] = qual.get("passed")
            flat["snr_db"] = qual.get("snr_db")
            flat["recommendation"] = qual.get("recommendation")
            w.writerow(flat)
    return out


try:  # Optional Parquet export (pandas/pyarrow); degrades gracefully.
    import pandas as pd  # noqa: E402

    def export_features_parquet(rows: List[Dict[str, object]], out_path: str | Path) -> Path:
        out = Path(out_path)
        csv_tmp = export_features_csv(rows, out.with_suffix(".tmp.csv"))
        df = pd.read_csv(csv_tmp)
        df.to_parquet(out, index=False)
        csv_tmp.unlink()
        return out
except Exception:  # pragma: no cover
    def export_features_parquet(rows, out_path):  # type: ignore[misc]
        raise RuntimeError("Parquet export requires pandas and pyarrow.")
