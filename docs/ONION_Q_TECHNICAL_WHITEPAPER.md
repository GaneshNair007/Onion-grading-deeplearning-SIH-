# ONION-Q — Technical Whitepaper

**AI-assisted onion inspection and procurement grading, with a versioned
standards engine and auditable evidence.**

Smart India Hackathon 2026 · SIH26031 · branch `sih-winning-system`

Every number in this document is reproduced from an artifact in this
repository. Where a measurement does not exist, the document says so — that is
the point of the architecture, not a gap in the write-up.

---

## 1. Problem

Onion procurement grading is a visual, judgement-heavy task performed at
procurement centres at high throughput. Two structural problems follow:

1. **Subjectivity and drift.** "Grade A", "relaxed" (URS) and "reject" calls
   depend on the inspector's eye, and the rules themselves change — the relaxed
   specification has been introduced and withdrawn repeatedly.
2. **Invisible defects.** Internal rot is not visible from the outside. A tray
   that looks compliant can contain bulbs that fail days later.

Conventional AI framing ("photograph an onion, get a grade") fails both
problems: it bakes a moving standard into frozen weights, and it produces a
confident number where the evidence does not support one.

## 2. Product positioning

ONION-Q is **procurement decision infrastructure**, not an onion classifier.
Four layers, deliberately separated:

| Layer | Responsibility | Artefact |
|---|---|---|
| **Perception** | See the produce: detect instances, measure visible condition, optionally capture acoustic evidence | models + capture protocols |
| **Measurement** | Turn perception into typed quantities and explicit "cannot measure" | `Measurements`, size/attribute contracts |
| **Governance** | Convert measurements into procurement decisions using a versioned, hashed policy | `config/grading/*.json`, `src/grading/` |
| **Auditability** | Keep evidence, human review and integrity hashes so a decision can be re-examined | `src/reporting/`, `server/`, offline journal |

The AI never decides the grade it cannot justify; the policy engine decides,
and the policy is a document that can change without retraining anything.

## 3. Procurement workflow

```
batch/tray capture
   → capture-quality gates                      (refuse bad photos, don't guess)
   → calibration markers (ArUco)                (millimetres, or explicitly none)
   → onion instance detection                   (one box per onion)
   → per-onion crop → visible attributes        (rot / sprout probabilities)
   → measurements (typed, None = not measured)
   → policy engine                              (versioned, hashed)
   → per-onion decision + machine-readable reasons
   → batch aggregation (percentages with an explicit denominator)
   → report + evidence hashes + QR payload
   → offline journal → idempotent sync → dashboard
   → inspector override (stored beside the machine decision)
```

## 4. Dataset

| Source | Images | Labels | Licence | Trained on |
|---|---|---|---|---|
| Onion Grading v7 (COCO segmentation) | 2 963 | `Class 1/2`, `Extra Class`, `Reject`, `Onions` | CC BY 4.0 | yes |
| onions v1 (COCO) | 783 | `rotten`, `sprout` | Public Domain | yes |
| Onion Leaves and Bulb | present | none (no annotation file) | **not detected** | **no — excluded** |
| **Total annotated** | **3 746** | | | |

Total dataset payload: ~244 MB across `dataset/part-001 … part-00N` (no single
file above the 100 MiB GitHub limit; no file was split).

Governance (`evaluation/dataset_governance.json`, `docs/DATASET_GOVERNANCE.md`)
enumerates every source group in `dataset/MANIFEST.csv` and states licence
status, annotation format and exclusion reason. The unlicensed source appears
explicitly under `excluded_sources` / `unresolved_sources`; a regression test
fails if a manifest source group can be silently ignored again.

Duplicate files are detected by SHA-256 and copied once. The dataset
fingerprint (`2443539b…507b`) is recorded in every training run and every model
card, so a model can always be traced to the exact data that produced it.

## 5. Vision methodology

**Attributes, not grades.** The training labels are attributes and commercial
classes; the pipeline predicts measurable attributes (rot, sprout) and lets the
policy engine interpret them. The 4-class commercial head is retained for
comparison only, and an automated test enforces that no grading or inference
module references it.

