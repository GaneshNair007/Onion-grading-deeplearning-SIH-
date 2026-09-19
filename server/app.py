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

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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
from src.reporting.evidence import capture_evidence                 # noqa: E402
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
                     lot_id: Optional[str] = Form(None),
                     policy: str = Form("demo_policy"),
                     require_calibration: bool = Form(True)) -> Dict[str, Any]:
    if not images:
        raise HTTPException(status_code=400, detail="no images supplied")
    with _tmp_uploads(images) as paths:
        result = scan_tray_batch(paths, policy, center_id=center_id,
                                 inspector_id=inspector_id, lot_id=lot_id,
                                 require_calibration=require_calibration)
    report = finalize(build_report(
        result["batch"],
        [{"onion_id": o["onion_id"], "source_image": o["source_image"],
          "decision": o["decision"]["decision"],
          "reason_codes": o["decision"]["reason_codes"],
          "measurements": o["measurements"]} for o in result["onions"]],
        evidence=capture_evidence(result["images"]),
        demo_mode=not result["policy"].get("source_verified", False),
        app_version=APP_VERSION))
    write_report(report, PROJECT_ROOT / "reports")
    _store_report(report)
    result["report"] = {"report_id": report["report_id"],
                        "report_hash": report["integrity"]["canonical_hash"],
                        "qr_payload": report["qr_payload"]}
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


# ----------------------------------------------------------------- acoustic
@app.post("/acoustic/ambient")
async def ambient(audio: UploadFile = File(...)) -> Dict[str, Any]:
    with _tmp_upload(audio) as path:
        return record_ambient_baseline(str(path))


@app.post("/acoustic/classify")
async def acoustic_classify(audio: UploadFile = File(...)) -> Dict[str, Any]:
    with _tmp_upload(audio) as path:
        return classify_acoustic(str(path))


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
