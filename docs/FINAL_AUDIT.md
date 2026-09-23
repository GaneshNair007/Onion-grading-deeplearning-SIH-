# Final Audit — 2026-09-24

## Repository safety

- Integration branch: `sih-final-integration`, created from `c8888896`.
- Existing modified `demo/tray_composed.png` and its provenance JSON were preserved.
- Existing untracked `onion-grading-master-plan-SIH26031.md` was preserved.
- The local `sih-winning-system` already contains the strongest backend; the remote `frontend` branch is older and does not contain the current dashboard. No blind merge was performed.

## Implemented system

- FastAPI service, SQLite audit store, static same-origin browser UI.
- Faster R-CNN MobileNetV3 detector plus MobileNetV3 attribute heads.
- ArUco physical calibration; no marker means no millimetre claim.
- Versioned policy engine with explicit unverified demo policy.
- Batch counts and percentages, per-onion reason codes, manual overrides.
- Browser camera, microphone capture, ambient gate, chirp/tap DSP and research-only acoustic result.
- Tamper-evident JSON/Markdown reports and QR payload.
- Persisted original and annotated evidence images, hashed into each report.

## Dataset audit

Generated `artifacts/dataset_audit/detection_dataset_audit.json`.

- 3,746 annotated images; 5,293 annotations.
- 5,291 usable boxes; 2 degenerate tiny boxes.
- 2,989 polygon annotations across 2,963 images.
- 29 duplicate records reported by the registry audit.
- Sources and licences: Public Domain detection/defect source and CC BY 4.0 grading segmentation source.
- The broad labels `Extra Class`, `Class 1`, `Class 2`, and `Reject` are not reinterpreted as precise government grades.

## Verified runtime gate

- `220 passed` after the annotation/evidence change (one third-party Starlette deprecation warning).
- Live uvicorn health, model registry, scan page, batch upload, report, and annotation retrieval all returned HTTP 200.
- Real demo tray: 7 detections; calibrated sizes; 5 reject and 2 manual review under the explicitly unverified demo policy.

## Material limitations

- Leak-safe detector test AP@0.50 is 0.1339 and F1@0.5 score is 0.2075; this is prototype quality.
- The broad commercial-quality head does not generalise (test macro-F1 0.1202) and is not used as a procurement-grade oracle.
- Rot/sprout validation uses a carveout, not independent field validation.
- Detector supplies boxes, not instance masks; size uses calibrated box long-side and remains sensitive to perspective.
- Acoustic model is trained only on synthetic signals and cannot affect procurement grade.
- No official Grade A/URS primary-source thresholds were verified; the demo policy remains `source_verified=false`.
