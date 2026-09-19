"""Impact-presence gate: refuse to answer when no tap/excitation was captured.

Why this exists
---------------
The baseline classifier answers for ANY input — including empty room noise —
because the synthetic training distribution does not span real recordings.
A "prediction" on audio that contains no physical excitation event is a false
answer (observed live: room noise produced an internal-defect probability of
0.93). The gate below runs BEFORE the model: if the recording does not contain
evidence of a tap or chirp response, the pipeline must return
``no_impact_detected`` with a null probability — never a number.

Physical basis
--------------
A real impact on an onion has a characteristic envelope:
  1. a fast attack well above the local noise floor,
  2. an impulsive crest factor (peak >> rms),
  3. a free decay afterwards (exponential-ish envelope).
Room noise has none of these: its peak/rms ratio is low and its envelope does
not decay. The thresholds were calibrated on measured noise floors and real
tap recordings (see tests/acoustic/test_impact_gate.py) and are deliberately
conservative — when in doubt the gate rejects the recording.

Chirp-response captures (speaker excitation) are checked separately: they
require sustained excitation energy above the measured noise floor rather than
a single transient.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np

# --- calibrated thresholds (see module docstring; conservative by design) ---
MIN_PEAK_AMPLITUDE = 0.030      # absolute transient floor (16-bit mic, phone cm away)
MIN_SNR_TO_FLOOR_DB = 8.0       # transient must exceed the local noise floor
MIN_CREST_FACTOR = 4.0          # impulsive: peak / rms
MIN_DECAY_RATE_PER_S = 1.5      # free decay after impact
CHIRP_MIN_EXCESS_DB = 6.0       # sustained excitation above floor for chirp mode


def _db(x: float) -> float:
    return float(20.0 * np.log10(max(x, 1e-12)))


def _noise_floor_rms(signal: np.ndarray) -> float:
    """Robust noise floor: median absolute amplitude of frame RMS."""
    frame = max(len(signal) // 20, 256)
    n_frames = max(len(signal) // frame, 1)
    rms = []
    for i in range(n_frames):
        seg = signal[i * frame:(i + 1) * frame]
        if len(seg):
            rms.append(float(np.sqrt(np.mean(seg.astype(np.float64) ** 2))))
    return float(np.median(rms)) if rms else 0.0


def check_impact_present(signal: np.ndarray, sr: int,
                         capture_method: Optional[str] = None,
                         noise_floor_rms: Optional[float] = None) -> Dict[str, Any]:
    """Decide whether the recording contains a tap/chirp excitation event.

    Returns a dict with at least ``passed``, ``reasons`` and measured values.
    Deliberately conservative: any missing evidence fails the gate.
    """
    sig = np.asarray(signal, dtype=np.float64).ravel()
    reasons: list[str] = []

    if sig.size == 0:
        return {"passed": False, "reasons": ["empty_signal"], "measured": {}}

    peak = float(np.max(np.abs(sig)))
    rms = float(np.sqrt(np.mean(sig ** 2)))
    floor = float(noise_floor_rms) if noise_floor_rms else _noise_floor_rms(sig)

    measured = {
        "peak_amplitude": round(peak, 4),
        "rms_energy": round(rms, 4),
        "noise_floor_rms": round(floor, 4),
        "transient_snr_db": round(_db(peak) - _db(floor), 1),
        "crest_factor": round(peak / max(rms, 1e-12), 2),
    }

    # --- absolute transient level ------------------------------------------
    if peak < MIN_PEAK_AMPLITUDE:
        reasons.append(
            f"no transient above absolute floor: peak {peak:.3f} < "
            f"{MIN_PEAK_AMPLITUDE:.3f}")

    # --- transient above the local noise floor ------------------------------
    transient_snr = measured["transient_snr_db"]
    if transient_snr < MIN_SNR_TO_FLOOR_DB:
        reasons.append(
            f"transient not above noise floor: {transient_snr:.1f} dB < "
            f"{MIN_SNR_TO_FLOOR_DB:.1f} dB")

    if capture_method == "phone_chirp":
        # Sustained excitation: excess energy over the floor.
        excess = _db(rms) - _db(max(floor, 1e-12))
        measured["rms_excess_over_floor_db"] = round(excess, 1)
        if excess < CHIRP_MIN_EXCESS_DB:
            reasons.append(
                f"no sustained chirp response: rms excess {excess:.1f} dB < "
                f"{CHIRP_MIN_EXCESS_DB:.1f} dB over floor")
    else:
        # --- impulsive character --------------------------------------------
        crest = measured["crest_factor"]
        if crest < MIN_CREST_FACTOR:
            reasons.append(
                f"not impulsive: crest factor {crest:.2f} < {MIN_CREST_FACTOR:.2f} "
                "(room noise is not impulsive)")

        # --- free decay after the impact ------------------------------------
        decay_rate = _fast_decay_rate(sig, sr, peak_index=int(np.argmax(np.abs(sig))))
        measured["post_peak_decay_rate_per_s"] = round(decay_rate, 1)
        if decay_rate < MIN_DECAY_RATE_PER_S:
            reasons.append(
                f"no free decay after impact: {decay_rate:.1f}/s < "
                f"{MIN_DECAY_RATE_PER_S:.1f}/s (noise does not decay)")

    return {"passed": len(reasons) == 0, "reasons": reasons, "measured": measured}


def _fast_decay_rate(sig: np.ndarray, sr: int, peak_index: int) -> float:
    """Estimate the envelope decay rate (1/s) in the 200 ms after the peak."""
    win = int(0.2 * sr)
    seg = sig[peak_index:peak_index + win]
    if seg.size < sr // 10:  # need at least 100 ms
        return 0.0
    frame = max(sr // 200, 32)  # 5 ms frames
    env = [float(np.sqrt(np.mean(seg[i:i + frame] ** 2)))
           for i in range(0, seg.size - frame, frame)]
    if len(env) < 4:
        return 0.0
    peak_env = max(env[0], 1e-12)
    # Time for the envelope to fall to 20% of its initial value.
    threshold = 0.2 * peak_env
    for idx, value in enumerate(env):
        if value <= threshold:
            return float(-np.log(max(value, 1e-12) / peak_env) /
                         max(idx * (frame / sr), 1e-6))
    # Did not fall to 20% within the window -> slow/no decay.
    return 0.0
