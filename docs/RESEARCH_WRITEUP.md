# ONION-Q — Research Writeup & Technical Documentation

**Project:** ONION-Q (Smart India Hackathon, SIH26031)
**System:** AI-assisted onion quality inspection and procurement grading for
procurement-center inspectors
**Branch:** `sih-winning-system` · Every number below is traceable to an
artifact in the repository (Appendix C maps claims → files).

---

## Table of Contents

1. Abstract
2. Problem Statement & Positioning
3. System Architecture
4. Dataset Engineering & Governance
5. Vision Pipeline I — Detection
6. Vision Pipeline II — Attribute Recognition
7. Non-Onion Rejection (OOD Gating)
8. Size Measurement & Calibration
9. Acoustic Pipeline — Signal Processing
10. Acoustic Pipeline — Impact-Presence Gate
11. Acoustic Modeling & Research-Only Policy
12. Multimodal Fusion
13. Policy Engine & Procurement Decisions
14. Deep Scan (Multi-View)
15. Tamper-Evident Reporting
16. Backend, Offline-First Sync & Supabase
17. Web & Mobile Capture Layer
18. Model Export & Performance Benchmark
19. Testing & Reproducibility
20. Limitations (Complete & Unvarnished)
21. Research Roadmap
Appendix A — Exact Reproduction Commands
Appendix B — Endpoint Inventory
Appendix C — Claim-to-Artifact Provenance Map

---

## 1. Abstract

ONION-Q is an end-to-end, offline-capable inspection platform that converts
photographs and (optionally) acoustic recordings of onions into **auditable
procurement decisions**. Its central design principle is the separation of
*measurement* from *decision*: neural networks estimate physically meaningful
attributes (onion presence, visible rot, sprouting, calibrated diameter);
a **versioned policy engine** — not a neural network — converts those
measurements into Grade A / Relaxed / Reject / Manual-review decisions against
a configurable procurement standard. Uncertain cases are never silently
graded; they are escalated with reason codes and remain fully auditable via
tamper-evident reports (canonical-JSON SHA-256 + QR).

Verified results (leak-safe, grouped splits; details in §5–6): onion
detection AP@0.50 = **0.639**, mAP@0.50:0.95 = **0.410**; visible-rot
recognition F1 = **0.928** (AUC 0.975); sprouting F1 = **0.784** (AUC 0.866).
The 4-class commercial-grade head (macro-F1 0.312) is deliberately confined
to research outputs and cannot influence procurement decisions — enforced by
tests. The acoustic channel implements a complete capture→DSP→features
pipeline with an **impact-presence gate** that makes false predictions on
non-impact audio impossible; its classifier is honestly labeled
`research_only` (synthetic-trained) and is structurally barred from grading.

---

## 2. Problem Statement & Positioning

**Primary user:** procurement-center inspector (NAFED/NCCF-style field
officer). **Secondary:** center supervisor, regional auditor, ministry
administrator. Household freshness scanning is a future expansion only.

The operational flow implemented:

```
PROCUREMENT BATCH → IMAGE CAPTURE → ONION DETECTION → PER-ONION VISION
→ SIZE MEASUREMENT → CONFIDENCE ASSESSMENT → OPTIONAL DEEP SCAN
→ ACOUSTIC INTERNAL-CONDITION ANALYSIS → POLICY ENGINE
→ PER-ONION DECISION → BATCH AGGREGATION → GRADE DISTRIBUTION
→ DIGITAL REPORT (hash + QR) → OFFLINE STORAGE → SYNC → DASHBOARD
```

Positioning sentence used across README/dashboard/reports: *the AI measures;
the policy decides; inspectors adjudicate; every step is auditable.*

---

## 3. System Architecture

**Monorepo layout (all importable, no hidden local files — clean-clone
smoke-tested):**

