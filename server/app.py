"""ONION-Q API service (FastAPI).

Exposes exactly the functions the mobile app calls, plus sync, verification and
dashboard endpoints. It is a thin layer: all logic lives in `src/` and
`inference/`, so the API cannot drift from the demos and tests.

Run:
    uvicorn server.app:app --reload --port 8000
Doc:
    http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from inference.combined_scan import (classify_acoustic, classify_vision,  # noqa: E402
                                     deep_scan_onion, fuse_results,
                                     record_ambient_baseline, save_scan_result,
                                     scan_onion_image, scan_tray_batch)
from server.store import Store                                      # noqa: E402
from src.grading.policy import active_policy, available_policies    # noqa: E402
from src.reporting.audit_hash import verify_integrity               # noqa: E402
from src.reporting.evidence import hash_evidence                    # noqa: E402
from src.reporting.annotation import persist_annotated_evidence     # noqa: E402
from src.reporting.generator import build_report, finalize, write_report  # noqa: E402
from src.vision.multi_view import GUIDED_VIEWS, view_instructions   # noqa: E402

APP_VERSION = "0.1.0"

app = FastAPI(
    title="ONION-Q API",
    version=APP_VERSION,
    description=("AI-assisted onion procurement grading. The API measures; the "
                 "versioned policy engine decides. Uncertain cases are escalated "
                 "to manual review with a reason code."),
)

# ------------------------------------------------------------------ CORS
# Your website runs on its own origin; the browser needs explicit permission
# to call this API. Origins come from ONIONQ_CORS_ORIGINS (comma-separated).
# NOTE: allow_credentials=True requires explicit origins (never "*").
import os as _os

_CORS_ORIGINS = [
    o.strip() for o in _os.environ.get("ONIONQ_CORS_ORIGINS", "").split(",")
    if o.strip()
]
if _CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

_store: Optional[Store] = None

# Serve the dashboard from the same origin as the API so a single
# ``uvicorn server.app:app`` launch gives the full demo (Phase AT walkthrough).
# NOTE: mounted at /dashboard/app, NOT /dashboard — a /dashboard mount would
# shadow the /dashboard/summary, /dashboard/overrides and /dashboard/scans API
# routes (mounts match before routes for sub-paths of the mount prefix).
_dashboard_dir = PROJECT_ROOT / "dashboard"
if _dashboard_dir.exists():
    app.mount("/dashboard/app", StaticFiles(directory=str(_dashboard_dir), html=True),
              name="dashboard")

_report_files_dir = PROJECT_ROOT / "reports" / "evidence"
_report_files_dir.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts/evidence", StaticFiles(directory=str(_report_files_dir)),
          name="report-evidence")


def store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def _registry_summary() -> Dict[str, Any]:
    import json
    path = PROJECT_ROOT / "models" / "registry.json"
    if not path.exists():
        return {"models": {}, "note": "run scripts/build_model_registry.py"}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "registry_version": data.get("registry_version"),
        "generated_at": data.get("generated_at"),
        "git_commit": data.get("git_commit"),
        "models": {k: {"task": v.get("task"),
                       "artifact": v.get("artifact_path"),
                       "metrics_confidence": v.get("metrics_confidence"),
                       "limitations": v.get("limitations", [])}
                   for k, v in (data.get("models") or {}).items()},
        "not_available": data.get("not_available", []),
    }


# --------------------------------------------------------------------- meta
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "app_version": APP_VERSION}


@app.post("/integrations/supabase/push")
def supabase_push(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Push reports (dir of local report JSONs, or a single report) to Supabase.

    Requires ONIONQ_SUPABASE_URL + ONIONQ_SUPABASE_SERVICE_KEY in the
    environment; otherwise responds honestly that syncing is disabled.
    """
    from src.integrations.supabase_sync import SupabaseSync, sync_reports_dir

    s = SupabaseSync()
    if not s.can_write:
        return {"synced": 0, "status": s.status(),
                "reason": "set ONIONQ_SUPABASE_URL and "
                          "ONIONQ_SUPABASE_SERVICE_KEY in .env"}
    single = payload.get("report") if isinstance(payload, dict) else None
    if single:
        return {"result": s.upsert_report(single), "status": s.status()}
    reports_dir = payload.get("reports_dir", "reports")
    return sync_reports_dir(reports_dir=reports_dir)


@app.get("/version")
def version() -> Dict[str, Any]:
    return {"app_version": APP_VERSION, "models": _registry_summary()}


@app.get("/policies")
def policies() -> Dict[str, Any]:
    out = {}
    for name in available_policies():
        policy = active_policy(name)
        out[name] = policy.summary()
    return {"policies": out, "default": "demo_policy"}


