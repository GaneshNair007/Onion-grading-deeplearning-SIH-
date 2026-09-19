# Feature status — source of truth for the pitch

Every claim made about ONION-Q must appear in this table with a status. If a
feature is not listed here, do not claim it. Statuses: **Yes** (implemented),
**Tested** (covered by an automated test in this repository), **Validated**
(measured on honest held-out data or by physical measurement), **Demo-ready**
(can be shown live today), plus the limitation that qualifies the claim.

Last updated: 2026-09-19.

| Feature | Implemented | Tested | Validated | Demo-ready | Limitations |
|---|---|---|---|---|---|
| Tray/batch scan (multi-onion) | Yes | Yes | Partly | Yes | Detector quality is the current bottleneck; accuracy depends on capture quality. |
| Onion instance detection | Yes | Yes | Partly | Yes | Single-class detector trained on CPU with limited data; see `docs/DETECTOR_EXPERIMENTS.md`. |
| Non-onion / OOD rejection | Yes | Yes | **No** | Yes | Gate is wired and testable, but calibrated only on synthetic negatives — no real negative-photo set has been collected. |
| Visible rot detection | Yes | Yes | Partly (leak-free F1 ≈ 0.93) | Yes | One dataset, one annotation protocol; no field validation; not a procurement standard. |
| Sprout detection | Yes | Yes | Partly (leak-free F1 ≈ 0.78) | Yes | Weaker than rot; same single-source caveat. |
| Commercial 4-class grading head | Yes | Yes | **No** (macro-F1 ≈ 0.31) | Research only | Never used for procurement; a test enforces this. |
| Surface-damage percentage | No | Yes (unavailable path) | No | Yes (as refusal) | Needs segmentation masks; the policy requiring it escalates to `manual_review`. |
| Size — ArUco calibrated | Yes | Yes (rendered mats) | **No** (physical) | Yes | Printed-mat accuracy is a human measurement; `PHYSICAL VALIDATION PENDING`. |
| Size — uncalibrated | Yes | Yes | No | Yes | Returns `diameter_mm = null`; a contract test forbids fabricated millimetres. |
| Capture-quality gates | Yes | Yes | Partly | Yes | Thresholds chosen conservatively; not tuned on a field dataset. |
| Multi-angle Deep Scan | Yes | Yes | Partly | Yes | Fusion rules conservative and documented; duplicate-view warning implemented. |
| Phone acoustic capture protocol | Yes | Yes | No | Yes | Chirp + tap paths designed; recording contract defined for Android. |
| Acoustic DSP (FFT/STFT/log-mel/features) | Yes | Yes | Partly | Yes | Verified on synthetic + generated signals, not on real onion recordings. |
| Acoustic internal-defect classifier | Pipeline only | Yes (DSP) | **No** | Yes (as research) | No onion ground truth exists; model is synthetic and `grading_eligible = False`. |
| Acoustic cannot change a grade | Yes | **Yes** | Yes | Yes | Enforced centrally in `acoustic_grading_eligible()` + engine flag. |
| Multimodal fusion | Yes | Yes | Partly | Yes | Disagreement → `manual_review`; research-only acoustics ignored. |
| Policy/standards engine | Yes | Yes | Yes (unit) | Yes | Demo thresholds; `source_verified = false` and shown as such. |
| Policy versioning + hashing | Yes | Yes | Yes | Yes | Every decision stores policy id, version and hash. |
| Policy provenance enforcement | Yes | Yes | Yes | Yes | A `source_verified` policy without URL/date/official source type is refused. |
| Batch aggregation | Yes | Yes | Yes | Yes | Percentages use `total_detected`; manual review never hidden. |
| Tamper-evident reports | Yes | Yes | Yes | Yes | Tamper **evident**, not tamper-proof; 4 tamper scenarios tested. |
| Evidence hashing | Yes | Yes | Yes | Yes | Input image identity is re-checkable; a swapped file is detected. |
| QR verification payload | Yes | Yes | Partly | Yes | Text payload works; PNG rendering needs `qrcode` (not installed here). |
| Human override + analytics | Yes | Yes | Yes (unit) | Yes | Override stored beside the machine decision; disagreement rate reported. |
| Active-learning review queue | Yes | Yes | Yes | Yes | Exports a work list only — never auto-labels or auto-retrains. |
| Offline-first store | Yes | Yes | Partly | Yes | Journal + retry semantics tested; no real device has run it. |
| Backend API | Yes | Yes | Partly | Yes | SQLite, no auth, single-process; not hardened for public deployment. |
| Dashboard | Yes | No | No | Yes | Static page over live endpoints; demo data must be labelled DEMO. |
| Android app | Source only | No | No | **No** | Toolchain absent — see `docs/ANDROID_BUILD_STATUS.md`. |
| ONNX export + runtime parity | Script only | No | No | No | `onnx` not installed here; export unverified. |
| Shelf-life prediction | No | No | No | No | Requires longitudinal labels that do not exist. |
| Internal rot from phone audio | No | No | No | No | Requires paired cut-open ground truth. |