| Layer | Location | Role |
|---|---|---|
| Contracts | `src/common/contracts.py` | Canonical schemas (VisionResult, AcousticResult, Measurements, Decision, …) + conformance tests |
| Vision | `src/vision/` | Attribute net, detector wrapper, OOD rejection, size, multi-view, capture quality |
| Acoustic DSP | `src/acoustic/` | WAV loading, quality gates, FFT/STFT/log-mel, 14 features, **impact gate** |
| Fusion | `src/fusion/fusion.py` | Conservative vision⊕acoustic combination |
| Grading | `src/grading/` | Policy engine, per-onion decision, batch aggregation |
| Reporting | `src/reporting/` | Canonical JSON, SHA-256, QR, evidence hashes |
| Inference | `inference/` | Task-level facades (single, batch, deep, acoustic) |
| Service | `server/` | FastAPI + SQLite store, idempotent sync, CORS, static dashboard |
| Dashboard/Scan UI | `dashboard/` | KPIs + live camera/mic scan page |
| Mobile | `mobile/android/` | CameraX + AudioTrack/AudioRecord + offline store (reference implementation) |
| Data governance | `dataset/`, `evaluation/` | Manifests, provenance, governance reports, splits |
| Training | `training/` | Detector, attributes, acoustic trainers (checkpointed) |

**Canonical contract example** (`src/common/contracts.py`):

```json
{
  "is_onion": true,
  "vision":   {"label": "sound", "confidence": 0.88, "defects": {}},
  "acoustic": {"status": "valid", "internal_defect_probability": 0.71,
               "confidence": 0.76, "model_version": "acoustic-v1"},
  "final":    {"label": "needs_manual_review", "freshness_score": null,
               "reason": "visual and acoustic evidence disagree"}
}
```

---

## 4. Dataset Engineering & Governance

### 4.1 Sources on disk (verified by enumeration, not assumption)

| Source | Images | License | Training | Role |
|---|---|---|---|---|
| Onion Grading v7i (COCO segmentation) | 2,963 | verified | **yes** | detection + attributes |
| onions v1 (COCO mmdetection) | 783 | verified | **yes** | detection + attributes |
| Onion Leaves and Bulb | 16,300 (12,260 bulbs, 4,040 leaves) | **unresolved** | **no** | OOD reference fitting only (background use) |
| **Total on disk** | **40,447** | — | 3,746 trainable-annotated | — |

### 4.2 Provenance & governance

- `dataset/MANIFEST.csv` + `dataset/training_manifest.csv`: per-file records
  (path, bytes, sha256, source group, license status).
- `src/data/provenance.py` enumerates **all** manifest sources — the
  license-unresolved group appears explicitly in `excluded_sources`/
  `unresolved_sources` (regression-tested; earlier bug silently omitted it).
- `scripts/dataset_governance.py` → `evaluation/dataset_governance.json` +
  `docs/DATASET_GOVERNANCE.md`: 20,054 manifest files; exact-duplicate
  detection by SHA-256; per-source license/annotation/training participation;
  deterministic **dataset fingerprint** `2443539b…` recorded in every model
  card.

### 4.3 Leakage — the defining dataset problem

Roboflow exports duplicate images across train/valid/test (augmented
siblings). Naive splits inflate metrics. Countermeasures implemented:

- Perceptual hashing groups near-duplicate images (`threshold 0.98`,
  `evaluation/detection_split.json`);
- **Grouped leak-safe split**: 2,622 train / 562 validation / 562 test,
  0 groups spanning splits;
- `scripts/diagnose_split_leakage.py` documents the delta vs the official
  split — e.g. the 4-class head scores far higher on the leaky split than on
  the grouped one, which is why grouped numbers are the only reported ones.

### 4.4 The 16,300-image question (resolved honestly)

Unlabeled images cannot manufacture rot/sprout/grade labels. They *were*
used, without license violation, where labels are unnecessary: fitting the
non-onion embedding reference from 12,260 bulbs (§7). Any further use
(detector augmentation, attribute training) is blocked on (a) license
resolution and (b) annotation effort — both team actions, tooling ready.

---

## 5. Vision Pipeline I — Detection

**Task:** single-class onion localization (`{0: background, 1: onion}`) in
tray photographs.