**Leakage discovery (a real finding).** Roboflow's official `valid` split is
**85.2 % near-duplicate with `train`** (median nearest-neighbour cosine
similarity 0.9986), while `test` is 1.0 %. A model scoring 0.938 on `valid`
scored **0.168** on `test`. Every metric produced before that discovery was
untrustworthy. `evaluation/split_leakage.json` records the measurement;
`src/data/splits.py` removes the failure mode by grouping near-duplicates with
ImageNet-pretrained embeddings (label-agnostic, so grouping cannot be circular)
and assigning whole groups to splits.

**Leak-safe splitting.** 3 746 images → **2 272 near-duplicate groups** →
2 622 / 562 / 562 (train / validation / test), verified **0 groups spanning two
splits**. The detector uses the same grouped split
(`evaluation/detection_split.json`), which also fixes a subtler problem: the
official validation split contained no defect-source images at all, so it could
not have measured detection on the data that matters.

## 6. Vision results

Leak-free grouped split, CPU training. Full per-class tables, PR curves,
confidence sweeps and error galleries: `models/vision/attributes/metrics.json`,
`docs/MODEL_CARDS.md`.

| Task | Metric | Value | Honest verdict |
|---|---|---|---|
| Visible rot (binary) | F1 / AUC | **0.928 / 0.975** | usable signal on held-out data |
| Sprout (binary) | F1 / AUC | **0.784 / 0.866** | usable but weaker |
| Commercial 4-class head | macro-F1 | **0.312** (chance ≈ 0.25) | **not reliable — never used for procurement** |
| Detector (single class, onion) | AP@0.50 / F1 | see `docs/DETECTOR_EXPERIMENTS.md` | experimental; leak-safe split |

The four-class number is the most important line in this table. It is why the
architecture is *measurements → policy* rather than *image → grade*: the
attribute models are usable, the grade classifier is not, and only the policy
layer turns attributes into a defensible decision.

## 7. Size measurement

RGB imagery cannot yield millimetres without a scale reference. ONION-Q uses a
printable ArUco calibration mat (`scripts/make_calibration_mat.py`):

* markers detected → homography → pixel-to-mm scale → equivalent diameter,
  reported as `size_method = "aruco_calibrated"`;
* markers absent → `diameter_mm = null`, `size_method = "uncalibrated"`.

A contract test makes it impossible to report a millimetre value without
calibration. Physical mat accuracy is **not** validated here — the protocol for
the team's caliper measurements is
`docs/PHYSICAL_SIZE_VALIDATION_PROTOCOL.md` (status: `PHYSICAL VALIDATION
PENDING`). Software validation (marker detection, scale consistency on rendered
mats, rotation/perspective/missing-marker cases) is tested.

## 8. Policy engine

The neural network produces measurements; a policy document produces decisions.
Every policy carries `policy_id`, `version`, `effective_from`, `effective_to`,
`source`, `source_type`, `source_url`, `verification_date` and
`source_verified`, and is hashed (`sha256:`) into every decision and report.

Three guarantees, each tested:

* `source_verified = true` **requires** a URL, a verification date and an
  official source type. A news article can never be promoted to a standard by
  editing a boolean — the loader refuses the file.
* An unverified policy is labelled
  `"Demonstration grading configuration"` in its summary and reported as
  `POLICY_UNVERIFIED` on every decision it produces.
* The shipped `demo_policy.json` is explicitly not an official standard, and
  `config/grading/strict_with_segmentation.json` demonstrates the intended
  behaviour of a stricter future standard: it requires a measurement the
  pipeline cannot yet produce, so every onion escalates to `manual_review` with
  `MEASUREMENT_UNAVAILABLE`. Same model, no retraining, different outcome.

## 9. Grading rules and escalation

