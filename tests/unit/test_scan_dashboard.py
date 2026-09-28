"""Exercise the real scan-page JavaScript without installing a browser library.

Node's standard-library VM supplies a small DOM/media boundary. The assertions
cover user-visible result semantics and ordering of file/HTTP callbacks; actual
image decoding and browser layout remain browser checks.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js required for scan-page JavaScript tests")

HARNESS = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const script = request.html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements = new Map(), previews = [], requests = [];
function get(id) {
  if (!elements.has(id)) {
    const element = {
      value: id === 'mode' ? 'batch' : '', disabled: false, hidden: false,
      _text: '', _html: '',
      get textContent() { return this._text; },
      set textContent(value) { this._text = value; this._html = ''; },
      get innerHTML() { return this._html; },
      set innerHTML(value) { this._html = value; this._text = ''; },
      getContext() { return {drawImage: image => { this.lastDraw = image.src; }}; },
    };
    elements.set(id, element);
  }
  return elements.get(id);
}
const context = vm.createContext({
  document: {getElementById: get},
  window: {location: {origin: 'http://localhost'}}, navigator: {},
  Image: class {
    constructor() { previews.push(this); this.naturalWidth = 800; this.naturalHeight = 600; }
  },
  URL: {createObjectURL: file => 'blob:' + file.name, revokeObjectURL() {}},
  FormData: class { append() {} },
  fetch: () => new Promise((resolve, reject) => requests.push({resolve, reject})),
  __test: {get, previews, requests}, payload: request.payload,
});
vm.runInContext(script, context);
Promise.resolve(vm.runInContext('(async () => {' + request.action + '})()', context))
  .then(result => process.stdout.write(JSON.stringify(result)))
  .catch(error => { console.error(error); process.exitCode = 1; });
"""