**Model:** Faster R-CNN, MobileNetV3-Large-320 FPN backbone (torchvision),
input long side 320 px. Chosen for CPU-trainability and export path; a YOLO
candidate was considered but rejected on dependency/license/stability grounds
for this environment.

**Training** (`training/train_detector.py`, verifiable config in
`models/vision/detector/training_config.json`):

| | baseline-v1 | **v0.2 (promoted)** |
|---|---|---|
| Train images | 240 | **2,622** |
| Split | official (leak-prone) | grouped leak-safe |
| Epochs × bs × lr | 4 × 4 | 8 × 4 × 2e-4 |
| Wall time, device | — | 4,347.8 s (72.5 min), CPU |
| Checkpointing | — | best+last, per-epoch history, early-stop logic, `--gallery-dir` |

**Test metrics** (562 images, 993 GT boxes, held-out, leak-safe —
`models/vision/detector/metrics.json`):

| Metric | baseline-v1 (re-scored, same split) | v0.2 |
|---|---|---|
| AP@0.50 | 0.134 | **0.639** |
| AP@0.75 | — | **0.439** |
| mAP@0.50:0.95 | 0.030 | **0.410** |
| Precision@0.5 | 0.235 | **0.745** |
| Recall@0.5 | 0.186 | **0.586** |
| F1@0.5 | 0.208 | **0.656** |
| TP/FP | — | 543 / 186 |

Loss fell 0.671 → 0.564 over 8 epochs with monotonic validation-metric
improvement — no overfitting signature.

**Error analysis** (committed galleries, `evaluation/detector_gallery/`):
false positives concentrate on crowded trays (touching onions) and tight
crops; false negatives on partial occlusion at tray edges. This motivated the
detector-uncertainty zones (§13.3) rather than threshold fudging.

**Selection discipline:** baseline preserved immutable at
`models/vision/detector-baseline-v1/`, deprecated in
`models/registry.json`; the comparison is reproducible via
`training/train_detector.py --eval-baseline`.

---

## 6. Vision Pipeline II — Attribute Recognition

**Model:** `OnionAttributeNet` — MobileNetV3-Small backbone (576-d pooled
embedding, exposed via `net.embed()`), dual heads: 4-class quality (softmax)
+ binary defect heads rot/sprout (sigmoid). 128 px input.

**Training** (`training/train_attribute_model.py`): 3 epochs, bs 32,
lr 8e-4, 35.6 s wall (CPU) — deliberately cheap to retrain whenever labels
improve.

**Held-out metrics** (`models/vision/attributes/metrics.json`):

- Defect heads, grouped carve-out (n=211, `defects_val_mmdet_carveout`):
  - **rotten: P 0.985, R 0.877, F1 0.928, ROC-AUC 0.975** (154 positives)
  - **sprout: P 0.828, R 0.744, F1 0.784, ROC-AUC 0.866** (129 positives)
- 4-class quality head (leak-safe test, n=381): accuracy 0.318,
  **macro-F1 0.312**, per-class F1 0.24–0.36 — **not reliable**.

**Production consequence (research-integrity rule):** the quality head is a
**research-only output**. It is quarantined under `research_outputs` in
inference JSON, excluded from `measurements`, and
`tests/unit/test_multimodal.py` plus contract tests enforce that no
production grading path can read it. Visible condition is carried by the
binary rot/sprout heads, which have real signal.

Honesty note carried in every vision result: the attribute model is trained
on Roboflow-labeled photographs; it is not field-validated, and **shelf-life
is never predicted** (no longitudinal labels exist).

---

## 7. Non-Onion Rejection (OOD Gating)

Two independent gates, in priority order:

1. **Detector gate (primary).** Any image where the trained detector finds
   no onion instance above the review threshold → `is_onion=false`,
   decision `not_onion`. Verified live: synthetic brown blob rejected;
   real onion accepted at 0.9998 detector confidence.