@app.get("/models")
def models() -> Dict[str, Any]:
    return _registry_summary()


@app.get("/views")
def views() -> Dict[str, Any]:
    return {"views": GUIDED_VIEWS, "instructions": view_instructions()}


# --------------------------------------------------------------------- scan
@app.post("/scan/image")
async def scan_image(image: UploadFile = File(...),
                     policy: str = Form("demo_policy"),
                     require_calibration: bool = Form(True)) -> Dict[str, Any]:
    with _tmp_upload(image) as path:
        return scan_onion_image(str(path), policy,
                                require_calibration=require_calibration)


@app.post("/scan/batch")
async def scan_batch(images: List[UploadFile] = File(...),
                     center_id: str = Form("MH-NSK"),
                     inspector_id: str = Form("INSP-001"),
                     batch_id: Optional[str] = Form(None),
                     lot_id: Optional[str] = Form(None),
                     policy: str = Form("demo_policy"),
                     require_calibration: bool = Form(True)) -> Dict[str, Any]:
    if not images:
        raise HTTPException(status_code=400, detail="no images supplied")
    with _tmp_uploads(images) as paths:
        result = scan_tray_batch(paths, policy, center_id=center_id,
                                 inspector_id=inspector_id, batch_id=batch_id,
                                 lot_id=lot_id,
                                 require_calibration=require_calibration)
        persisted = persist_annotated_evidence(
            [str(p) for p in paths], result, _report_files_dir)
    evidence = []
    annotated_images = []
    for item in persisted:
        evidence.append(hash_evidence("original_image", item["original_path"]))
        evidence.append(hash_evidence("annotated_image", item["annotated_path"]))
        name = Path(item["annotated_path"]).name
        annotated_images.append({
            "url": f"/artifacts/evidence/{name}",
            "filename": name,
        })
    report = finalize(build_report(
        result["batch"],
        [{"onion_id": o["onion_id"], "source_image": o["source_image"],
          "decision": o["decision"]["decision"],
          "reason_codes": o["decision"]["reason_codes"],
          "measurements": o["measurements"]} for o in result["onions"]],
        evidence=evidence,
        demo_mode=not result["policy"].get("source_verified", False),
        app_version=APP_VERSION))
    write_report(report, PROJECT_ROOT / "reports")
    _store_report(report)
    result["report"] = {"report_id": report["report_id"],
                        "report_hash": report["integrity"]["canonical_hash"],
                        "qr_payload": report["qr_payload"]}
    result["annotated_images"] = annotated_images
    return result


@app.post("/scan/deep")
async def scan_deep(neck: Optional[UploadFile] = File(None),
                    base: Optional[UploadFile] = File(None),
                    side_a: Optional[UploadFile] = File(None),
                    side_b: Optional[UploadFile] = File(None),
                    audio: Optional[UploadFile] = File(None),
                    policy: str = Form("demo_policy")) -> Dict[str, Any]:
    with _tmp_uploads([f for f in (neck, base, side_a, side_b) if f]) as paths, \
            _tmp_upload(audio) as audio_path:
        mapping = {name: str(path) for name, path in zip(
            [f.filename for f in (neck, base, side_a, side_b) if f], paths)}
        # Map uploaded files onto guided view names by position.
        named = dict(zip(GUIDED_VIEWS,
                         [str(p) for p in paths]))
        if not named:
            raise HTTPException(status_code=400, detail="no view images supplied")
        result = deep_scan_onion(named, policy,
                                 audio_path=str(audio_path) if audio_path else None)
    result["uploaded"] = mapping
    return result


