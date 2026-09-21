"""End-to-end collection-mode tests.

The chain under test is the one that turns a real phone tap into trainable
data: save recording (null label) -> cut-open ground truth (label propagates)
-> the trainer's own loaders find a group id and a trusted label. The honesty
rules are asserted explicitly: labels start null, uncertain/sprouted are
excluded from the binary interior task, re-labelling is refused, and the
status report tells the truth about insufficient data.
"""
from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.acoustic.collection import (  # noqa: E402
    REQUIRED_MINIMUM_ONIONS,
    binary_internal_class,
    collection_status,
    next_onion_id,
    record_ground_truth,
    save_recording,
)


def _tap_wav(path: Path, freq: float = 280.0, seconds: float = 1.0) -> bytes:
    """A tap-shaped WAV (fast attack, exponential decay) as raw bytes.

    Written as 16-bit PCM via the stdlib wave module — the same format the
    scan page encodes in the browser (scipy float32 WAVs are a different
    container that stdlib wave cannot parse).
    """
    sr = 16000
    t = np.arange(int(sr * seconds)) / sr
    sig = 0.5 * np.exp(-t * 25) * np.sin(2 * np.pi * freq * t)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(sig, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path.read_bytes()


def _save(onion_id: str, tmp_path: Path, freq: float = 280.0) -> dict:
    wav = tmp_path / f"in_{onion_id}_{freq}.wav"
    return save_recording(
        _tap_wav(wav, freq=freq), onion_id=onion_id,
        capture_method="phone_tap", position="equator",
        device="pytest", raw_dir=tmp_path / "raw")


# ------------------------------------------------------------------ saving
def test_save_recording_writes_trainer_ready_sidecar(tmp_path):
    out = _save("ONION_000001", tmp_path)
    raw = tmp_path / "raw" / "ONION_000001"
    wav_path = raw / out["audio_file"]
    assert wav_path.exists()
    # ONION id must be inside the filename: the trainer groups by it.
    assert out["audio_file"] == "ONION_000001_phone_tap_equator_01.wav"
    sidecar = json.loads((raw / "ONION_000001_phone_tap_equator_01.json")
                         .read_text(encoding="utf-8"))
    assert sidecar["dataset_type"] == "verified_onion_acoustic"
    assert sidecar["onion_id"] == "ONION_000001"
    assert sidecar["recording_id"] == "AUDIO_000001"  # schema pattern ^AUDIO_\d{6}$
    assert sidecar["internal_label"] is None, "labels start null — never inferred"
    assert sidecar["binary_internal_class"] is None
    assert sidecar["label_verified"] is False
    assert sidecar["sample_rate_hz"] == 16000        # read from the real header
    assert 0.9 < sidecar["duration_seconds"] < 1.1
    assert Path(sidecar["audio_path"]).exists()      # path resolves


def test_recording_ids_are_sequential_and_never_reused(tmp_path):
    a = _save("ONION_000001", tmp_path, freq=280.0)
    b = _save("ONION_000001", tmp_path, freq=300.0)
    c = _save("ONION_000002", tmp_path, freq=320.0)
    assert [a["recording_id"], b["recording_id"], c["recording_id"]] == \
        ["AUDIO_000001", "AUDIO_000002", "AUDIO_000003"]


def test_save_recording_rejects_bad_input(tmp_path):
    with pytest.raises(ValueError):
        save_recording(_tap_wav(tmp_path / "x.wav"), "onion-1",
                       raw_dir=tmp_path / "raw")           # bad onion id
    with pytest.raises(ValueError):
        save_recording(_tap_wav(tmp_path / "x.wav"), "ONION_000001",
                       capture_method="impact_hammer",
                       raw_dir=tmp_path / "raw")           # not a phone method
    with pytest.raises(ValueError):
        save_recording(b"definitely not a wav file", "ONION_000001",
                       raw_dir=tmp_path / "raw")           # non-WAV bytes


def test_next_onion_id_counts_existing_dirs(tmp_path):
    _save("ONION_000007", tmp_path)
    assert next_onion_id(tmp_path / "raw") == "ONION_000008"


# -------------------------------------------------------------- ground truth
def test_ground_truth_propagates_to_sidecars(tmp_path):
    _save("ONION_000001", tmp_path, freq=280.0)
    _save("ONION_000001", tmp_path, freq=300.0)
    photo = tmp_path / "cut.png"
    photo.write_bytes(b"\x89PNG\r\n\x1a\n")   # copied as evidence, never parsed

    result = record_ground_truth(
        "ONION_000001", internal_label="sound", labelled_by="T. Tester",
        photograph=photo, raw_dir=tmp_path / "raw")

    assert result["label_verified"] is True
    assert result["binary_internal_class"] == 0
    assert result["sidecars_updated"] == 2
    raw = tmp_path / "raw" / "ONION_000001"
    gt = json.loads((raw / "ground_truth.json").read_text(encoding="utf-8"))
    assert gt["internal_label"] == "sound"
    assert gt["evidence"]["cut_surface_photograph"] == "cut_surface.png"
    for sidecar_path in sorted(raw.glob("ONION_*.json")):
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert sidecar["internal_label"] == "sound"
        assert sidecar["binary_internal_class"] == 0
        assert sidecar["label_verified"] is True
        assert sidecar["quality_status"] == "ready_for_training_review"


def test_binary_class_mapping():
    assert binary_internal_class("sound") == 0
    assert binary_internal_class("external_defect_only") == 0  # interior sound
    assert binary_internal_class("internal_defect") == 1
    assert binary_internal_class("hollow_or_abnormal") == 1
    assert binary_internal_class("neck_rot") == 1              # rot vocabulary
    assert binary_internal_class("soft_rot") == 1
    assert binary_internal_class("sprouted") is None           # exterior only
    assert binary_internal_class("uncertain") is None          # not ground truth


def test_ground_truth_refuses_invalid_and_relabelling(tmp_path):
    _save("ONION_000001", tmp_path)
    with pytest.raises(ValueError):
        record_ground_truth("ONION_000001", internal_label="probably_fine",
                            labelled_by="T", photograph=None,
                            raw_dir=tmp_path / "raw")       # not in vocabulary
    with pytest.raises(ValueError):
        record_ground_truth("ONION_000001", internal_label="sound",
                            labelled_by="   ", photograph=None,
                            raw_dir=tmp_path / "raw")       # no labeller
    record_ground_truth("ONION_000001", internal_label="sound",
                        labelled_by="T", photograph=None,
                        raw_dir=tmp_path / "raw")
    with pytest.raises(ValueError):
        record_ground_truth("ONION_000001", internal_label="internal_defect",
                            labelled_by="T", photograph=None,
                            raw_dir=tmp_path / "raw")       # re-labelling refused
    with pytest.raises(ValueError):
        record_ground_truth("ONION_000999", internal_label="sound",
                            labelled_by="T", photograph=None,
                            raw_dir=tmp_path / "raw")       # nothing recorded


# ------------------------------------------------------------------ status
def test_collection_status_reports_insufficient_data_honestly(tmp_path):
    st = collection_status(tmp_path / "raw")
    assert st["status"] == "insufficient_verified_data"
    assert st["required_minimum_onions"] == REQUIRED_MINIMUM_ONIONS == 30
    assert st["available_verified_onions"] == 0
    assert st["recordings_total"] == 0

    _save("ONION_000001", tmp_path)          # recorded but NOT labelled
    st = collection_status(tmp_path / "raw")
    assert st["onions_started"] == 1
    assert st["available_verified_onions"] == 0, "unlabelled != verified"
    assert st["status"] == "insufficient_verified_data"

    record_ground_truth("ONION_000001", "sound", "T", None,
                        raw_dir=tmp_path / "raw")
    st = collection_status(tmp_path / "raw")
    assert st["available_verified_onions"] == 1
    assert st["status"] == "insufficient_verified_data"   # 1 < 30 — still true


# ------------------------------------------- the chain the whole project needs
def test_trainer_trains_on_collected_then_labelled_data(tmp_path):
    """collect -> label -> the REAL trainer runs and produces artifacts.

    This is the acceptance test for the entire collection mode: the bytes
    saved by the page must be trainable with zero manual reformatting.
    """
    for freq in (280.0, 300.0):
        _save("ONION_000001", tmp_path, freq=freq)
    for freq in (420.0, 450.0):
        _save("ONION_000002", tmp_path, freq=freq)
    record_ground_truth("ONION_000001", "sound", "T", None,
                        raw_dir=tmp_path / "raw")
    record_ground_truth("ONION_000002", "internal_defect", "T", None,
                        raw_dir=tmp_path / "raw")

    model_dir = tmp_path / "model"
    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "training" / "train_acoustic.py"),
         "--data", str(tmp_path / "raw"), "--out-dir", str(model_dir)],
        capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr[-800:]
    card = json.loads((model_dir / "model_card.json").read_text(encoding="utf-8"))
    assert card["metadata"]["dataset_type"] == ["verified_onion_acoustic"]
    assert "warning" not in card["metadata"], \
        "no synthetic-demo warning may attach to verified-onion training"
    assert (model_dir / "acoustic_baseline.joblib").exists()
    assert card["metrics"]["random_forest"]["n_train"] >= 2