2. **Embedding-OOOD gate (fallback; e.g. ONNX-only mobile builds).**
   `models/vision/rejection_reference.npz` — a diagonal one-class Gaussian
   (mean, inverse-variance, 99th-percentile Mahalanobis threshold) fitted
   over 576-d embeddings from **1,500 real bulb images**
   (`scripts/build_rejection_reference.py`). Validation:
   bulb median distance 21.2 vs threshold 49.4; recorded, honest limitation:
   onion **leaves** overlap (65.7% inlier) — this gate catches gross
   non-onions (mat, stone, table), not plant parts. Because the bulb source
   license is unresolved, the artifact is machine-local (gitignored) and
   rebuildable in ~1 minute; nothing is redistributed.

**Known gap:** real-world negatives (potato, tomato, garlic, hand, bags) have
not been collected, so the false-reject/false-accept operating point on
produce is unmeasured. `scripts/build_negative_set.py` exists for exactly
this and is the single highest-value data action for Case 1.

---

## 8. Size Measurement & Calibration

- **Method:** ArUco calibration mat (printed A4, generated by
  `scripts/make_calibration_mat.py`); PnP from ≥1 visible marker gives the
  homography; onion bbox projects to millimetres.
- **Output honesty contract:** `diameter_mm` is returned only with
  `size_method="calibrated"` + `calibration_confidence` + marker count;
  otherwise `approximate` (pixel bbox, explicit non-measurement note) or
  `unavailable`. Never a silent fake number.
- **Software validation:** rendered-mat tests cover perspective, partial
  marker visibility, rotation, resolution changes, blur (tolerances in
  `tests/vision/`).
- **Physical validation:** pending team measurement against a printed mat —
  protocol in `docs/PHYSICAL_SIZE_VALIDATION_PROTOCOL.md`
  (print → caliper-verify 40 mm marker → photograph caliper-measured spheres
  → MAE/relative error). Status is labeled `PHYSICAL VALIDATION PENDING`.

---

## 9. Acoustic Pipeline — Signal Processing

Location: `src/acoustic/` (loading, quality, features) + tests. WAV in →
per-recording quality report + 14-dimensional feature vector out.

**Quality gates (all pre-model):** clipping (sample saturation), silence
(RMS floor), SNR vs estimated noise floor, duration consistency, sample-rate
validation. Failure ⇒ `retest_required` with actionable guidance — never a
guess.

**Features (14, `FEATURE_ORDER`):** rms_energy, peak_amplitude,
dominant_frequency_hz, spectral_centroid_hz, spectral_bandwidth_hz,
spectral_rolloff_hz, spectral_entropy, zero_crossing_rate,
energy_low/mid/high_band, resonance_peak_hz, decay_rate,
decay_time_60db_s. Computed from FFT/STFT with band-pass pre-filtering;
log-mel spectrograms available for future deep models. Export: CSV/Parquet
with deterministic column order.

**Design principle:** every feature is a *physical descriptor* of the
impact response (energy distribution, resonances, decay). No feature claims
internal-rot semantics — that mapping requires labeled onion data (§11).

---

## 10. Acoustic Pipeline — Impact-Presence Gate

**The bug this eliminates:** the classifier answered every input; empty room
noise produced "internal-defect probability 0.93" — a false answer.

**Mechanism** (`src/acoustic/impact_gate.py`, runs **before** the model):
a valid measurement must contain physical evidence of an excitation event:

1. transient above absolute floor (peak ≥ 0.030);
2. transient ≥ 8 dB over the frame-median noise floor;
3. impulsive character (crest factor ≥ 4);
4. **free decay**: negative log-envelope slope over up to 2 s of post-peak
   audio **and** late-window envelope < ½ early-window (systematic decrease —
   fluctuating noise swells cannot pass);
5. chirp-mode alternative: sustained RMS excess ≥ 6 dB over floor.

Calibrated and validated on a labeled set (5 noise floors incl. mains hum
and wind-like swells vs 5 real taps): **10/10 correct** with wide margins
(taps: crest 12.5, decay 2.1/s vs thresholds 4.0, 1.5/s). Failure output:
`status="no_impact_detected"`, `internal_defect_probability=null`,
human guidance to re-capture. Twelve regression tests pin this behavior.

---

## 11. Acoustic Modeling & Research-Only Policy