# ------------------------------------------------------- gate calibration
@app.post("/acoustic/calibration-capture")
async def calibration_capture(audio: UploadFile = File(...),
                              kind: str = Form(...),
                              device: str = Form(""),
                              distance_cm: str = Form(""),
                              notes: str = Form("")) -> Dict[str, Any]:
    """Save a labeled calibration recording and return its raw gate metrics.

    ``kind``: chirp_valid (chirp with onion present), chirp_room (chirp,
    onion absent), tap_valid, noise_room, noise_swell. Stored under
    local_data/gate_calibration/ (gitignored) — calibration data, not
    dataset. Returns the gate's measured dict so the page can show it and
    the evaluator can sweep thresholds over real measurements.
    """
    import wave as _wave
    from src.acoustic.impact_gate import check_impact_present
    from src.acoustic.loading import load_wav

    valid_kinds = {"chirp_valid", "chirp_room", "tap_valid", "noise_room",
                   "noise_swell"}
    if kind not in valid_kinds:
        raise HTTPException(status_code=400, detail=f"kind must be one of {sorted(valid_kinds)}")
    with _tmp_upload(audio) as path:
        try:
            _, sig = load_wav(str(path))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"unreadable WAV: {exc}")
        import numpy as _np
        try:
            with _wave.open(str(path), "rb") as w:
                sr = int(w.getframerate())
        except Exception:
            sr = 0
        gate = check_impact_present(
            sig, sr, capture_method=("phone_chirp" if kind.startswith("chirp")
                                     else "phone_tap" if kind.startswith("tap")
                                     else None),
            noise_floor_rms=None)
        dest_dir = Path("local_data/gate_calibration")
        dest_dir.mkdir(parents=True, exist_ok=True)
        import time as _time
        name = f"{kind}_{_time.strftime('%H%M%S')}.wav"
        (dest_dir / name).write_bytes(Path(path).read_bytes())
        (dest_dir / (name[:-4] + ".json")).write_text(
            json.dumps({"kind": kind, "device": device, "distance_cm": distance_cm,
                        "notes": notes, "measured": gate["measured"],
                        "passed_current_gate": gate["passed"],
                        "reasons": gate["reasons"]}, indent=2), encoding="utf-8")
        return {"saved": name, "kind": kind, "measured": gate["measured"],
                "passed_current_gate": gate["passed"], "reasons": gate["reasons"]}


@app.get("/acoustic/calibration-status")
def calibration_status() -> Dict[str, Any]:
    """Calibration set summary: counts per kind + current-gate accuracy."""
    from collections import Counter
    d = Path("local_data/gate_calibration")
    counts: Counter = Counter()
    if d.exists():
        for j in d.glob("*.json"):
            try:
                meta = json.loads(j.read_text(encoding="utf-8"))
                counts[str(meta.get("kind", "unknown"))] += 1
            except Exception:
                pass
    return {"recordings": dict(counts), "total": sum(counts.values()),
            "directory": str(d)}


# ----------------------------------------------------------------- acoustic
@app.post("/acoustic/ambient")
async def ambient(audio: UploadFile = File(...)) -> Dict[str, Any]:
    with _tmp_upload(audio) as path:
        return record_ambient_baseline(str(path))


@app.post("/acoustic/classify")
async def acoustic_classify(audio: UploadFile = File(...),
                            capture_method: str = Form("unknown")) -> Dict[str, Any]:
    with _tmp_upload(audio) as path:
        return classify_acoustic(str(path), capture_method=capture_method)


