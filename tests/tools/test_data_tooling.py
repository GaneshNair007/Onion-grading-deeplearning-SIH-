"""Tests for the team's data-ingestion tooling (Phase AN).

These scripts are how the project gets better after this session, so their
safety properties are tested like product code: no source file is ever moved or
deleted, duplicates are refused, unknown labels are rejected, and a recording
without cut-open ground truth is never presented as labelled.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import add_cut_open_ground_truth as cut_open            # noqa: E402
import add_labelled_images as add_images                # noqa: E402
import collect_acoustic_sample as collect               # noqa: E402


def _png(path: Path, size: int = 48) -> Path:
    from PIL import Image
    Image.new("RGB", (size, size), (180, 120, 40)).save(path)
    return path


def _tap_wav(path: Path, freq: float = 1200.0, amp: float = 0.5) -> Path:
    sr = 44100
    t = np.linspace(0, 1.6, int(sr * 1.6), endpoint=False)
    sig = amp * np.sin(2 * np.pi * freq * t) * np.exp(-6 * t)
    sig[: int(sr * 0.1)] = 0.004 * np.sin(2 * np.pi * 50 * t[: int(sr * 0.1)])
    wavfile.write(str(path), sr, np.clip(sig, -1, 1).astype(np.float32))
    return path


# --------------------------------------------------------- labelled images
def test_add_labelled_images_copies_never_moves_and_records_provenance(tmp_path):
    source = tmp_path / "photos"
    source.mkdir()
    _png(source / "onion_1.png")
    provenance = tmp_path / "provenance.json"
    out = tmp_path / "dataset-verified"

    code = add_images.main([
        "--source", str(source), "--label", "rotten",
        "--license", "self-collected (team-owned)",
        "--collector", "tester", "--out", str(out),
        "--provenance", str(provenance),
    ])
    assert code == 0
    assert (source / "onion_1.png").exists(), "the source folder must be untouched"
    copied = list((out / "verified_onion_image" / "rotten").glob("*.png"))
    assert len(copied) == 1

    data = json.loads(provenance.read_text(encoding="utf-8"))
    assert len(data["images"]) == 1
    row = data["images"][0]
    assert row["sha256"].startswith("sha256:")
    assert row["label"] == "rotten"
    assert row["dataset_type"] == "verified_onion_image"

    # A second run must refuse the duplicate instead of copying it twice.
    code = add_images.main([
        "--source", str(source), "--label", "rotten",
        "--license", "self-collected (team-owned)",
        "--collector", "tester", "--out", str(out),
        "--provenance", str(provenance),
    ])
    assert code == 0
    data = json.loads(provenance.read_text(encoding="utf-8"))
    assert len(data["images"]) == 1, "duplicate by SHA-256 must be skipped"


def test_add_labelled_images_requires_a_stated_licence(tmp_path):
    source = tmp_path / "photos"
    source.mkdir()
    _png(source / "x.png")
    code = add_images.main([
        "--source", str(source), "--label", "sound",
        "--license", "license not detected", "--collector", "tester",
        "--out", str(tmp_path / "out"),
        "--provenance", str(tmp_path / "p.json"),
    ])
    assert code == 2, "an unstated licence must block registration"


def test_unknown_label_is_rejected_by_argparse(tmp_path):
    source = tmp_path / "photos"
    source.mkdir()
    _png(source / "x.png")
    with pytest.raises(SystemExit):
        add_images.main([
            "--source", str(source), "--label", "definitely_rotten",
            "--license", "self", "--collector", "t", "--out", str(tmp_path / "o"),
            "--provenance", str(tmp_path / "p.json"),
        ])


# ------------------------------------------------------- acoustic capture
def test_collect_acoustic_sample_records_metadata_and_repeatability(tmp_path):
    taps = [_tap_wav(tmp_path / f"tap{i}.wav", freq=f) for i, f in
            enumerate((1150.0, 1200.0, 1250.0), start=1)]
    raw = tmp_path / "raw"
    code = collect.main([
        "--onion-id", "ONION_000123", "--audio", *[str(t) for t in taps],
        "--device", "unit-test-phone", "--variety", "N-53",
        "--position", "equator", "--out", str(raw),
        "--notes", "synthetic test signal",
    ])
    assert code in (0, 3)
    metadata = json.loads((raw / "ONION_000123" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["onion_id"] == "ONION_000123"
    assert metadata["dataset_type"] == "verified_onion_image" or \
        metadata["dataset_type"] == "verified_onion_acoustic"
    assert metadata["dataset_type"] == "verified_onion_acoustic"
    assert len(metadata["taps"]) == 3
    assert metadata["repeatability"]["status"] in {"ok", "retest_required"}
    # The crucial honesty marker: no internal label yet.
    assert metadata["internal_label"] == ""
    assert metadata["ground_truth_method"] == "unknown"
    assert "cut-open" in metadata["warning"].lower() or \
        "cut-open label" in metadata["warning"]


def test_collect_rejects_a_single_unusable_recording(tmp_path):
    silence = tmp_path / "silence.wav"
    wavfile.write(str(silence), 8000, np.zeros(8000, dtype=np.float32))
    code = collect.main([
        "--onion-id", "ONION_000999", "--audio", str(silence),
        "--device", "unit-test-phone", "--out", str(tmp_path / "raw"),
    ])
    assert code == 2, "a recording that fails every quality gate is not saved"


def test_repeatability_flags_inconsistent_taps():
    samples = [
        {"features": {"resonance_peak_hz": 1000.0, "rms_energy": 0.1,
                      "spectral_centroid_hz": 900.0, "decay_rate": 5.0}},
        {"features": {"resonance_peak_hz": 4000.0, "rms_energy": 0.5,
                      "spectral_centroid_hz": 3000.0, "decay_rate": 1.0}},
    ]
    result = collect.repeatability(samples)
    assert result["status"] == "retest_required"
    assert "variation" in result["reason"]


# ------------------------------------------------------ destructive labels
def test_cut_open_ground_truth_requires_a_capture_and_a_photograph(tmp_path):
    raw = tmp_path / "raw"
    (raw / "ONION_000123").mkdir(parents=True)
    (raw / "ONION_000123" / "metadata.json").write_text(
        json.dumps({"onion_id": "ONION_000123", "dataset_type":
                    "verified_onion_acoustic"}), encoding="utf-8")
    photo = _png(tmp_path / "cut.png")

    code = cut_open.main([
        "--onion-id", "ONION_000123", "--internal-label", "soft_rot",
        "--photograph", str(photo), "--labelled-by", "tester",
        "--raw", str(raw),
    ])
    assert code == 0
    ground_truth = json.loads(
        (raw / "ONION_000123" / "ground_truth.json").read_text(encoding="utf-8"))
    assert ground_truth["internal_label"] == "soft_rot"
    assert ground_truth["ground_truth_method"] == "cut_open"
    assert ground_truth["labelled_by"] == "tester"
    assert (raw / "ONION_000123" / "cut_surface.png").exists()

    metadata = json.loads(
        (raw / "ONION_000123" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["ground_truth_verified"] is True
    assert metadata["internal_label"] == "soft_rot"


def test_cut_open_refuses_an_unknown_onion_and_a_missing_photo(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    photo = _png(tmp_path / "cut.png")
    assert cut_open.main([
        "--onion-id", "ONION_999999", "--internal-label", "sound",
        "--photograph", str(photo), "--labelled-by", "t", "--raw", str(raw),
    ]) == 1
    (raw / "ONION_0001").mkdir()
    assert cut_open.main([
        "--onion-id", "ONION_0001", "--internal-label", "sound",
        "--photograph", str(tmp_path / "nope.png"), "--labelled-by", "t",
        "--raw", str(raw),
    ]) == 2


def test_cut_open_refuses_to_silently_relabel(tmp_path):
    raw = tmp_path / "raw"
    (raw / "ONION_0007").mkdir(parents=True)
    (raw / "ONION_0007" / "metadata.json").write_text("{}", encoding="utf-8")
    photo = _png(tmp_path / "cut.png")
    args = ["--onion-id", "ONION_0007", "--internal-label", "hollow",
            "--photograph", str(photo), "--labelled-by", "t", "--raw", str(raw)]
    assert cut_open.main(args) == 0
    assert cut_open.main(args) == 3, "a second label needs --force"
    assert cut_open.main(args + ["--force"]) == 0


# --------------------------------------------------- acoustic training gate
def test_acoustic_training_refuses_without_verified_onion_data(tmp_path):
    """The refusal is the feature: no synthetic model may claim onion metrics."""
    out = subprocess.run(
        [sys.executable, "training/train_acoustic.py",
         "--data", str(tmp_path / "empty"),
         "--require-verified-onion-data"],
        cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert out.returncode != 0
    assert "REFUSING" in out.stdout + out.stderr or \
        "no WAV" in out.stdout + out.stderr
