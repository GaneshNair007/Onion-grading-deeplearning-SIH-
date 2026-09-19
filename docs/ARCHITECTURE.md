# ONION-Q — Architecture

> **One sentence:** ONION-Q turns subjective onion procurement grading into a
> measurable, auditable digital workflow by separating *measurement* (models)
> from *policy* (a versioned standards document).

## 1. The core separation

```
IMAGE / AUDIO
      │
      ▼
  MEASUREMENT LAYER            ← neural networks and DSP live here
  (vision attributes, size, acoustic evidence)
      │   measurements + confidence + reason codes
      ▼
  POLICY ENGINE                ← versioned JSON, hashed, no model weights
  (must satisfy grade rules?  → grade_a | relaxed | reject | manual_review)
      │
      ▼
  REPORT + AUDIT               ← tamper-evident hash, QR, offline journal
```

The network never outputs a grade. It outputs probabilities and physical
measurements. `src/grading/engine.py` turns those into a decision under
`config/grading/*.json`. Changing a government threshold therefore means
editing a JSON file, **not retraining a model** — and historical measurements
can be re-evaluated under a new policy because every decision stores
`policy_id`, `policy_version` and `policy_hash`.

## 2. Components

| Layer | Module | Responsibility |
|---|---|---|
| Data | `src/data/dataset_registry.py` | Reads `dataset/MANIFEST.csv`; resolves images across parts; supplies real COCO labels |
| Data | `src/data/labels.py` | The **only** place a source category becomes a model label |
| Data | `src/data/splits.py` | Near-duplicate-aware grouping so augmented siblings never straddle train/test |
| Data | `src/data/provenance.py` | License gate + `dataset/training_manifest.csv` governance |
| Vision | `src/vision/detector.py` | Onion instance detection (Faster R-CNN MobileNetV3-Large 320) |
| Vision | `src/vision/model.py` | `OnionAttributeNet` — 4-class commercial grade + rotten/sprout heads |
| Vision | `src/vision/multi_view.py` | Guided 4-view capture; conservative per-view fusion |
| Vision | `src/vision/rejection.py` | Detector gate first, embedding-OOD fallback second |
| Vision | `src/vision/size.py` | ArUco-calibrated size, or an explicit *uncalibrated* verdict |
| Vision | `src/vision/capture_quality.py` | Blur / glare / crowding / framing / calibration gates |
| Acoustic | `src/acoustic/{loading,quality,features,splits}.py` | WAV I/O, quality gates, FFT/STFT/log-mel features, onion-level splits |
| Fusion | `src/fusion/fusion.py` | Confidence-aware fusion; invalid audio never changes a grade |
| Grading | `src/grading/{policy,engine,batch}.py` | Policy loading/hashing, decision rules, batch percentages |
| Reporting | `src/reporting/{generator,audit_hash,qr}.py` | Report, hash chain, QR verification payload |
| Mobile | `src/mobile/{capture_protocol,offline_store}.py` | Guided phone measurement; offline-first scan journal and sync |
| Entry points | `inference/{batch_scan,deep_scan,combined_scan,vision_inference,acoustic_inference}.py` | App-facing API |

## 3. Two inspection modes

### MODE A — Quick Batch Scan (`inference/batch_scan.py`)

Tray image(s) → detect instances → per-onion crop → attributes → calibrated
size → capture-quality gate → policy → batch aggregation → report.

No acoustic work in this mode: throughput matters. Suspicious or low-confidence
onions are flagged for Deep Scan.

### MODE B — Deep Scan (`inference/deep_scan.py`)

Four guided views (`neck`, `base`, `side_a`, `side_b`) → per-view attributes →
conservative fusion → optional phone acoustic measurement (quality-gated) →
confidence-aware fusion → policy → decision.

**Multi-view fusion rules** (chosen to avoid manufacturing confidence):

* defect *existence* = `any` view above threshold (one clear view of rot is
  evidence; clean views do not disprove it);
* defect *severity* = `max` across views, never the mean;
* surface-area percentages are **not** summed across views — the views overlap,
  so aggregation would inflate the measurement, and it is reported as
  unavailable;
* coverage is reported (`complete` / `incomplete`).

## 4. Confidence and escalation