# ------------------------------------------------- live data-collection mode
@app.post("/acoustic/collect")
async def acoustic_collect(audio: UploadFile = File(...),
                           onion_id: str = Form(...),
                           capture_method: str = Form("phone_tap"),
                           position: str = Form("equator"),
                           device: str = Form(""),
                           os_version: str = Form(""),
                           notes: str = Form("")) -> Dict[str, Any]:
    """Save one real recording (copy-only) with its per-WAV metadata sidecar.

    This is the data-collection path of the scan page: every saved WAV lands in
    dataset-acoustic/raw/<ONION_ID>/ in exactly the format
    training/train_acoustic.py reads (ONION id in the filename, label sidecar
    next to the file). internal_label stays null until the cut-open step.
    """
    from src.acoustic.collection import save_recording
    with _tmp_upload(audio) as path:
        try:
            return save_recording(
                wav_bytes=path.read_bytes(), onion_id=onion_id,
                capture_method=capture_method, position=position,
                device=device, os_version=os_version, notes=notes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.get("/acoustic/collection-status")
def acoustic_collection_status() -> Dict[str, Any]:
    """Honest trainability summary: verified onions vs the 30-onion minimum."""
    from src.acoustic.collection import collection_status
    return collection_status()


@app.post("/acoustic/ground-truth")
async def acoustic_ground_truth(onion_id: str = Form(...),
                                internal_label: str = Form(...),
                                labelled_by: str = Form(...),
                                method: str = Form("cut_open"),
                                notes: str = Form(""),
                                photograph: Optional[UploadFile] = File(None)) -> Dict[str, Any]:
    """Cut-open ground truth: the only endpoint that may set internal_label.

    Multipart form so the scan page can upload the cut-surface photograph as
    evidence alongside the label.
    """
    from src.acoustic.collection import record_ground_truth
    with _tmp_upload(photograph) as photo_path:
        try:
            return record_ground_truth(
                onion_id=onion_id,
                internal_label=internal_label,
                labelled_by=labelled_by,
                photograph=photo_path,
                method=method,
                notes=notes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.post("/fuse")
def fuse(payload: Dict[str, Any]) -> Dict[str, Any]:
    return fuse_results(payload.get("vision", {}), payload.get("acoustic"))


@app.post("/vision/classify")
def vision_classify(payload: Dict[str, Any]) -> Dict[str, Any]:
    path = payload.get("image_path")
    if not path:
        raise HTTPException(status_code=400, detail="image_path is required")
    return classify_vision(path)


# ---------------------------------------------------------- reports and sync
@app.post("/reports")
def put_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "report_id" not in payload:
        raise HTTPException(status_code=400, detail="report_id is required")
    return _store_report(payload)


@app.get("/reports/{report_id}")
def get_report(report_id: str) -> Dict[str, Any]:
    report = store().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


@app.get("/report/verify/{report_id}")
def verify_report(report_id: str) -> Dict[str, Any]:
    report = store().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    verdict = verify_integrity(report)
    return {"report_id": report_id, **verdict,
            "statement": ("Tamper-EVIDENT check: a changed report fails this "
                          "hash comparison. Not a forgery guarantee.")}


@app.post("/report/verify")
def verify_report_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return verify_integrity(payload)


@app.post("/sync/scans")
def sync_scans(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Idempotent ingest of field scan records (retry-safe)."""
    records = payload.get("records") or [payload]
    results = [store().put_scan(record) for record in records]
    return {"accepted": len(results), "duplicate": sum(1 for r in results
                                                       if r["duplicate"]),
            "results": results}


@app.post("/review/override")
def review_override(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record an inspector's override beside the machine decision.

    Validated against the canonical HumanOverride contract, so the API cannot
    accept a decision value the grading engine would never emit.
    """
    from src.common.contracts import ContractError, HumanOverride
    try:
        override = HumanOverride.from_dict(payload)
    except ContractError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not override.onion_id:
        raise HTTPException(status_code=400, detail="onion_id is required")
    stored = store().put_override({
        "override_id": override.override_id,
        "onion_id": override.onion_id,
        "batch_id": override.batch_id,
        "inspector_id": override.inspector_id,
        "center_id": payload.get("center_id"),
        "machine_decision": override.machine_decision,
        "human_decision": override.human_decision,
        "machine_confidence": override.machine_confidence,
        "reason_code": override.reason_code,
        "reason": payload.get("reason") or override.reason_code,
        "note": override.note,
        "model_version": payload.get("model_version"),
    })
    return {**stored,
            "machine_decision_preserved": True,
            "disagreement": override.is_disagreement,
            "note": ("The override is stored alongside the machine decision, "
                     "so an auditor sees both.")}


@app.get("/dashboard/summary")
def dashboard_summary(center_id: Optional[str] = None) -> Dict[str, Any]:
    return store().summary(center_id)


@app.get("/dashboard/overrides")
def dashboard_overrides(center_id: Optional[str] = None) -> Dict[str, Any]:
    """Human-in-the-loop analytics: override rate and AI/human disagreement."""
    return store().override_analytics(center_id)


@app.get("/dashboard/scans")
def dashboard_scans(center_id: Optional[str] = None) -> Dict[str, Any]:
    return {"scans": store().scans(center_id)}


# ------------------------------------------------------------------ helpers
class _tmp_upload:
    """Save an upload to a temp file and remove it afterwards."""

    def __init__(self, upload: Optional[UploadFile]) -> None:
        self.upload = upload
        self.path: Optional[Path] = None

    def __enter__(self) -> Optional[Path]:
        if self.upload is None:
            return None
        suffix = Path(self.upload.filename or "upload.bin").suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(self.upload.file.read())
        tmp.close()
        self.path = Path(tmp.name)
        return self.path

    def __exit__(self, *exc) -> None:
        if self.path and self.path.exists():
            self.path.unlink(missing_ok=True)


class _tmp_uploads:
    def __init__(self, uploads: List[UploadFile]) -> None:
        self.uploads = uploads
        self.paths: List[Path] = []
        self._handles: List[_tmp_upload] = []

    def __enter__(self) -> List[Path]:
        for upload in self.uploads:
            handle = _tmp_upload(upload)
            self.paths.append(handle.__enter__())
            self._handles.append(handle)
        return self.paths

    def __exit__(self, *exc) -> None:
        for handle in self._handles:
            handle.__exit__(*exc)


def _store_report(report: Dict[str, Any]) -> Dict[str, Any]:
    from src.reporting.audit_hash import verify_integrity as _verify
    verdict = _verify(report)
    stored = store().put_report(report)
    return {**stored, "hash_valid": verdict["valid"],
            "report_hash": (report.get("integrity") or {}).get("canonical_hash")}


@app.exception_handler(Exception)
async def unhandled(_request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500,
                        content={"error": type(exc).__name__, "detail": str(exc)})
