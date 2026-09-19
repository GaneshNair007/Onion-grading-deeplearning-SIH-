# Deployment status

One row per component, with the evidence that supports the status. Statuses are
deliberately narrow: **WORKING** means it runs from this repository today and is
covered by a test; **PARTIAL** means it runs but not under field conditions;
**BLOCKED** means it cannot be completed here and the reason is stated;
**NOT VALIDATED** means it exists but no measurement supports a performance
claim.

Last updated: 2026-09-19 (commit at the time of writing).

| Component | Status | Evidence / limitation |
|---|---|---|
| Python CLI (batch scan) | **WORKING** | `scripts/demo_batch_scan.py` runs end to end; `tests/integration/test_batch_scan.py`. |
| Python CLI (deep scan) | **WORKING** | `scripts/demo_deep_scan.py`; `tests/e2e/test_field_workflow.py`. |
| Policy engine | **WORKING** | `src/grading/policy.py` + `tests/grading/test_policy_and_engine.py`; refuses a `source_verified` policy without provenance. |
| Batch aggregation | **WORKING** | `src/grading/batch.py`; percentages reconcile with counts (`BatchResult.check_percentages`). |
| Report generation | **WORKING** | `src/reporting/generator.py`; report carries model + policy + git identity. |
| Report integrity (hash) | **WORKING** | 4 tamper scenarios in `tests/unit/test_report_integrity.py`. |
| Evidence hashing | **WORKING** | `src/reporting/evidence.py`; a swapped input file is detected. |
| QR payload | **PARTIAL** | Payload encoded + decoded in tests; PNG rendering needs `qrcode`, which is **not installed** here (`QrUnavailable` is raised, never a broken file). |
| Backend API | **WORKING** | `server/app.py`; `server/tests/test_api.py` (health, policies, models, sync, reports, verify, override, dashboard). |
| Idempotent sync | **WORKING** | Repeated `record_id` stores one row (`test_sync_is_idempotent`). |
| Human override | **WORKING** | Stored beside the machine decision; analytics in `/dashboard/overrides`. |
| Dashboard | **PARTIAL** | Static HTML reading live API endpoints; no chart library, no auth, not load-tested. |
| Android source | **BLOCKED** | No JDK/Gradle/Android SDK on the build machine — see `docs/ANDROID_BUILD_STATUS.md`. |
| Android build / APK | **BLOCKED** | Not compiled; no APK exists. |
| ONNX export | **BLOCKED** | The `onnx` package is not installed in this environment; `scripts/export_onnx.py` is written and reports the missing dependency rather than faking an artifact. |
| Attribute model (rot/sprout) | **PARTIAL** | Real signal (rot F1 ≈ 0.93, sprout F1 ≈ 0.78 on a leak-free split) but one dataset, one annotation protocol, no field validation. |
| 4-class quality head | **NOT VALIDATED** | macro-F1 ≈ 0.31 — research comparison only; a test asserts grading code never uses it. |
| Detector | **PARTIAL** | Real trained model on a leak-safe split; see `docs/DETECTOR_EXPERIMENTS.md` for the honest numbers vs baseline. |
| Instance segmentation | **NOT IMPLEMENTED** | Masks exist in the source labels; no segmentation model trained. Defect surface area stays `null` by design. |
| Size calibration (software) | **WORKING** | ArUco mat generator + measurement on rendered mats; `tests/vision/test_size_and_multiview.py`. |
| Size calibration (physical) | **NOT VALIDATED** | Printed-mat accuracy is a human measurement; protocol in `docs/PHYSICAL_SIZE_VALIDATION_PROTOCOL.md`, status `PHYSICAL VALIDATION PENDING`. |
| Acoustic DSP | **WORKING** | Loading, quality gates, FFT/STFT, log-mel, 14 features; `tests/acoustic/test_acoustic_pipeline.py`. |
| Acoustic classifier | **NOT VALIDATED** | Trained on synthetic/demo audio only. `grading_eligible` is `False` and a test proves it cannot change a grade. |
| Real onion acoustic dataset | **MISSING** | No public verified onion acoustic dataset found; collection protocol ready, no recordings yet. |
| Multimodal fusion | **WORKING** | Confidence-aware; disagreement → `manual_review`; research-only acoustics → vision-only. |
| Offline-first store | **WORKING** | Append-only journal + retry semantics; `tests/unit/test_reporting_and_store.py`. |
| CI | **WORKING (local equivalent)** | `.github/workflows/test.yml` runs tests + import checks with no large artifacts. |
| Reproducibility | **WORKING** | `scripts/clean_clone_smoke_test.py` verifies a checkout needs no untracked files. |
