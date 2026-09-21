"""Live data-collection mode: save each real tap/chirp recording with the
metadata needed to eventually train a REAL onion acoustic model.

This module is the storage backbone for phone-only collection
(`dataset-acoustic/collection_protocol.md`). It is deliberately strict:

* Every recording is stored as ``<ONION_ID>_<method>_<position>_<NN>.wav``
  plus a per-WAV JSON sidecar. The trainer
  (``training/train_acoustic.py``) needs the ONION id inside the *filename*
  for leak-safe grouping and reads the sidecar for the label — one format,
  no drift.
* ``internal_label`` starts as ``None`` and is ONLY set by the cut-open
  ground-truth step (``record_ground_truth``). Labels are never inferred
  from audio, filenames or acoustics.
* Unknown values are stored as ``None`` — never guessed.
* The trainability summary returns the exact honesty contract of the
  project: until enough verified onions exist, the status is
  ``insufficient_verified_data`` with the counts attached.

Binary class mapping (used only for the internal-defect screening task):

=========================  ======  =====================================
internal_label             class   meaning
=========================  ======  =====================================
sound                      0       interior verified sound
external_defect_only       0       exterior defect, interior verified sound
internal_defect            1       interior defect verified
hollow_or_abnormal         1       interior structurally abnormal
sprouted                   None    exterior condition — excluded from the
                                   binary interior task
uncertain                  None    excluded (an uncertain label is not
                                   ground truth)
=========================  ======  =====================================

The richer rot vocabulary of ``scripts/add_cut_open_ground_truth.py``
(neck_rot, soft_rot, ...) maps by the same defect rule: any label containing
rot / hollow / defect / abnormal / unhealthy -> 1, sound -> 0.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Live collection target. Override with ONIONQ_ACOUSTIC_RAW_DIR for testing
# so a live session never writes into the real dataset tree.
RAW_DIR = Path(os.environ.get("ONIONQ_ACOUSTIC_RAW_DIR") or
               PROJECT_ROOT / "dataset-acoustic" / "raw")

ONION_ID_RE = re.compile(r"^ONION_\d{6}$")
RECORDING_ID_RE = re.compile(r"^AUDIO_\d{6}$")

#: Initial label vocabulary (project spec) + the existing rot vocabulary of
#: scripts/add_cut_open_ground_truth.py. Union — both tools accept both.
INTERNAL_LABELS = (
    "sound", "internal_defect", "external_defect_only", "sprouted",
    "hollow_or_abnormal", "uncertain",
    "neck_rot", "soft_rot", "internal_sprouting", "hollow",
    "watery_translucent", "other",
)
GROUND_TRUTH_METHODS = ("cut_open", "expert_inspection", "unknown")

CAPTURE_METHODS = ("phone_tap", "phone_chirp", "unknown")
POSITIONS = ("neck", "equator", "base", "unknown")

#: Minimum verified onions before any metric may be quoted (project rule).
REQUIRED_MINIMUM_ONIONS = 30

#: Labels that count as "interior defect" for the binary screening task.
_DEFECT_WORDS = ("rot", "hollow", "defect", "abnormal", "unhealthy")
_SOUND_EXACT = {"sound", "external_defect_only"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_rel(path: Path) -> str:
    """Repository-relative posix path; absolute fallback for tmp dirs."""
    path = Path(path).resolve()
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def validate_onion_id(onion_id: str) -> str:
    if not ONION_ID_RE.match(onion_id or ""):
        raise ValueError(
            f"onion_id must match ONION_xxxxxx (6 digits), got {onion_id!r}")
    return onion_id


def next_onion_id(raw_dir: Path = RAW_DIR) -> str:
    """Deterministic next id: highest existing ONION_xxxxxx + 1."""
    raw_dir = Path(raw_dir)
    highest = 0
    if raw_dir.exists():
        for entry in raw_dir.iterdir():
            m = re.match(r"^ONION_(\d{6})$", entry.name)
            if entry.is_dir() and m:
                highest = max(highest, int(m.group(1)))
    return f"ONION_{highest + 1:06d}"


def _next_recording_id(raw_dir: Optional[Path] = None) -> str:
    """Sequential AUDIO_xxxxxx id, schema-pattern compliant, no reuse."""
    raw_dir = RAW_DIR if raw_dir is None else Path(raw_dir)
    highest = 0
    if raw_dir.exists():
        for sidecar in raw_dir.rglob("*.json"):
            if sidecar.name in ("metadata.json", "ground_truth.json"):
                continue
            try:
                head = sidecar.read_text(encoding="utf-8")[:400]
            except OSError:
                continue
            for match in re.finditer(r"AUDIO_(\d{6})", head):
                highest = max(highest, int(match.group(1)))
    return f"AUDIO_{highest + 1:06d}"


def next_recording_id(raw_dir: Optional[Path] = None) -> str:
    """Public helper: next free AUDIO_xxxxxx id (schema pattern)."""
    return _next_recording_id(RAW_DIR if raw_dir is None else Path(raw_dir))


def parse_wav_header(path: Path) -> Dict[str, Any]:
    """Real header values from the file — never assumed."""
    with wave.open(str(path), "rb") as w:
        return {
            "sample_rate_hz": int(w.getframerate()),
            "channels": int(w.getnchannels()),
            "duration_seconds": round(w.getnframes() / w.getframerate(), 4),
            "sample_width_bytes": int(w.getsampwidth()),
        }


def write_sidecar(path: Path, recording_id: str, onion_id: str,
                  capture_method: str, position: str, device: str,
                  header: Dict[str, Any], raw_dir: Path = RAW_DIR) -> Path:
    """Write the per-WAV sidecar the trainer reads. Label fields stay None."""
    sidecar = {
        "recording_id": recording_id,
        "onion_id": onion_id,
        "dataset_type": "verified_onion_acoustic",
        "audio_path": _repo_rel(path),
        "format": "wav",
        "sample_rate_hz": header.get("sample_rate_hz"),
        "channels": header.get("channels"),
        "duration_seconds": header.get("duration_seconds"),
        "capture_method": capture_method,
        "device": device or None,
        "position": position,
        "external_label": None,          # filled by visual assessment, if ever
        "internal_label": None,          # ONLY the cut-open step sets this
        "binary_internal_class": None,   # derived ONLY at ground-truth time
        "ground_truth_method": "unknown",
        "label_verified": False,
        "quality_status": "pending",
        "split": "not_applicable",       # assigned later at ONION level
        "captured_at": _now(),
        "notes": "",
    }
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return sidecar_path


def binary_internal_class(internal_label: str) -> Optional[int]:
    label = internal_label.lower()
    if label == "uncertain":
        return None
    if label in _SOUND_EXACT:
        return 0
    if any(word in label for word in _DEFECT_WORDS):
        return 1
    if label == "sprouted":
        return None                      # exterior condition, not interior
    if label == "sound":
        return 0
    return None


def save_recording(wav_bytes: bytes, onion_id: str,
                   capture_method: str = "phone_tap",
                   position: str = "equator",
                   device: str = "",
                   os_version: str = "",
                   notes: str = "",
                   raw_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Save one recording (copy-only) with its sidecar and return a manifest.

    Raises ValueError on bad ids/fields; raises wave.Error on non-WAV bytes.
    Never infers or invents any label.
    """
    validate_onion_id(onion_id)
    raw_dir = RAW_DIR if raw_dir is None else Path(raw_dir)
    if capture_method not in CAPTURE_METHODS:
        raise ValueError(f"capture_method must be one of {CAPTURE_METHODS}")
    if position not in POSITIONS:
        raise ValueError(f"position must be one of {POSITIONS}")

    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(wav_bytes)
    tmp.close()
    tmp_path = Path(tmp.name)
    try:
        header = parse_wav_header(tmp_path)          # validates WAV structure
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"not a readable WAV file: {exc}") from exc

    target_dir = Path(raw_dir) / onion_id
    target_dir.mkdir(parents=True, exist_ok=True)
    seq = len(list(target_dir.glob(f"{onion_id}_{capture_method}_{position}_*.wav"))) + 1
    if seq > 99:
        tmp_path.unlink(missing_ok=True)
        raise ValueError("more than 99 recordings for one onion/position; "
                         "stop collecting and reassess the protocol")
    name = f"{onion_id}_{capture_method}_{position}_{seq:02d}.wav"
    destination = target_dir / name
    shutil.copy2(tmp_path, destination)              # copy semantics
    tmp_path.unlink(missing_ok=True)

    recording_id = _next_recording_id(raw_dir)
    sidecar_path = write_sidecar(destination, recording_id, onion_id,
                                 capture_method, position, device, header,
                                 raw_dir)

    _update_onion_metadata(target_dir, onion_id, name, capture_method,
                           position, device, os_version, header, notes)
    return {
        "recording_id": recording_id,
        "onion_id": onion_id,
        "audio_file": name,
        "sidecar": _repo_rel(sidecar_path),
        "header": header,
        "internal_label": None,
        "label_verified": False,
        "next_step": ("after recording all views: cut the onion open and run "
                      "POST /acoustic/ground-truth (or "
                      "scripts/add_cut_open_ground_truth.py)"),
    }