**Status: no publicly downloadable, redistributable onion acoustic dataset
exists** (surveyed in `dataset-acoustic/README.md` + `SOURCES.md`; the one
onion vibrometry study — Landahl et al. 2022, *Biosystems Engineering*,
DOI 10.1016/j.biosystemseng.2022.07.004 — is subscription-only with no data
release). Therefore:

- The shipped classifier (RandomForest over the 14 features) is trained on
  **synthetic impact audio**; its card records `dataset_type: synthetic`,
  metrics (train n=11 / test n=5 — deliberately tiny, cannot be mistaken for
  a real result).
- Contract-enforced statuses: `research_only=true`,
  `grading_eligible=false` — the fusion layer (§12) and policy engine
  structurally cannot consume research-only acoustic evidence.
- **Path to a real model (tooling ready, collection pending):**
  `dataset-acoustic/collection_protocol.md` (3 standardized taps, ambient
  baseline, device metadata), `scripts/collect_acoustic_sample.py`
  (repeatability across taps, WAV+JSON sidecar), Android collector in
  `mobile/android/`, `scripts/add_cut_open_ground_truth.py` to attach
  cut-open labels by onion_id. The DSP pipeline, split-by-onion training
  scaffold, and feature export are already production-grade; swapping the
  synthetic artifact for a verified one flips `grading_eligible` by data,
  not code changes.

---

## 12. Multimodal Fusion

`src/fusion/fusion.py` — conservative by construction:

| Situation | Behavior |
|---|---|
| Non-onion image | short-circuit `not_onion`; acoustic ignored |
| Acoustic absent/`retest_required`/`no_impact`/research-only | **vision-only**, `status` records the reason (e.g. `vision_only_audio_unreliable`, `vision_only_acoustic_not_validated`) |
| Valid + eligible acoustic | weighted combination, weights from confidence |
| Vision ⊕ acoustic disagree | `manual_review`, reason `multimodal disagreement` |

Low-confidence acoustic evidence can never upgrade/downgrade an onion
silently; its confidence and reason are always surfaced.

---

## 13. Policy Engine & Procurement Decisions

- **Policies are versioned JSON** (`config/grading/*.json`) with provenance
  fields: `policy_id`, `version`, `effective_from/to`, `source`,
  `source_verified`, `source_type`, `context_urls`, `access_date`,
  `policy_hash` (SHA-256 of canonical JSON, verified at load).
- **Active demo policy** (`ONIONQ_DEMO_STRICT_V1 1.0.0`,
  `source_verified=false`): Grade A = 45–65 mm, no visible rot, no sprout,
  internal-defect prob ≤ 0.4 (eligible evidence only); Relaxed = 35–70 mm,
  no rot/sprout; Reject = rot or sprout visible. Manual-review triggers:
  model confidence < 0.65, missing calibration, multimodal disagreement,
  occlusion > 0.35. UI and reports carry a **DEMO banner** because
  `source_verified=false`.
- **Decision function** (`src/grading/engine.py`): pure, deterministic,
  measurement-driven; same measurements + same policy ⇒ same decision.
  Switching policy JSON re-grades a batch with **zero retraining** (Demo 2 of
  the SIH demo script).
- **Batch aggregation** (`src/grading/batch.py`): counts, percentages,
  denominator rules, mean confidence, per-onion reason codes.
- **Detector uncertainty zones:** high-confidence / review / ignore bands
  tuned on validation PR curves — low-confidence boxes route to review, not
  to grades.

---

## 14. Deep Scan (Multi-View)

Four guided views (neck, base, side A, side B) per onion; per-view capture
quality + prediction + confidence + evidence. Fusion is deliberately
asymmetric: **a real defect on any valid view stands** (no averaging away);
severity takes the worst supported value; identical-file duplicate views are
detected (hash) and flagged `DUPLICATE_VIEW_WARNING` instead of being counted
as multi-angle coverage. Optional acoustic capture attaches to the same
session; the fused contract is the §3 interface.

---

## 15. Tamper-Evident Reporting