Every gate that cannot be satisfied produces `manual_review` **with a reason
code**, never a default grade:

| Situation | Result |
|---|---|
| Model confidence < policy threshold | `manual_review` + `LOW_MODEL_CONFIDENCE` |
| Onions crowded/overlapping | `manual_review` + `OCCLUSION_HIGH` / `CROWDED_TRAY` |
| No calibration marker | `manual_review` + `CALIBRATION_MISSING` |
| Policy needs a measurement the pipeline cannot produce | `manual_review` + `MEASUREMENT_UNAVAILABLE` |
| Vision and acoustic disagree | `manual_review` + `MULTIMODAL_DISAGREEMENT` |
| Acoustic quality poor | `vision_only_audio_unreliable` (vision result kept) |
| Acoustic model has no onion ground truth | decision unchanged + `ACOUSTIC_NOT_VALIDATED` |
| Detector/attribute artifact absent | `model_unavailable`, nothing graded |

Reason codes are defined in `src/common/reasons.py` with plain-language text for
farmer-facing views.

## 4b. Canonical contracts and version identity

**One contract per concept** (`src/common/contracts.py`): `VisionResult`,
`AcousticResult`, `SizeResult`, `OnionMeasurement`, `GradingDecision`,
`BatchResult`, `HumanOverride`, `InspectionReport`. The API validates input
against them (for example `/review/override` cannot accept a decision value the
grading engine would never emit), and
`tests/contracts/test_contract_conformance.py` runs the **real** pipeline and
asserts its output still satisfies the contracts — the shapes are verified, not
assumed. Notable invariants encoded there:

* `diameter_mm` may only be non-null when `size_method == "aruco_calibrated"`;
* a `GradingDecision` must carry at least one reason code;
* `acoustic_grading_eligible()` is the single gate that decides whether acoustic
evidence may influence a grade (status valid **and** verified onion ground truth
**and** not research-only);
* `BatchResult.check_percentages()` reconciles reported percentages against the
counts they came from.

The practical effect: the API, the report generator, the dashboard and the tests
all speak the same vocabulary, so the demo cannot drift away from the product
without a test failing.

**Version identity** (`src/common/version.py`): `APP_VERSION`, the git commit,
the model registry contents and the active policy version/hash are read from
reality (git, `models/registry.json`, `config/grading`) and stamped into every
report header under `header.identity`. Nothing asserts a version the repository
cannot substantiate.

## 5. Trust boundaries and honesty wording

* Reports are **tamper-evident**, not tamper-proof (`src/reporting/audit_hash.py`).
* Size is reported in millimetres **only** when ArUco calibration is present;
  otherwise an explicitly labelled pixel estimate.
* No shelf-life / freshness score is produced — no longitudinal labels exist,
  so `freshness_score` is `null` everywhere and fusion refuses to synthesise one.
* Acoustic output is *supporting evidence* today: without cut-open onion ground
  truth it cannot alter a grade.
* The offline journal is append-only and never deletes evidence; sync failures
  leave records `failed` and retryable.

## 6. Repository layout (current)

```
config/grading/          policies + policy sources + schema
dataset/                 partitioned image dataset (MANIFEST.csv, part-001..018)
dataset-acoustic/        acoustic sources, protocol, synthetic demo, parts
models/                  registry.json + trained artifacts + model cards
src/                     library code (data, vision, acoustic, fusion, grading, reporting, mobile)
inference/               app-facing scan entry points
training/                trainers (detector, attributes, acoustic)
scripts/                 demos, fixtures, registry/provenance builders, smoke test
tests/                   unit | vision | acoustic | grading | integration | e2e
docs/                    this file and the rest of the documentation set
server/                  FastAPI service exposing the same functions as the app
dashboard/               static, API-driven operations dashboard
mobile/android/          Kotlin reference implementation (not compiled here)
```

### Note on the legacy `backend/` directory

A `backend/` tree exists **in the local working copy only** (untracked). It
contains a pre-audit prototype whose models were trained on synthetic images
and oscillator audio. Nothing in the tracked project imports from it; the
self-contained replacement is `src/` + `inference/` + `server/`. It is left
untouched on disk rather than deleted, and it is excluded from the repository.