def _update_onion_metadata(target_dir: Path, onion_id: str, name: str,
                           capture_method: str, position: str, device: str,
                           os_version: str, header: Dict[str, Any],
                           notes: str) -> None:
    meta_path = target_dir / "metadata.json"
    meta: Dict[str, Any] = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    taps = meta.get("taps") or []
    if name not in taps:
        taps.append(name)
    meta.update({
        "recording_id": meta.get("recording_id") or f"AUDIO_{onion_id.split('_')[1]}",
        "onion_id": onion_id,
        "dataset_type": "verified_onion_acoustic",
        "capture_method": capture_method,
        "position": position,
        "device": device or None,
        "os_version": os_version or None,
        "sample_rate_hz": header.get("sample_rate_hz"),
        "channels": header.get("channels"),
        "duration_seconds": header.get("duration_seconds"),
        "taps": taps,
        "external_label": meta.get("external_label"),
        "internal_label": meta.get("internal_label"),
        "ground_truth_method": meta.get("ground_truth_method", "unknown"),
        "ground_truth_verified": meta.get("ground_truth_verified", False),
        "redistribution_allowed": False,
        "collected_at": meta.get("collected_at") or _now(),
        "last_capture_at": _now(),
        "notes": notes or meta.get("notes", ""),
        "warning": ("No internal ground truth yet. A recording without a "
                    "cut-open label cannot train an internal-defect "
                    "classifier."),
    })
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def record_ground_truth(onion_id: str, internal_label: str,
                        labelled_by: str, photograph: Optional[Path],
                        method: str = "cut_open",
                        notes: str = "",
                        raw_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Cut-open ground truth: the only step allowed to set internal_label.

    Writes ground_truth.json (with photograph evidence), propagates the label
    into every per-WAV sidecar of this onion so the trainer can find it, and
    derives the binary class from the documented mapping above.
    """
    validate_onion_id(onion_id)
    raw_dir = RAW_DIR if raw_dir is None else Path(raw_dir)
    if internal_label not in INTERNAL_LABELS:
        raise ValueError(f"internal_label must be one of {INTERNAL_LABELS}")
    if method not in GROUND_TRUTH_METHODS:
        raise ValueError(f"method must be one of {GROUND_TRUTH_METHODS}")
    if not labelled_by or not labelled_by.strip():
        raise ValueError("labelled_by is required (who cut and inspected?)")

    target_dir = Path(raw_dir) / onion_id
    if not target_dir.exists():
        raise ValueError(f"no recordings for {onion_id}: {target_dir}")
    gt_path = target_dir / "ground_truth.json"
    if gt_path.exists():
        raise ValueError(
            f"{onion_id} already has cut-open ground truth; re-labelling is a "
            "correction — use scripts/add_cut_open_ground_truth.py --force "
            "with a note explaining why the label changed.")

    binary = binary_internal_class(internal_label)
    photo_name = None
    if photograph is not None:
        if not Path(photograph).exists():
            raise ValueError(f"photograph not found: {photograph}")
        dest = target_dir / f"cut_surface{Path(photograph).suffix.lower()}"
        shutil.copy2(photograph, dest)
        photo_name = dest.name

    payload = {
        "onion_id": onion_id,
        "ground_truth_method": method,
        "internal_label": internal_label,
        "binary_internal_class": binary,
        "labelled_by": labelled_by.strip(),
        "label_verified": True,
        "labelled_at": _now(),
        "evidence": {
            "cut_surface_photograph": photo_name,
            "notes": notes,
        },
        "warning": ("A single onion is one sample. Never quote classifier "
                    "metrics from a handful of cut-open labels."),
    }
    (target_dir / "ground_truth.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")

    sidecars = _propagate(target_dir, onion_id, internal_label, binary,
                          method, labelled_by)

    meta_path = target_dir / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["internal_label"] = internal_label
        meta["binary_internal_class"] = binary
        meta["ground_truth_method"] = method
        meta["ground_truth_verified"] = True
        meta["labelled_by"] = labelled_by.strip()
        meta.pop("warning", None)
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "onion_id": onion_id,
        "internal_label": internal_label,
        "binary_internal_class": binary,
        "label_verified": True,
        "sidecars_updated": sidecars,
        "photograph": photo_name,
    }


def propagate_label_to_sidecars(target_dir: Path, onion_id: str,
                                internal_label: str, binary: Optional[int],
                                method: str, labelled_by: str) -> int:
    """Push a verified label into every per-WAV sidecar of one onion.

    Shared by record_ground_truth and scripts/add_cut_open_ground_truth.py so
    both labelling paths produce the same trainer-readable format.
    """
    return _propagate(target_dir, onion_id, internal_label, binary, method,
                      labelled_by)


def _propagate(target_dir: Path, onion_id: str, internal_label: str,
               binary: Optional[int], method: str, labelled_by: str) -> int:
    sidecars = 0
    for sidecar_path in sorted(Path(target_dir).glob(f"{onion_id}_*.json")):
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["internal_label"] = internal_label
        sidecar["binary_internal_class"] = binary
        sidecar["ground_truth_method"] = method
        sidecar["label_verified"] = True
        sidecar["labelled_by"] = labelled_by.strip()
        sidecar["quality_status"] = "ready_for_training_review"
        sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
        sidecars += 1
    return sidecars


def collection_status(raw_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Honest trainability summary in the project's standard JSON shape."""
    raw_dir = RAW_DIR if raw_dir is None else Path(raw_dir)
    onions: Dict[str, Dict[str, int]] = {}
    if raw_dir.exists():
        for sidecar_path in raw_dir.glob("ONION_*/*.json"):
            if sidecar_path.name in ("metadata.json", "ground_truth.json"):
                continue
            onion_id = sidecar_path.parent.name
            entry = onions.setdefault(onion_id, {"recordings": 0, "labelled": 0})
            entry["recordings"] += 1
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            if sidecar.get("label_verified"):
                entry["labelled"] += 1

    verified_onions = [o for o, v in onions.items() if v["labelled"] > 0]
    total_recordings = sum(v["recordings"] for v in onions.values())
    total_labelled = sum(v["labelled"] for v in onions.values())

    summary: Dict[str, Any] = {
        "status": "insufficient_verified_data",
        "reason": (f"only {len(verified_onions)} verified onion(s) with "
                   f"cut-open labels; internal-defect metrics require "
                   f"{REQUIRED_MINIMUM_ONIONS}"),
        "required_minimum_onions": REQUIRED_MINIMUM_ONIONS,
        "available_verified_onions": len(verified_onions),
        "onions_started": len(onions),
        "next_onion_id": next_onion_id(raw_dir),
        "recordings_total": total_recordings,
        "recordings_labelled": total_labelled,
        "onions": onions,
        "next_actions": [
            "collect 3 taps per onion with POST /acoustic/collect",
            "cut open and submit the interior label + photograph via "
            "POST /acoustic/ground-truth",
        ],
    }
    if len(verified_onions) >= REQUIRED_MINIMUM_ONIONS:
        summary["status"] = "ready_for_training"
        summary["reason"] = "enough verified onions to train with quoted metrics"
        summary["train_command"] = ("python training/train_acoustic.py --data "
                                    "dataset-acoustic/raw "
                                    "--require-verified-onion-data")
    return summary