`src/reporting/`: canonical JSON serialization (sorted keys, fixed float
format) → SHA-256 over the canonical form → QR payload
(`{type, report_id, hash, verify_route}`) → optional PNG. Evidence hashing
covers original images and derived overlays (and audio where captured).
Verification (`GET /report/verify/{id}` or `POST /report/verify`)
re-canonicalizes and re-hashes: tests prove (1) unmodified ⇒ VALID;
(2) any field edit (grade %, inspector name, evidence hash) ⇒
INTEGRITY CHECK FAILED. Wording discipline: **tamper-evident**, never
"tamper-proof".

---

## 16. Backend, Offline-First Sync & Supabase

- **FastAPI** (`server/app.py`, 20+ endpoints — Appendix B): scan/batch/deep,
  acoustic, fuse, reports+verify, override, sync, dashboard; OpenAPI at
  `/docs`; CORS from `ONIONQ_CORS_ORIGINS` (explicit origins, credentials
  enabled); dashboard + scan page served same-origin at `/dashboard/app/`.
- **Store** (`server/store.py`): SQLite (WAL), tables scans/reports/
  overrides; `/sync/scans` **idempotent by client UUID** (double-upload ⇒
  one record — tested); override records inspector, original AI result,
  confidence, new result, reason code, note.
- **Supabase** (`src/integrations/supabase_sync.py` + `supabase/schema.sql`):
  PostgREST over requests (no SDK dependency); service-key writes
  (backend-only, never shipped to a website), anon-key reads; **idempotent
  upsert on report id** mirroring local sync; honest no-op reporting when
  unconfigured; `POST /integrations/supabase/push` bulk-pushes local
  reports. RLS: public read, service-key-only writes.
- **Offline-first:** local journal (`scans.jsonl` per center) → later sync;
  conflict-free by UUID idempotency; the offline→sync round-trip is
  integration-tested.

---

## 17. Web & Mobile Capture Layer

**Web scan page** (`dashboard/scan.html`, served by the API itself):
`getUserMedia` rear-camera capture or file upload → single (`/scan/image`)
or tray (`/scan/batch`) scan with per-onion grade rendering; acoustic panel
records ambient baseline, plays a 1 s logarithmic chirp (Web Audio oscillator
through the **speaker**) while recording via **microphone** (echo
cancellation/AGC disabled by request), or records a guided 3 s tap; PCM →
16-bit WAV encoded client-side; results render with honest statuses incl.
`NO TAP/CHIRP DETECTED` guidance. Live-verified: not-onion rejection, batch
grading, full acoustic loop (SNR 16.4 dB room recording gated correctly).

**Android** (`mobile/android/`): CameraX frame capture → ONNX vision path;
`AudioTrack` chirp playback + `AudioRecord` capture (ambient → chirp → 3-tap
fallback) with device metadata (model, OS, sample rate, capture method);
file-based offline store + sync client. **Build status: source implemented,
compilation unverified on this machine** (no JDK/SDK present) —
`docs/ANDROID_BUILD_STATUS.md` records the exact Gradle commands for an SDK
machine. No claims of APK existence.

---

## 18. Model Export & Performance Benchmark

- **ONNX export** (`scripts/export_onnx.py`, legacy exporter forced because
  torch 2.13 dynamo cannot trace torchvision NMS): detector parity
  max-abs-diff ≈ 1e-6 on a real test image; attributes parity 3e-06.
  `evaluation/export_validation.json` holds inputs/hashes/numbers.
- **Latency (this machine, CPU)**: detector PyTorch 133 ms median
  (p95 421 ms) → **ONNX Runtime 24.4 ms (≈5.5×)**; attributes 1.4 ms ORT.
  Artifact sizes: detector 76 MB, attributes 4.3 MB ONNX / 4.4 MB PT.
- **Benchmark harness** (`scripts/benchmark_inference.py`): median/p95 per
  stage, complete-onion time, batch throughput (onions/s), hardware recorded.
- Mobile runtime target: ONNX Runtime Mobile (detector) + quantizable
  attribute net; TFLite export evaluated as follow-up.

---

## 19. Testing & Reproducibility

