"""Acoustic tests: quality gates, retest flow, missing-model handling.

No test here claims that any feature detects internal rot. They verify that the
pipeline *refuses* unreliable audio and *never* invents a prediction when the
model or the ground truth is missing.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile

from src.acoustic.features import FEATURE_ORDER, analyze_file, extract_features
from src.acoustic.loading import AudioLoadError, load_wav, resample_linear
from src.acoustic.quality import check_quality

SR = 44100


def _write(tmp_path: Path, name: str, sig: np.ndarray, sr: int = SR) -> Path:
    path = tmp_path / name
    wavfile.write(str(path), sr, np.clip(sig, -1, 1).astype(np.float32))
    return path


def _tap_like(duration: float = 1.6, amp: float = 0.5, sr: int = SR) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    sig = amp * np.sin(2 * np.pi * 900 * t) * np.exp(-5 * t)
    sig[: int(sr * 0.1)] = 0.004 * np.sin(2 * np.pi * 60 * t[: int(sr * 0.1)])
    return sig


# --------------------------------------------------------------- quality QC
def test_silence_is_detected():
    report = check_quality(np.zeros(int(SR * 1.6), dtype=np.float32), SR)
    assert report["passed"] is False
    assert any(i["code"] == "silence" for i in report["issues"])
    assert report["recommendation"] == "retest_required"


def test_clipping_is_detected():
    sig = np.zeros(int(SR * 1.6), dtype=np.float32)
    sig[int(SR * 0.5):int(SR * 0.5) + 20] = 1.0     # sustained full-scale run
    report = check_quality(sig, SR)
    assert any(i["code"] == "clipping" for i in report["issues"])


def test_sample_rate_mismatch_is_reported():
    report = check_quality(_tap_like(), SR, expected_sample_rate=48000)
    assert any(i["code"] == "sample_rate_mismatch" for i in report["issues"])


def test_unsupported_sample_rate_is_reported():
    report = check_quality(_tap_like(sr=12345), 12345)
    assert any(i["code"] == "invalid_sample_rate" for i in report["issues"])


def test_inconsistent_duration_is_reported():
    report = check_quality(_tap_like(duration=0.4), SR, expected_duration_s=1.6)
    assert any(i["code"] == "inconsistent_duration" for i in report["issues"])


def test_good_tap_passes_all_gates():
    report = check_quality(_tap_like(), SR, expected_duration_s=1.6)
    assert report["passed"] is True
    assert report["recommendation"] == "ok"
    assert report["quality_score"] > 0.5


def test_low_snr_is_reported():
    rng = np.random.default_rng(3)
    sig = rng.normal(0, 0.02, int(SR * 1.6)).astype(np.float32)
    report = check_quality(sig, SR)
    assert any(i["code"] == "low_snr" for i in report["issues"])


# --------------------------------------------------------------- features
def test_features_are_extracted_in_a_stable_order(tmp_path):
    path = _write(tmp_path, "tap.wav", _tap_like())
    sr, sig = load_wav(path)
    features = extract_features(sig, sr)
    assert list(features.keys()) == list(FEATURE_ORDER)
    assert all(isinstance(v, float) for v in features.values())
    assert features["dominant_frequency_hz"] == pytest.approx(900, abs=250)


def test_feature_extraction_is_deterministic(tmp_path):
    path = _write(tmp_path, "tap.wav", _tap_like())
    sr, sig = load_wav(path)
    assert extract_features(sig, sr) == extract_features(sig, sr)


def test_analyze_file_refuses_bad_audio_without_features(tmp_path):
    path = _write(tmp_path, "silence.wav", np.zeros(int(SR * 1.6), dtype=np.float32))
    result = analyze_file(path)
    assert result["features"] is None
    assert result["quality"]["passed"] is False


def test_resample_changes_length_and_preserves_energy():
    sig = _tap_like(sr=48000)
    out = resample_linear(sig, 48000, 16000)
    assert len(out) == pytest.approx(len(sig) / 3, rel=0.02)
    assert np.isfinite(out).all()


def test_missing_file_raises_a_clear_error(tmp_path):
    with pytest.raises(AudioLoadError):
        load_wav(tmp_path / "does_not_exist.wav")


# ------------------------------------------------- missing model / retest
def test_missing_acoustic_model_reports_no_prediction(tmp_path):
    from inference.acoustic_inference import classify_acoustic
    path = _write(tmp_path, "tap.wav", _tap_like())
    result = classify_acoustic(str(path),
                               model_path=str(tmp_path / "nope.joblib"))
    assert result["status"] == "model_not_trained"
    assert result["internal_defect_probability"] is None
    assert result["confidence"] is None


def test_bad_audio_requests_a_retest_not_a_guess(tmp_path):
    from inference.acoustic_inference import classify_acoustic
    path = _write(tmp_path, "silence.wav", np.zeros(int(SR * 1.6), dtype=np.float32))
    result = classify_acoustic(str(path))
    assert result["status"] == "retest_required"
    assert result["internal_defect_probability"] is None


def test_synthetic_demo_model_is_never_described_as_onion_ground_truth():
    """The shipped synthetic model must be labelled, not presented as onion data."""
    from inference.acoustic_inference import MODEL_VERSION
    assert "synthetic" in MODEL_VERSION or "demo" in MODEL_VERSION


def test_capture_protocol_retests_before_giving_up():
    from src.mobile.capture_protocol import measure_onion

    calls = {"n": 0}

    def bad_recorder(play_chirp: bool):
        calls["n"] += 1
        return SR, np.zeros(int(SR * 1.6), dtype=np.float32)

    result = measure_onion(bad_recorder,
                           {"device_model": "test", "os_version": "test",
                            "sample_rate_hz": SR}, use_chirp=True)
    assert result["ok"] is False
    assert "quality gates" in result["reason"]
    assert calls["n"] >= 2, "must retry (chirp then tap) before reporting failure"
    assert len(result["attempts"]) == calls["n"]


def test_capture_protocol_succeeds_on_a_good_recording():
    from src.mobile.capture_protocol import measure_onion

    def good_recorder(play_chirp: bool):
        return SR, _tap_like().astype(np.float32)

    result = measure_onion(good_recorder,
                           {"device_model": "test", "os_version": "test",
                            "sample_rate_hz": SR})
    assert result["ok"] is True
    assert result["capture_metadata"]["capture_method"] == "phone_chirp"
    assert result["features"]
