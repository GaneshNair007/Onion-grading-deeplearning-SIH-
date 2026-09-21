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


def _lead_in_floor(signal: np.ndarray, sr: int, lead_seconds: float = 0.1) -> float:
    """RMS of the pre-excitation lead-in (first ~100 ms).

    For sustained excitations (chirps) the median-frame floor is
    self-referential — the signal IS the excitation, so excess-over-floor
    is ~0 dB by construction. The lead-in, recorded before the chirp
    starts (the scan page starts its speaker 150 ms after recording), is
    the honest floor. Returns 0.0 when the lead-in is too short to trust.
    """
    n = min(int(sr * lead_seconds), len(signal) // 4)
    if n < 16:
        return 0.0
    lead = signal[:n]
    return float(np.sqrt(np.mean(lead.astype(np.float64) ** 2)))


def _resolve_floor(sig: np.ndarray, sr: int, rms: float,
                   noise_floor_rms: Optional[float]) -> tuple:
    """Pick the honest noise floor for this recording.

    An explicitly provided floor (the ambient baseline measured before the
    excitation) is trusted when it is consistent with the recording: an
    honest ambient floor is at most as loud as the quietest stretch of the
    recording itself. A provided floor LOUDER than the inter-event quiet
    was not measured in silence (e.g. the pipeline's ambient estimate over
    a recording whose impact starts at t=0) and is discarded in favour of
    the recording's own estimates. A self-estimated median-frame floor is
    only meaningful when the recording is dominated by inter-event quiet
    (floor well below the signal RMS); otherwise fall back to the lead-in
    segment when that is genuinely quieter. Returns (floor, source_label).
    """
    if noise_floor_rms:
        provided = float(noise_floor_rms)
        median = _noise_floor_rms(sig)
        if median > 0 and provided > median:
            # "Floor" louder than the quietest frames: measured over the
            # excitation, not silence. Fall back to in-recording evidence.
            lead = _lead_in_floor(sig, sr)
            if lead > 0 and lead <= median:
                return lead, "lead_in_provided_suspect"
            return median, "median_frame_provided_suspect"
        return provided, "provided"
    floor = _noise_floor_rms(sig)
    if rms and rms > 0 and floor is not None and floor > 0.5 * rms:
        lead = _lead_in_floor(sig, sr)
        if lead > 0 and lead < 0.5 * rms:
            return lead, "lead_in"
    if floor is None:
        lead = _lead_in_floor(sig, sr)
        if lead and lead > 0:
            return lead, "lead_in"
        return 0.0, "no_floor_evidence"
    return floor, "median_frame"


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
    floor, floor_source = _resolve_floor(sig, sr, rms, noise_floor_rms)

    measured = {
        "peak_amplitude": round(peak, 4),
        "rms_energy": round(rms, 4),
        "noise_floor_rms": round(floor, 4),
        "floor_source": floor_source,
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
    elif capture_method in ("phone_tap", "impact_hammer"):
        # --- impulsive character --------------------------------------------
        crest = measured["crest_factor"]
        if crest < MIN_CREST_FACTOR:
            reasons.append(
                f"not impulsive: crest factor {crest:.2f} < {MIN_CREST_FACTOR:.2f} "
                "(room noise is not impulsive)")

        # --- free decay after the impact ------------------------------------
        decay_rate = _fast_decay_rate(sig, sr, peak_index=int(np.argmax(np.abs(sig))),
                                      noise_floor=floor)
        measured["post_peak_decay_rate_per_s"] = round(decay_rate, 1)
        if decay_rate < MIN_DECAY_RATE_PER_S:
            reasons.append(
                f"no free decay after impact: {decay_rate:.1f}/s < "
                f"{MIN_DECAY_RATE_PER_S:.1f}/s (noise does not decay)")
    else:
        # Method unknown/omitted: accept EITHER a tap signature OR a chirp
        # signature, and record which one matched. Both failing is required
        # for a rejection.
        crest = measured["crest_factor"]
        decay_rate = _fast_decay_rate(sig, sr, peak_index=int(np.argmax(np.abs(sig))),
                                      noise_floor=floor)
        measured["post_peak_decay_rate_per_s"] = round(decay_rate, 1)
        tap_ok = (crest >= MIN_CREST_FACTOR
                  and decay_rate >= MIN_DECAY_RATE_PER_S)
        excess = _db(rms) - _db(max(floor, 1e-12))
        measured["rms_excess_over_floor_db"] = round(excess, 1)
        chirp_ok = excess >= CHIRP_MIN_EXCESS_DB
        if tap_ok:
            measured["matched_signature"] = "tap"
        elif chirp_ok:
            measured["matched_signature"] = "chirp"
        if not (tap_ok or chirp_ok):
            reasons.append(
                f"no tap signature: crest {crest:.2f} < {MIN_CREST_FACTOR:.2f} "
                f"or decay {decay_rate:.1f}/s < {MIN_DECAY_RATE_PER_S:.1f}/s")
            reasons.append(
                f"no sustained chirp response: rms excess {excess:.1f} dB < "
                f"{CHIRP_MIN_EXCESS_DB:.1f} dB over floor")

    return {"passed": len(reasons) == 0, "reasons": reasons, "measured": measured}


def _fast_decay_rate(sig: np.ndarray, sr: int, peak_index: int,
                     noise_floor: float = 0.0) -> float:
    """Best envelope decay rate (1/s) over the impulsive events in the clip.

    RT60-style, per event: the guided protocol is "tap 3x", so a capture
    contains several impacts and the loudest (global) peak is often the
    LAST one — measured live: a valid 3-tap capture whose final tap sat
    0.27 s before the end read 0.0/s from the global peak (hand noise in
    the short tail) while its earlier taps showed clean free decay. This
    estimator therefore finds every impulsive event (local envelope max
    above 35% of the global envelope max, 15 ms refractory), fits the
    envelope over the 150 ms after each event — the timescale on which a
    damped onion ring actually lives (measured: rings die in 15 ms–100 ms)
    — and returns the best rate among events that also pass the
    systematic-decrease check. Fluctuating noise and hum have no discrete
    event whose envelope halves within 150 ms, so they still return 0.0.
    """
    del peak_index, noise_floor  # multi-event, scale-free analysis
    frame = max(sr // 200, 32)  # 5 ms frames
    n_frames = (sig.size - frame) // frame
    if n_frames < 8:
        return 0.0
    env = np.sqrt(np.mean(sig[:n_frames * frame].reshape(n_frames, frame) ** 2,
                          axis=1))
    env_max = float(env.max())
    if env_max < 1e-9:
        return 0.0

    # Event candidates: local envelope maxima above 35% of the global max.
    # Frame 0 counts (an impact may open the recording); refractory does not
    # apply to it since nothing precedes it.
    thresh = 0.35 * env_max
    refractory = 3  # frames (15 ms)
    events: list[int] = []
    if env[0] > env[1] and env[0] > thresh:
        events.append(0)
        last = 0
    else:
        last = -refractory
    for i in range(1, n_frames - 1):
        if env[i] >= env[i - 1] and env[i] > env[i + 1] and env[i] > thresh \
                and i - last >= refractory:
            events.append(i)
            last = i
    if not events:
        return 0.0

    best = 0.0
    for k, f0 in enumerate(events):
        # 150 ms fit window, cut short by the next event if it comes sooner
        # (a following tap re-excites the envelope and would flatten the
        # fit) or by the end of the recording.
        f_end = events[k + 1] if k + 1 < len(events) else n_frames
        f_end = min(f_end, f0 + 30, n_frames)  # 30 frames = 150 ms
        if f_end - f0 < 8:
            continue
        seg_env = env[f0:f_end]
        peak_env = float(seg_env.max())
        if peak_env < 1e-9:
            continue
        keep = seg_env > 0.05 * peak_env
        if keep.sum() < 4:
            # Very fast rings collapse below 5% of the event peak within a
            # few frames; retry relative to 1% before giving up on the
            # event (the ring still dominates its own tail there, while a
            # noise spike surrounded by its own floor cannot produce a
            # decreasing multi-frame fit).
            keep = seg_env > 0.01 * peak_env
            if keep.sum() < 4:
                continue
        t = np.arange(seg_env.size, dtype=np.float64) * (frame / sr)
        slope = float(np.polyfit(t[keep], np.log(seg_env[keep]), 1)[0])
        rate = max(-slope, 0.0)

        # Systematic decrease required over the response window: late
        # envelope must fall well below the early envelope. Fluctuating
        # noise fails this even if a local slope looks like a decay.
        n10 = max(int(keep.sum()) // 10, 1)
        idx = np.nonzero(keep)[0]
        early = float(np.mean(seg_env[idx[:n10]]))
        late = float(np.mean(seg_env[idx[-max(int(keep.sum()) // 5, 1):]]))
        if late >= 0.5 * max(early, 1e-12):
            continue
        best = max(best, rate)
        if best >= MIN_DECAY_RATE_PER_S:
            break  # enough evidence of a physical impact
    return best