# ------------------------------------------------- legacy CLI parity
def _run_cli_collect(tmp_path: Path) -> Path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import collect_acoustic_sample as collect  # noqa: E402
    tap_paths = [tmp_path / f"tap{i}.wav" for i in (1, 2, 3)]
    for p, f in zip(tap_paths, (280.0, 300.0, 320.0)):
        _tap_wav(p, freq=f)                      # returns bytes; keep the path
    raw = tmp_path / "raw"
    code = collect.main([
        "--onion-id", "ONION_000123", "--audio", *[str(t) for t in tap_paths],
        "--device", "pytest-phone", "--position", "equator",
        "--out", str(raw),
    ])
    assert code in (0, 3)
    return raw


def test_cli_collector_writes_onion_named_taps_with_sidecars(tmp_path):
    raw = _run_cli_collect(tmp_path)
    meta = json.loads((raw / "ONION_000123" / "metadata.json").read_text(encoding="utf-8"))
    assert meta["recording_id"] == "AUDIO_000123"   # schema-pattern compliant
    assert len(meta["taps"]) == 3
    for tap in meta["taps"]:
        assert tap.startswith("ONION_000123_"), \
            "trainer grouping requires the ONION id inside the filename"
        sidecar = json.loads((raw / "ONION_000123" /
                              Path(tap).with_suffix(".json").name)
                             .read_text(encoding="utf-8"))
        assert sidecar["internal_label"] is None
        assert sidecar["label_verified"] is False


def test_cli_ground_truth_propagates_into_sidecars(tmp_path):
    raw = _run_cli_collect(tmp_path)
    photo = tmp_path / "cut.png"
    photo.write_bytes(b"\x89PNG\r\n\x1a\n")
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import add_cut_open_ground_truth as gt_tool  # noqa: E402
    out = gt_tool.main([
        "--onion-id", "ONION_000123", "--internal-label", "internal_defect",
        "--photograph", str(photo), "--labelled-by", "T. Tester",
        "--raw", str(raw),
    ])
    assert out == 0
    sidecars = sorted((raw / "ONION_000123").glob("ONION_*.json"))
    assert sidecars, "collector must write per-WAV sidecars"
    for sidecar_path in sidecars:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert sidecar["internal_label"] == "internal_defect"
        assert sidecar["binary_internal_class"] == 1
        assert sidecar["label_verified"] is True