def run_page(action: str, payload=None):
    result = subprocess.run(
        [NODE, "-e", HARNESS],
        input=json.dumps({
            "html": (PROJECT_ROOT / "dashboard" / "scan.html").read_text(encoding="utf-8"),
            "action": action,
            "payload": payload,
        }),
        text=True, encoding="utf-8", capture_output=True, timeout=10,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def render(payload, single=True):
    return run_page(
        f"renderVision(payload, {str(single).lower()}); return __test.get('visionOut').innerHTML;",
        payload,
    )


@pytest.mark.parametrize("payload", [
    {"status": "success", "is_onion": False, "onion": None},
    {"status": "success", "is_onion": True, "onion": None},
    {"status": "no_onion_detected", "is_onion": None, "onion": None},
    {"status": "detection_inconclusive", "is_onion": None, "onion": None},
], ids=["legacy-no-boxes", "missing-onion", "no-onion-detected", "inconclusive"])
def test_missing_detection_is_inconclusive_and_never_a_grade(payload):
    rendered = render(payload)
    assert "DETECTION INCONCLUSIVE" in rendered
    assert "does not mean the image is not an onion" in rendered
    assert "No grade assigned" in rendered
    assert "MANUAL REVIEW" not in rendered
    assert "NOT AN ONION" not in rendered
    assert "GRADE A" not in rendered


@pytest.mark.parametrize("payload,single", [
    ({"status": "model_unavailable", "onion": None}, True),
    ({"detector": {"status": "model_unavailable"}, "onion": None}, True),
    ({"images": [{"status": "model_unavailable"}], "onions": []}, False),
], ids=["single-status", "single-detector-status", "legacy-batch-status"])
def test_model_unavailable_is_distinct_from_failed_detection(payload, single):
    rendered = render(payload, single)
    assert "MODEL UNAVAILABLE" in rendered
    assert "No grade assigned" in rendered
    assert "DETECTION INCONCLUSIVE" not in rendered


def test_empty_batch_hides_legacy_report_and_unannotated_image():
    rendered = render({
        "status": "success", "onions": [],
        "batch": {"counts": {"grade_a": 0}, "percentages": {"grade_a": 0}},
        "report": {"report_id": "EMPTY-REPORT"},
        "annotated_images": [{"url": "empty-annotation.png"}],
    }, single=False)
    assert "DETECTION INCONCLUSIVE" in rendered
    for misleading_output in ("EMPTY-REPORT", "empty-annotation.png", "Grade A", "grade split"):
        assert misleading_output not in rendered


def test_detected_single_displays_actual_decision_and_measurement():
    rendered = render({
        "status": "success", "is_onion": True,
        "onion": {"decision": {"decision": "grade_a"},
                  "vision": {"label": "sound", "confidence": 0.9},
                  "size": {"diameter_mm": 55, "size_method": "aruco_calibrated"}},
    })
    assert "GRADE A" in rendered
    assert "55 mm (aruco_calibrated)" in rendered
    assert "sound" in rendered


@pytest.mark.parametrize("decision,expected", [(None, "NO GRADE"), ("manual_review", "MANUAL REVIEW")])
def test_manual_review_requires_an_explicit_decision(decision, expected):
    rendered = render({"status": "success", "is_onion": True,
                       "onion": {"decision": {"decision": decision}}})
    assert expected in rendered
    if decision is None:
        assert "MANUAL REVIEW" not in rendered


def test_detected_batch_keeps_report_and_annotated_evidence():
    rendered = render({
        "onions": [{"onion_id": "ONION_1", "decision": {"decision": "grade_a"}}],
        "batch": {"counts": {"grade_a": 1}},
        "report": {"report_id": "VALID-REPORT"},
        "annotated_images": [{"url": "real-evidence.png"}],
    }, single=False)
    assert "1 × Grade A" in rendered
    assert "VALID-REPORT" in rendered
    assert "real-evidence.png" in rendered


def test_new_file_clears_results_and_ignores_older_preview_load():
    result = run_page("""
        const {get, previews} = __test;
        get('visionOut').innerHTML = 'OLD GRADE'; get('raw').textContent = 'OLD JSON';
        get('file').onchange({target: {files: [{name: 'first.png'}]}});
        get('file').onchange({target: {files: [{name: 'second.png'}]}});
        previews[0].onload();
        const disabledUntilCurrentPreview = get('scan').disabled;
        previews[1].onload();
        return {disabledUntilCurrentPreview, scanDisabled: get('scan').disabled,
                preview: get('snap').lastDraw, canvasHidden: get('snap').hidden,
                cameraHidden: get('cam').hidden, output: get('visionOut').textContent,
                raw: get('raw').textContent, cameraState: get('camState').textContent};
    """)
    assert result == {
        "disabledUntilCurrentPreview": True, "scanDisabled": False,
        "preview": "blob:second.png", "canvasHidden": False, "cameraHidden": True,
        "output": "No scan for this image yet.", "raw": "—",
        "cameraState": "File selected: second.png",
    }


@pytest.mark.parametrize("failed", [False, True], ids=["stale-success", "stale-error"])
def test_pending_scan_cannot_overwrite_a_new_file_selection(failed):
    result = run_page("""
        const {get, previews, requests} = __test;
        get('file').onchange({target: {files: [{name: 'first.png'}]}});
        previews[0].onload();
        const pendingScan = get('scan').onclick();
        const disabledWhileScanning = get('scan').disabled;
        get('file').onchange({target: {files: [{name: 'second.png'}]}});
        previews[1].onload();
        if (payload.failed) requests[0].reject(new Error('older scan failed'));
        else requests[0].resolve({ok: true, json: async () => ({
            onions: [{onion_id: 'OLD_ONION'}], batch: {counts: {grade_a: 99}}
        })});
        await pendingScan;
        return {disabledWhileScanning, scanDisabled: get('scan').disabled,
                output: get('visionOut').textContent, html: get('visionOut').innerHTML,
                raw: get('raw').textContent, error: get('scanErr').textContent};
    """, {"failed": failed})
    assert result == {
        "disabledWhileScanning": True, "scanDisabled": False,
        "output": "No scan for this image yet.", "html": "", "raw": "—", "error": "",
    }