| Gate | Condition | Outcome |
|---|---|---|
| Confidence | `model_confidence < min_model_confidence` | `manual_review` (`LOW_MODEL_CONFIDENCE`) |
| Capture | occlusion above limit or capture rejected | `manual_review` (`OCCLUSION_HIGH`) |
| Calibration | size needed but no calibrated diameter | `manual_review` (`CALIBRATION_MISSING`) |
| Multimodal | visual and acoustic evidence disagree | `manual_review` (`MULTIMODAL_DISAGREEMENT`) |
| Defects | visible rot / sprouting when disallowed | `reject` |
| Measurement | policy needs a value the pipeline cannot produce | `manual_review` (`MEASUREMENT_UNAVAILABLE`) |
| Acoustic | evidence not validated against cut-open truth | never changes a grade (`ACOUSTIC_NOT_VALIDATED`) |

Batch percentages use `total_detected` as the denominator; manual-review onions
are reported as their own class rather than excluded. `BatchResult.check_percentages()`
verifies that reported percentages reconcile with the counts.

## 10. Deep Scan (multi-angle)

Guided views: neck, base, side A, side B. Fusion is conservative and documented:

* existence of a defect is decided by *any* valid view above threshold — one
  clear view of rot is evidence; three clean views do not disprove it;
* severity uses the maximum across views, never a mean that averages a real
  defect away;
* duplicate images supplied for several views are detected by hash and reported
  as `DUPLICATE_VIEW_WARNING` — four copies of one photo is not
  "complete multi-angle coverage".

## 11. Acoustic research track

The phone-only path is the product direction: ambient baseline, three
standardised taps (or an experimental chirp with baseline-response
normalisation), quality gates (silence, clipping, SNR, duration, sample rate,
impact presence), FFT/STFT, log-mel spectrograms and 14 acoustic features.

**No public redistributable onion acoustic dataset was found.** The only
onion-specific vibrometry study located is a paywalled paper whose data is not
published; it is recorded as a research reference and used to design the
collection protocol, not as evidence that a phone microphone detects internal
defects. Consequently:

* the shipped acoustic classifier is trained on **synthetic** audio and is
  labelled as such in its model card and in every warning;
* `grading_eligible` is `False` for any model without
  `dataset_type = verified_onion_acoustic`, enforced centrally by
  `acoustic_grading_eligible()` and asserted by tests at both the fusion and
  engine level;
* `training/train_acoustic.py --require-verified-onion-data` **refuses to
  train** without cut-open labels, so a synthetic model can never be quoted
  with an onion metric;
* the collection tooling (`scripts/collect_acoustic_sample.py`,
  `scripts/add_cut_open_ground_truth.py`) captures the metadata and the
  destructive ground truth needed to make the claim legitimate later.

The honest statement: **the acoustic pipeline is a validated DSP chain attached
to an unvalidated classifier.** That asymmetry is deliberate and visible in the
UI text and the report.

## 12. Human-in-the-loop

Inspectors may override any decision (accept, reject, mark for review, re-scan).
The override is stored *beside* the machine decision, never in place of it, with
inspector id, timestamp, machine decision, its confidence, reason code, free-text
note and model version. `/dashboard/overrides` reports the override rate,
AI-vs-human disagreement rate, reasons and per-model breakdown. A disagreement
is not automatically an AI error — it is the human judgement of record, and the
dashboard says so.

## 13. Report integrity

Reports carry `report_version`, git commit, app version, model versions, policy
id/version/hash, per-onion results with reason codes, evidence entries with
SHA-256 hashes of the inputs, and a canonical-JSON SHA-256 integrity block with
a QR payload.

Four tamper scenarios are tested: unmodified (valid), a percentage shifted by
0.01 (fails), a changed inspector id (fails), a changed evidence hash (fails).
Swapping an input image on disk is detected by re-hashing. The wording is
deliberately "tamper-**evident**": this detects modification, it does not make a
report unforgeable, and it is not called tamper-proof or fraud detection.

## 14. Offline-first architecture

Field scanning writes to an append-only JSONL journal (fsync per record, atomic
rewrite when marking, corrupt-line tolerant). Each record carries a
client-generated UUID; the server upserts on that id, so a retried upload
produces exactly one row (tested). Nothing is ever deleted, and a failed upload
stays pending for the next sync pass.

