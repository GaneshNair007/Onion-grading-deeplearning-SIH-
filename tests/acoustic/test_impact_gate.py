"""Regression tests for the impact-presence gate.

Root cause fixed here: the classifier answered for ANY audio — room noise
produced an internal-defect probability of 0.93. These tests make that
failure impossible to reintroduce: audio without a tap/chirp excitation
must yield ``no_impact_detected`` with a NULL probability, never a number.
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.acoustic.impact_gate import check_impact_present  # noqa: E402


def _write_wav(path: Path, sig: np.ndarray, sr: int = 16000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(sig, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


def _tap(sr: int = 16000, seconds: float = 1.0,
         rng: np.random.Generator | None = None) -> np.ndarray:
    t = np.arange(int(sr * seconds)) / sr
    env = np.exp(-t * 25)
    sig = 0.5 * env * np.sin(2 * np.pi * 280 * t)
    sig += 0.2 * env * np.sin(2 * np.pi * 1400 * t)
    rng = rng or np.random.default_rng(0)
    return sig + rng.normal(0, 0.005, len(t))


def _noise(seconds: float = 1.0, seed: int = 0,
           sigma: float = 0.02) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0, sigma, int(16000 * seconds))


# ------------------------------------------------------------- gate level
def test_gate_rejects_white_noise():
    g = check_impact_present(_noise(), 16000)
    assert g["passed"] is False
    assert g["reasons"]


def test_gate_rejects_smooth_hum():
    sr = 16000
    t = np.arange(sr) / sr
    sig = 0.15 * np.sin(2 * np.pi * 120 * t)
    g = check_impact_present(sig, sr)
    assert g["passed"] is False


def test_gate_rejects_quality_passing_fluctuating_noise():
    """Mimics the live failure: noise that passes SNR quality gates but has
    no impact transient and no decay."""
    sr = 16000
    t = np.arange(sr * 2) / sr
    env = 0.10 + 0.08 * np.sin(2 * np.pi * 0.7 * t)
    sig = env * np.random.default_rng(3).normal(0, 1, len(t))
    sig += 0.03 * np.sin(2 * np.pi * 120 * t)
    g = check_impact_present(sig, sr)
    assert g["passed"] is False


def test_gate_accepts_real_tap():
    g = check_impact_present(_tap(), 16000)
    assert g["passed"] is True, g["reasons"]


def test_gate_accepts_quieter_tap():
    g = check_impact_present(0.4 * _tap(rng=np.random.default_rng(5)), 16000)
    assert g["passed"] is True, g["reasons"]


def test_gate_rejects_empty_signal():
    g = check_impact_present(np.array([]), 16000)
    assert g["passed"] is False


# ------------------------------------------------------- inference level
def test_classify_returns_no_impact_for_noise(tmp_path):
    from inference.acoustic_inference import classify_acoustic

    # Fluctuating noise that passes quality gates -> the impact gate itself
    # must reject it (quality gates alone catch quieter noise earlier).
    sr = 16000
    t = np.arange(sr * 2) / sr
    env = 0.10 + 0.08 * np.sin(2 * np.pi * 0.7 * t)
    sig = env * np.random.default_rng(3).normal(0, 1, len(t))
    sig += 0.03 * np.sin(2 * np.pi * 120 * t)
    p = _write_wav(tmp_path / "noise_swell.wav", sig)
    r = classify_acoustic(str(p))
    assert r["status"] == "no_impact_detected"
    assert r["internal_defect_probability"] is None
    assert r["grading_eligible"] is False
    assert any("excitation" in w for w in r["warnings"])


def test_classify_still_answers_for_a_real_tap(tmp_path):
    from inference.acoustic_inference import classify_acoustic

    p = _write_wav(tmp_path / "tap.wav", _tap(rng=np.random.default_rng(2)))
    r = classify_acoustic(str(p))
    assert r["status"] == "valid"
    assert r["internal_defect_probability"] is not None
    # Honesty labels unchanged: synthetic demo can never grade.
    assert r["research_only"] is True
    assert r["grading_eligible"] is False


def test_fusion_never_uses_impactless_audio(tmp_path):
    """The fusion layer must ignore non-impact audio even if given it directly."""
    from src.fusion.fusion import fuse_results

    vision = {"label": "sound", "confidence": 0.9, "defects": {},
              "model_version": "vision-v1"}
    bogus = {"status": "valid",  # forged: gate bypassed upstream
             "internal_defect_probability": 0.99, "confidence": 0.9,
             "ground_truth_verified": False, "model_version": "x"}
    out = fuse_results(vision, bogus)
    # Vision-only fallback happens BEFORE fusion (not_onion short-circuit);
    # what matters is that research-only acoustic evidence is never eligible.
    assert out.get("acoustic_eligible") is False
    assert out["final"]["label"] == "not_onion"