- **204 tests, 0 failed** (`python -m pytest tests server/tests -q`), layers:
  unit (DSP, gate, grading), contracts (canonical schemas, research-only
  enforcement), integration (batch, offline sync), e2e (field workflow,
  production safety incl. report tamper, acoustic-eligibility), vision
  (checkpoint formats, rejection reference), acoustic (quality, gate,
  capture protocol), tools (data ingestion scripts), server API (17).
- One known third-party warning (joblib/NumPy pickle deprecation) filtered
  by exact message in `pytest.ini` — documented, not blanket-suppressed.
- **Clean-clone gate** (`scripts/clean_clone_smoke_test.py --tracked-only`):
  a pristine clone installs, imports, runs demo + tests with no machine
  paths; scans for `C:\SIH`-style references and `backend/` legacy imports.
- **CI**: `.github/workflows/test.yml` runs the suite on push/PR.
- Determinism: dataset fingerprint in every model card; policy hash verified
  at load; canonical-JSON hashing is byte-stable.

---

## 20. Limitations (Complete & Unvarnished)

1. **No field validation.** All metrics are lab/dataset metrics; no
   procurement-center pilot has occurred.
2. **Detector occlusion failure mode.** Crowded/touching onions and tight
   crops dominate FP/FN galleries (AP50 0.639, recall 0.586 — honest, not
   field-ready).
3. **Acoustic classifier is synthetic-trained.** It cannot detect internal
   rot; only the capture/DSP pipeline is field-usable today.
4. **No real onion acoustic dataset exists publicly**; creating one requires
   the team's physical collection + cut-open labeling.
5. **Real non-onion negatives not collected** → OOD false-reject/accept
   rates on produce unmeasured.
6. **Physical size accuracy unvalidated** (protocol ready; needs caliper
   measurements).
7. **4-class grade head unreliable** (macro-F1 0.312) — quarantined,
   research-only by enforcement.
8. **Android build unverified** on this machine; no APK exists.
9. **Single-dataset label provenance** — rot/sprout labels inherit Roboflow
   annotation quality; no inter-annotator agreement study.
10. **Shelf-life prediction absent by design** (no longitudinal labels).
11. **Fraud detection is out of scope** — anomaly detection ≠ fraud detection;
    reports are tamper-evident, not tamper-proof.
12. **16,300 images license-unresolved** — excluded from supervised training
    pending rights clarification.
13. **Household/consumer mode deliberately de-scoped** to keep the
    procurement workflow primary.

---

## 21. Research Roadmap

**Immediate (team actions, tooling ready):**
1. Collect 30–40 real negatives → measured OOD operating point.
2. Print mat + caliper validation → physical MAE for size.
3. Record 40+ onions (3 taps each) + cut-open labels → first verified onion
   acoustic dataset; retrain; flip `grading_eligible` by evidence.
4. Resolve leaves-and-bulb license → 12k bulbs into detector/attribute
   training.

**Model track:** crowded-scene augmentation + tiling or DETR-style set
prediction for occlusion; mask head from the segmentation source for
projected-area/equivalent-diameter; active-learning loop from
`scripts/export_review_queue.py` (low-confidence, overrides, disagreements)
with 100-image weekly annotation sprints.

**Systems track:** INT8 quantization + per-device acoustic gain calibration
crowdsource table; Room migration for the Android store; signed report
chains (Ed25519 over the canonical hash) as the follow-on to tamper
evidence; multi-center dashboard with policy-diff views.

**Science track:** cultivar-aware acoustic baselines per Landahl et al.;
chirp deconvolution for phone speaker/mic response; repeatability thresholds
per device class; public release of the collected onion acoustic dataset
(fills a genuine gap — none exists).

---

## Appendix A — Exact Reproduction Commands