## 15. Backend and dashboard

FastAPI over SQLite, no ORM, no external services: `/health`, `/version`,
`/models`, `/policies`, `/views`, `/scan/image`, `/scan/batch`, `/scan/deep`,
`/acoustic/*`, `/fuse`, `/reports`, `/reports/{id}`, `/report/verify/{id}`,
`/report/verify`, `/sync/scans`, `/review/override`, `/dashboard/summary`,
`/dashboard/scans`, `/dashboard/overrides`. The API is deliberately thin: it
calls the same functions the CLI demos and the tests call, so the demo cannot
drift from the product. Demo records are labelled `DEMO`; no national or
official statistics are fabricated.

## 16. Reproducibility

* `scripts/clean_clone_smoke_test.py` verifies a checkout needs no untracked
  local directory (the pre-audit code imported from `backend/`, which was never
  committed — audit finding P0.1).
* `dataset/README.md`, `dataset/LICENSES_AND_SOURCES.md` and `MANIFEST.csv`
  document the data; `docs/DATASET_GOVERNANCE.md` adds per-source governance.
* Every training run records `dataset_fingerprint`, split strategy, seed,
  configuration, history and metrics next to its artifact.
* `.github/workflows/test.yml` runs imports + tests without large artifacts.

## 17. Results summary

| Capability | Status | Evidence |
|---|---|---|
| Batch scan end-to-end | working | `scripts/demo_batch_scan.py` |
| Rot / sprout attributes | real signal, leak-safe | F1 0.928 / 0.784 |
| Grade-class classifier | not reliable | macro-F1 0.312; excluded by test |
| Policy engine + provenance | working, tested | refuses unverifiable `source_verified` |
| Calibrated size | software-tested, physical pending | protocol document |
| Reports + tamper evidence | working, tested | 4 tamper scenarios |
| Offline sync idempotency | working, tested | `test_sync_is_idempotent` |
| Android app | blocked (no toolchain) | `docs/ANDROID_BUILD_STATUS.md` |
| ONNX export | blocked (`onnx` absent) | `evaluation/export_validation.json` |
| Acoustic internal defect | **not validated** | no cut-open ground truth exists |

## 18. Limitations

1. The visible-defect models are trained on two public datasets with one
   annotation protocol each; they are not field-validated on procurement
   produce and their labels are not a government standard.
2. The detector is the weakest link: single class, CPU-trained, and measured on
   a leak-safe split that is harder than the source splits.
3. No instance segmentation yet, so defect *surface area* is reported as
   unavailable rather than estimated.
4. Physical size accuracy is unverified until the caliper protocol is completed.
5. Acoustic internal-defect detection has **no** verified onion ground truth.
   The pipeline is ready; the claim is not.
6. The four-class commercial classifier is not reliable enough for procurement.
7. The Android application has not been compiled here; only its contract is
   verified.
8. The backend has no authentication, no rate limiting and no multi-tenant
   isolation; it is a field-pilot component, not a public service.

## 19. Future work

1. **Collect the first real dataset**: paired images, three-tap recordings and
   cut-open ground truth per onion — the single highest-value action available.
2. **Instance segmentation** from the polygon masks already present in the
   source annotations, enabling measured defect surface area.
3. **Detector scaling** on more annotated trays with recall-oriented thresholds,
   then ONNX Runtime Mobile benchmarking on real phones.
4. **Physical size validation** and per-device recalibration.
5. **Policy provenance**: replace the demo thresholds once an official
   specification document is obtained, and register the policy hash.
6. **Field pilot instrumentation**: override analytics is already the feedback
   channel; feed it into the active-learning queue.

## 20. What this project will not claim

* that visible-defect models are field-validated;
* that the four-class classifier can grade procurement produce;
* that phone audio detects internal rot;
* that a report is tamper-proof;
* that size is physically accurate before calibration is verified;
* that synthetic or auxiliary audio is onion ground truth;
* that the Android app works before it has been built.
