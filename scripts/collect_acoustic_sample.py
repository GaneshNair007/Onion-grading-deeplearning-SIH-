#!/usr/bin/env python3
"""Register a real phone acoustic capture for one onion (Phase AN / §31).

Copies the taps into ``dataset-acoustic/raw/<ONION_ID>/`` with a metadata
sidecar matching ``dataset-acoustic/metadata_schema.json``, and checks
repeatability across the taps. A sample that fails the repeatability check is
recorded as ``retest_required`` rather than quietly averaged.

Three taps are expected. The variance between them is data quality, not noise to
be hidden: an onion whose response changes every tap was not measured reliably,
and a classifier trained on such samples learns the measurement error.

Usage:
    python scripts/collect_acoustic_sample.py \
        --onion-id ONION_000123 --variety "N-53" \
        --device "Pixel 7a / Android 14" --capture-method phone_tap \
        --position equator \
        --audio tap1.wav tap2.wav tap3.wav --ambient ambient.wav
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.acoustic.collection import write_sidecar  # noqa: E402
from src.acoustic.collection import next_recording_id  # noqa: E402
from src.acoustic.features import analyze_file  # noqa: E402

RAW_DIR = PROJECT_ROOT / "dataset-acoustic" / "raw"
CAPTURE_METHODS = ("phone_tap", "phone_chirp", "impact_hammer", "vibrometry",
                   "unknown")
POSITIONS = ("neck", "equator", "base", "unknown")
#: Coefficient of variation above which the taps disagree too much to be used.
REPEATABILITY_CV_LIMIT = 0.35


def _sample_features(path: Path) -> Dict[str, Any]:
    result = analyze_file(path)
    return {
        "path": str(path),
        "quality_passed": result["features"] is not None,
        "quality": result.get("quality"),
        "features": result.get("features"),
        "error": result.get("error"),
    }


def repeatability(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Coefficient of variation of the features that carry the physics."""
    keys = ("resonance_peak_hz", "rms_energy", "spectral_centroid_hz",
            "decay_rate")
    usable = [s for s in samples if s["features"]]
    out: Dict[str, Any] = {"n_usable": len(usable), "cv": {}, "status": "unknown",
                           "limit": REPEATABILITY_CV_LIMIT}
    if len(usable) < 2:
        out["status"] = "retest_required"
        out["reason"] = ("fewer than two usable taps; a single recording cannot "
                         "demonstrate repeatability")
        return out
    worst = 0.0
    for key in keys:
        values = [float(s["features"][key]) for s in usable
                  if s["features"].get(key) is not None]
        if len(values) < 2:
            continue
        mean = statistics.fmean(values)
        if mean == 0:
            continue
        cv = statistics.pstdev(values) / abs(mean)
        out["cv"][key] = round(cv, 4)
        worst = max(worst, cv)
    out["worst_cv"] = round(worst, 4)
    out["status"] = ("ok" if worst <= REPEATABILITY_CV_LIMIT
                     else "retest_required")
    if out["status"] != "ok":
        out["reason"] = (f"tap-to-tap variation {worst:.2f} exceeds the "
                         f"{REPEATABILITY_CV_LIMIT} limit")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--onion-id", required=True,
                    help="ONION_xxxxxx identifier shared by all views/recordings")
    ap.add_argument("--audio", type=Path, nargs="+", required=True)
    ap.add_argument("--ambient", type=Path, default=None)
    ap.add_argument("--capture-method", default="phone_tap",
                    choices=CAPTURE_METHODS)
    ap.add_argument("--position", default="equator", choices=POSITIONS)
    ap.add_argument("--device", required=True)
    ap.add_argument("--os-version", default="")
    ap.add_argument("--variety", default="")
    ap.add_argument("--weight-g", type=float, default=None)
    ap.add_argument("--diameter-mm", type=float, default=None)
    ap.add_argument("--recording-volume", type=float, default=None)
    ap.add_argument("--image-ids", nargs="*", default=[])
    ap.add_argument("--dataset-type", default="verified_onion_acoustic",
                    choices=("verified_onion_acoustic",
                             "related_produce_acoustic",
                             "generic_audio_pretraining", "synthetic"))
    ap.add_argument("--notes", default="")
    ap.add_argument("--out", type=Path, default=RAW_DIR)
    ap.add_argument("--recording-id", dest="recording_id", default=None,
                    help="explicit AUDIO_xxxxxx id; auto-assigned (next free) "
                         "when omitted")
    args = ap.parse_args(argv)
    if args.recording_id is None:
        from src.acoustic.collection import next_recording_id
        args.recording_id = next_recording_id(args.out)

    missing = [str(p) for p in args.audio if not Path(p).exists()]
    if missing:
        print(f"ERROR: audio file(s) not found: {missing}", file=sys.stderr)
        return 1

    samples = [_sample_features(Path(p)) for p in args.audio]
    repeat = repeatability(samples)
    usable = [s for s in samples if s["quality_passed"]]
    if not usable:
        print(json.dumps({
            "status": "retest_required",
            "reason": "no tap passed the audio quality gates",
            "samples": [{k: v for k, v in s.items() if k != "features"}
                        for s in samples],
        }, indent=2), file=sys.stderr)
        return 2

    target_dir = args.out / args.onion_id
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: List[str] = []
    for index, sample in enumerate(samples, 1):
        source = Path(sample["path"])
        # ONION id in the filename: training/train_acoustic.py groups the
        # leak-safe split by this token, so it must be present.
        destination = target_dir / f"{args.onion_id}_{args.capture_method}_{args.position}_{index:02d}{source.suffix.lower()}"
        shutil.copy2(source, destination)          # copy only
        copied.append(destination.name)
        # Per-WAV sidecar in the trainer's exact format: label fields stay
        # empty until the cut-open ground-truth step fills them. Each tap is a
        # distinct recording and gets its own unique AUDIO_xxxxxx id.
        header = {"sample_rate_hz": (sample["quality"] or {}).get("sample_rate_hz"),
                  "channels": 1,
                  "duration_seconds": (sample["quality"] or {}).get("duration_seconds")}
        tap_recording_id = next_recording_id(args.out)
        sidecar_path = write_sidecar(destination, tap_recording_id,
                                     args.onion_id, args.capture_method,
                                     args.position, args.device, header,
                                     raw_dir=args.out)
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["notes"] = args.notes
        sidecar["quality_status"] = ("passed" if sample["quality_passed"]
                                     else "retest_required")
        sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    ambient_name = None
    if args.ambient and Path(args.ambient).exists():
        ambient_destination = target_dir / f"ambient{Path(args.ambient).suffix.lower()}"
        shutil.copy2(args.ambient, ambient_destination)
        ambient_name = ambient_destination.name

    metadata: Dict[str, Any] = {
        "recording_id": f"AUDIO_{int(args.onion_id.split('_')[1]):06d}",
        "onion_id": args.onion_id,
        "dataset_type": args.dataset_type,
        "source_name": "team field collection",
        "source_url": "",
        "paper_doi": "",
        "license": "self-collected (team-owned); redistribution decision pending",
        "audio_path": copied[0] if copied else "",
        "format": "wav",
        "sample_rate_hz": (usable[0]["quality"] or {}).get("sample_rate_hz"),
        "channels": 1,
        "duration_seconds": (usable[0]["quality"] or {}).get("duration_seconds"),
        "capture_method": args.capture_method,
        "device": args.device,
        "os_version": args.os_version,
        "recording_volume": args.recording_volume,
        "position": args.position,
        "variety": args.variety,
        "weight_g": args.weight_g,
        "diameter_mm_field": args.diameter_mm,
        "external_label": "",
        "internal_label": "",          # filled by the cut-open step
        "ground_truth_method": "unknown",
        "split": "not_applicable",
        "redistribution_allowed": False,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "image_ids": args.image_ids,
        "taps": copied,
        "ambient_file": ambient_name,
        "capture_quality": [s["quality"] for s in samples],
        "repeatability": repeat,
        "collection_status": repeat["status"],
        "notes": args.notes,
        "warning": ("No internal ground truth yet. A recording without a "
                    "cut-open label cannot train or validate an internal-defect "
                    "classifier. Run scripts/add_cut_open_ground_truth.py."),
    }
    (target_dir / "metadata.json").write_text(json.dumps(metadata, indent=2),
                                              encoding="utf-8")
    print(json.dumps({
        "onion_id": args.onion_id,
        "recording_id": args.recording_id,
        "saved_to": str(target_dir),
        "taps_saved": len(copied),
        "sidecars_written": len(copied),
        "repeatability": repeat,
        "collection_status": repeat["status"],
        "next_step": "python scripts/add_cut_open_ground_truth.py "
                     f"--onion-id {args.onion_id} --internal-label <label> "
                     "--photograph cut.jpg --labelled-by '<name>'",
    }, indent=2))
    return 0 if repeat["status"] == "ok" else 3


if __name__ == "__main__":
    raise SystemExit(main())
