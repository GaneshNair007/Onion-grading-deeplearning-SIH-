"""Tests for the acoustic pipeline, fusion engine, and demo contract.

Run: pytest tests/test_multimodal.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "inference"))

from src.acoustic.loading import (AudioLoadError, inspect_format, load_wav,
                                  normalize_peak, resample_linear)
from src.acoustic.quality import check_quality, calculate_snr_db
from src.acoustic.splits import split_by_onion
from src.fusion import fuse_results

SYNTH_DIR = PROJECT_ROOT / "dataset-acoustic" / "synthetic" / "demo_chirp_responses"


# ---------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def good_tone_wav(tmp_path_factory):
    """1.6 s decaying 1500 Hz tone with a quiet lead-in: passes all gates."""
    sr = 44100
    t = np.linspace(0, 1.6, int(sr * 1.6), endpoint=False)
    sig = 0.4 * np.sin(2 * np.pi * 1500 * t) * np.exp(-4 * t)
    sig[: int(sr * 0.1)] = 0.003 * np.sin(2 * np.pi * 40 * t[: int(sr * 0.1)])
    path = tmp_path_factory.mktemp("wav") / "good_tone.wav"
    wavfile.write(str(path), sr, (sig * 32767).astype(np.int16))
    return path


@pytest.fixture(scope="module")
def demo_wav():
    return SYNTH_DIR / "synthetic_firmlike_001.wav"


# ---------------------------------------------------------------- loading
def test_audio_loading(demo_wav):
    sr, sig = load_wav(demo_wav)
    assert sr == 44100
    assert sig.dtype == np.float32
    assert len(sig) == 70560
    assert -1.0 <= float(np.max(np.abs(sig))) <= 1.0


def test_inspect_format(demo_wav):
    info = inspect_format(demo_wav)
    assert info["sample_rate_hz"] == 44100
    assert info["channels"] == 1
    assert info["duration_seconds"] == pytest.approx(1.6, abs=0.01)


def test_missing_file_raises(tmp_path):
    with pytest.raises(AudioLoadError):
        load_wav(tmp_path / "nope.wav")


def test_resample_linear_changes_length():
    sr_in, sr_out = 44100, 22050
    sig = np.ones(4410, dtype=np.float32)
    out = resample_linear(sig, sr_in, sr_out)
    assert len(out) == 2205


def test_normalize_peak_silent_signal():
    sig = np.zeros(1000, dtype=np.float32)
    assert float(np.max(np.abs(normalize_peak(sig)))) == 0.0


# ---------------------------------------------------------------- quality
def test_silence_detection(tmp_path):
    sr = 44100
    silence = np.zeros(int(sr * 1.6), dtype=np.float32)
    report = check_quality(silence, sr)
    assert not report["passed"]
    codes = {i["code"] for i in report["issues"]}
    assert "silence" in codes
    assert report["recommendation"] == "retest_required"


def test_clipping_detection():
    sr = 8000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    sig = np.clip(3.0 * np.sin(2 * np.pi * 200 * t), -1.0, 1.0).astype(np.float32)
    report = check_quality(sig, sr)
    codes = {i["code"] for i in report["issues"]}
    assert "clipping" in codes
    assert not report["passed"]


def test_sample_rate_mismatch_flagged(good_tone_wav):
    sr, sig = load_wav(good_tone_wav)
    report = check_quality(sig, sr, expected_sample_rate=48000)
    codes = {i["code"] for i in report["issues"]}
    assert "sample_rate_mismatch" in codes


def test_invalid_sample_rate_flagged(good_tone_wav):
    _, sig = load_wav(good_tone_wav)
    report = check_quality(sig, 12345)
    codes = {i["code"] for i in report["issues"]}
    assert "invalid_sample_rate" in codes


def test_inconsistent_duration_flagged(good_tone_wav):
    sr, sig = load_wav(good_tone_wav)
    report = check_quality(sig, sr, expected_duration_s=0.4)
    codes = {i["code"] for i in report["issues"]}
    assert "inconsistent_duration" in codes


def test_good_recording_passes(good_tone_wav):
    sr, sig = load_wav(good_tone_wav)
    report = check_quality(sig, sr)
    assert report["passed"], report
    assert report["recommendation"] == "ok"


# ---------------------------------------------------------------- features
def test_feature_extraction_values(demo_wav):
    from src.acoustic.features import analyze_file
    result = analyze_file(demo_wav)
    assert result["features"] is not None
    f = result["features"]
    assert 100 <= f["resonance_peak_hz"] <= 8000
    assert 0 < f["spectral_entropy"] <= 1.0
    assert f["decay_rate"] > 0
    assert set(f) >= {"rms_energy", "peak_amplitude", "dominant_frequency_hz",
                      "spectral_centroid_hz", "spectral_bandwidth_hz",
                      "spectral_rolloff_hz", "zero_crossing_rate"}


def test_failing_file_returns_no_features(tmp_path):
    from src.acoustic.features import analyze_file
    sr = 8000
    path = tmp_path / "silence.wav"
    wavfile.write(str(path), sr, np.zeros(int(sr * 1.0), dtype=np.float32))
    result = analyze_file(path)
    assert result["features"] is None
    assert "quality" in result["error"]


# ---------------------------------------------------------------- splits
def test_split_by_onion_not_recording():
    onions = [f"ONION_{i:06d}" for i in range(20)]
    assignment = split_by_onion(onions, seed=7)
    assert set(assignment.values()) == {"train", "validation", "test"}
    assert len(assignment) == 20
    again = split_by_onion(onions, seed=7)
    assert assignment == again  # deterministic


def test_split_ratios_respected():
    onions = [f"ONION_{i:06d}" for i in range(100)]
    a = split_by_onion(onions, seed=1)
    counts = {s: list(a.values()).count(s) for s in ("train", "validation", "test")}
    assert counts["train"] == 60 and counts["validation"] == 20 and counts["test"] == 20


# ---------------------------------------------------------------- fusion
#: Defect confidences are part of the contract: fusion derives its "defect
#: pressure" from them rather than from a freshness number that no current
#: model emits (see src/fusion/fusion.py).
_DEFAULT_DEFECTS = {
    "rotten": {"detected": False, "confidence": 0.05},
    "sprout": {"detected": False, "confidence": 0.05},
}


def _vision(label="sound", conf=0.9, is_onion=True, freshness=0.8,
            defects=None):
    return {"is_onion": is_onion,
            "vision": {"label": label, "confidence": conf,
                       "defects": defects if defects is not None else _DEFAULT_DEFECTS,
                       "freshness_score": freshness,
                       "model_version": "vision-test"},
            "warnings": []}


def _acoustic(status="valid", prob=0.1, conf=0.9, verified=True, dataset_type=None):
    """Acoustic contract. `verified=True` declares the ONLY state in which
    acoustic evidence may influence a grade (see src/common/contracts.py)."""
    types = dataset_type or (["verified_onion_acoustic"] if verified
                             else ["synthetic"])
    return {"status": status, "internal_defect_probability": prob,
            "confidence": conf, "model_version": "acoustic-test",
            "dataset_type": types,
            "ground_truth_verified": "verified_onion_acoustic" in types,
            "research_only": "verified_onion_acoustic" not in types}


def test_non_onion_rejection():
    out = fuse_results(_vision(is_onion=False), _acoustic())
    assert out["is_onion"] is False
    assert out["final"]["label"] == "not_onion"
    assert out["final"]["freshness_score"] is None


def test_vision_only_fallback_when_audio_absent():
    out = fuse_results(_vision(), None)
    assert out["status"] == "vision_only"
    assert out["final"]["label"] == "sound"


def test_vision_only_fallback_when_audio_unreliable():
    out = fuse_results(_vision(), _acoustic(status="retest_required"))
    assert out["status"] == "vision_only_audio_unreliable"
    assert "retest_required" in out["final"]["reason"]


def test_vision_uncertain_requires_manual_review():
    out = fuse_results(_vision(label="uncertain", conf=0.3), None)
    assert out["final"]["label"] == "needs_manual_review"
    assert out["final"]["freshness_score"] is None


def test_multimodal_disagreement_flags_manual_review():
    out = fuse_results(_vision(label="sound", conf=0.9),
                       _acoustic(prob=0.85, conf=0.9))
    assert out["final"]["label"] == "needs_manual_review"
    assert out["final"]["reason"] == "multimodal disagreement"
    assert out["status"] == "manual_review"


def test_fused_score_combines_evidence():
    out = fuse_results(_vision(freshness=0.9), _acoustic(prob=0.4, conf=0.9))
    # 0.65*0.9 - 0.35*0.4 = 0.445
    assert out["final"]["freshness_score"] == pytest.approx(0.445, abs=0.01)
    assert out["status"] == "fused"


def test_no_fused_score_is_synthesised_without_a_vision_freshness_model():
    """The real vision model emits freshness_score=None; fusion must not invent one."""
    out = fuse_results(_vision(freshness=None), _acoustic(prob=0.4, conf=0.9))
    assert out["final"]["freshness_score"] is None
    assert out["final"]["visible_defect_score"] is not None
    assert any("freshness_score is null" in w for w in out["warnings"])


def test_low_confidence_acoustic_never_silent():
    out = fuse_results(_vision(), _acoustic(prob=0.2, conf=0.3))
    assert out["status"] == "fused"
    assert any("confidence" in w and "low" in w for w in out["warnings"])


# ------------------------------------------- research-only acoustic safety
def test_synthetic_acoustic_cannot_produce_a_fused_result():
    """A synthetic/demo model must never take part in fusion (Phase K)."""
    out = fuse_results(_vision(label="sound", conf=0.9),
                       _acoustic(prob=0.99, conf=0.99, verified=False))
    assert out["status"] == "vision_only_acoustic_not_validated"
    assert out["acoustic_eligible"] is False
    assert out["final"]["label"] == "sound"
    assert any("research-only" in w for w in out["warnings"])


def test_acoustic_without_verified_metadata_is_not_eligible():
    """Absent metadata is not evidence: silence must not authorise grading."""
    bare = {"status": "valid", "internal_defect_probability": 0.9,
            "confidence": 0.9}
    out = fuse_results(_vision(), bare)
    assert out["status"] == "vision_only_acoustic_not_validated"
    assert out["acoustic_eligible"] is False


# ------------------------------------------------- inference integrations
def test_acoustic_inference_without_model(demo_wav, tmp_path):
    from acoustic_inference import classify_acoustic
    result = classify_acoustic(str(demo_wav),
                               model_path=str(tmp_path / "missing.joblib"))
    assert result["status"] == "model_not_trained"
    assert result["internal_defect_probability"] is None


def test_acoustic_inference_retest_on_silence(tmp_path):
    from acoustic_inference import classify_acoustic
    sr = 8000
    path = tmp_path / "quiet.wav"
    wavfile.write(str(path), sr, np.zeros(int(sr * 1.6), dtype=np.int16))
    result = classify_acoustic(str(path),
                               model_path=str(PROJECT_ROOT / "models" / "acoustic" / "acoustic_baseline.joblib"))
    assert result["status"] == "retest_required"


def test_acoustic_inference_with_demo_model(demo_wav):
    from acoustic_inference import classify_acoustic
    model = PROJECT_ROOT / "models" / "acoustic" / "acoustic_baseline.joblib"
    if not model.exists():
        pytest.skip("demo model not trained yet")
    result = classify_acoustic(str(demo_wav), model_path=str(model))
    assert result["status"] in {"valid", "retest_required", "model_not_trained"}
    if result["status"] == "valid":
        assert 0.0 <= result["internal_defect_probability"] <= 1.0
        assert any("SYNTHETIC" in w for w in result["warnings"])


def test_vision_inference_contract(real_onion_image):
    """Contract test against a real dataset photograph (no untracked folders)."""
    from vision_inference import classify_vision
    try:
        result = classify_vision(str(real_onion_image))
    except RuntimeError as exc:
        pytest.skip(f"torch unavailable in this environment: {exc}")
    if result["status"] == "model_unavailable":
        pytest.skip("attribute artifact not present in this checkout")
    # A 4-class commercial grade or a defect label, plus explicit uncertainty.
    assert result["vision"]["label"] in {"sound", "sprouted", "visibly_rotten",
                                         "reject_grade", "uncertain"}
    assert 0.0 <= result["vision"]["confidence"] <= 1.0
    assert result["vision"]["freshness_score"] is None, (
        "no shelf-life model exists, so none may be reported")
    assert any("field-validated" in w for w in result["warnings"])


def test_demo_onion_scan_script_is_self_contained():
    """The combined demo was deleted once (audit P0.1/P0.3) because it imported
    an untracked local dataset folder. The rewritten script must stay
    self-contained: image/audio come from the command line, and only tracked
    inference modules are imported. The supporting demo scripts must also
    remain in place."""
    script = PROJECT_ROOT / "scripts" / "demo_onion_scan.py"
    assert script.exists(), (
        "scripts/demo_onion_scan.py (combined vision+acoustic demo) is missing")
    src = script.read_text(encoding="utf-8")
    for forbidden in ("Onion Grading", "demo/", "C:\\SIH", "local_data", ".pt\""):
        assert forbidden not in src, (
            f"demo_onion_scan.py must not reference untracked local data "
            f"({forbidden!r}); take --image/--audio from the command line only")
    assert (PROJECT_ROOT / "scripts" / "demo_batch_scan.py").exists()
    assert (PROJECT_ROOT / "scripts" / "demo_deep_scan.py").exists()