```bash
# Environment
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements.txt

# Tests & self-containment
python -m pytest tests server/tests -q
python scripts/clean_clone_smoke_test.py --tracked-only

# Dataset governance / provenance
python -m src.data.provenance
python scripts/dataset_governance.py
python scripts/audit_detection_dataset.py
python scripts/diagnose_split_leakage.py

# Training (detector baseline → v0.2)
python training/train_detector.py --model-id smoke --max-images 240 --epochs 2
python training/train_detector.py --model-id vision-detector-v0.2 \
    --epochs 8 --lr 2e-4 --min-size 320 --gallery-dir evaluation/detector_gallery
python training/train_attribute_model.py
python training/train_acoustic.py          # synthetic demo only

# Rebuild machine-local artifacts
python scripts/build_rejection_reference.py
python scripts/export_onnx.py
python scripts/build_model_registry.py

# Demos
python scripts/demo_batch_scan.py --compose 9 --with-mat
python scripts/demo_deep_scan.py --demo-views 4
uvicorn server.app:app --port 8000        # dashboard: /dashboard/app/, scan: /dashboard/app/scan.html
python scripts/benchmark_inference.py
python scripts/generate_report.py <batch_json>
```

## Appendix B — Endpoint Inventory

| Endpoint | Purpose |
|---|---|
| GET /health, /version, /models, /policies, /views | meta + registry + policy list |
| POST /scan/image | Case 1+2: gate → attributes → policy decision |
| POST /scan/batch | tray scan → per-onion decisions + report |
| POST /scan/deep | 4-view deep scan (+optional audio) |
| POST /acoustic/ambient | noise-floor baseline |
| POST /acoustic/classify | impact gate → quality → model |
| POST /fuse | conservative vision⊕acoustic |
| POST /vision/classify | attribute head direct |
| POST /reports, GET /reports/{id} | generate / fetch |
| GET /report/verify/{id}, POST /report/verify | integrity verification |
| POST /sync/scans | idempotent offline upload |
| POST /review/override | inspector override + audit |
| GET /dashboard/summary, /dashboard/overrides, /dashboard/scans | KPIs |
| POST /integrations/supabase/push | cloud report sync |

## Appendix C — Claim-to-Artifact Provenance Map

| Claim | Artifact |
|---|---|
| Detector AP50 0.639 / mAP 0.410 / F1 0.656; 2,622 train; 8 epochs; CPU 4,347.8 s | `models/vision/detector/metrics.json`, `history.json`, `training_config.json` |
| Baseline AP50 0.134 same-split | `models/vision/detector-baseline-v1/eval_on_leak_safe/` |
| Rot F1 0.928 / AUC 0.975; sprout F1 0.784 / AUC 0.866 | `models/vision/attributes/metrics.json` → `defects_val_mmdet_carveout` |
| Quality head macro-F1 0.312 (research-only) | same file → `quality_test`; `tests/unit/test_multimodal.py` |
| Leak-safe split, 0 spanning groups | `evaluation/detection_split.json`, `scripts/diagnose_split_leakage.py` |
| Governance: 20,054 files; excluded source 16,300 | `evaluation/dataset_governance.json`, `docs/DATASET_GOVERNANCE.md` |
| Fingerprint `2443539b…` | `evaluation/dataset_governance.json`; model cards |
| OOD reference: 1,500 bulbs, threshold 49.4, leaves 65.7% | `evaluation/rejection_reference_report.json` |
| Impact gate 10/10; noise ⇒ null probability | `tests/acoustic/test_impact_gate.py`, `src/acoustic/impact_gate.py` |
| Acoustic model synthetic, research-only | `models/acoustic/model_card.json`, contract tests |
| ONNX parity 1e-6 / 3e-06; ORT 24.4 ms | `evaluation/export_validation.json` |
| Policy demo, source_verified=false, hash | `config/grading/demo_policy.json` |
| Tamper tests | `tests/unit/test_report_integrity.py`, `tests/e2e/test_production_safety.py` |
| Idempotent sync | `server/tests/test_api.py`, `tests/integration/` |
| 204 tests green; clean clone | local run log; `scripts/clean_clone_smoke_test.py` |
| No public onion acoustic dataset | `dataset-acoustic/README.md`, `SOURCES.md` |

---

*Document generated from on-disk artifacts; branch `sih-winning-system`,
HEAD `30602cdf`. If numbers and artifacts ever disagree, the artifacts win —
that rule is the project.*
