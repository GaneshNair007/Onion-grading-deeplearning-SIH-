# Final Judge Rehearsal — Onion-Q (SIH26031)

Run this in one command from the repository root:

    python scripts/run_ci_gate.py

That single command replays exactly what GitHub Actions runs on every push —
the same four steps, in the same order, on a clean checkout — so you can
rehearse the judges' "does it actually run?" question before you ever leave
the machine.

Below is what each part means, what the numbers are today, and what to say
when they ask the hard questions.

---

## 1 · What the system actually is

Onion-Q is a procurement-grade onion inspection pipeline built around three
honest principles:

- **No black-box output.** Every decision comes from a trained model, a
  configurable policy, or an explicit "I can't answer yet" status.
- **No fabricated labels.** The models are trained only on the labels that
  actually exist in the tracked datasets; the rest are deliberately absent
  and documented as such.
- **No hidden local data.** A clean clone of the repository runs the full
  test suite. The reproducibility smoke test enforces that.

The system has two tiers, matching the problem statement:

- **Tier 1 (required):** camera-only onion detection, visible-defect
  classification, calibrated size, configurable Grade A / URS rule engine,
  batch percentages, and an evidence-backed digital report with QR code,
  policy version, and audit trail.
- **Tier 2 (differentiator):** phone-only acoustic hidden-defect screening
  using the built-in speaker and microphone — with a clearly labelled
  synthetic-demo acoustic model until real labelled onion data exists.

---

## 2 · What the model actually knows right now

### Vision detector
- Architecture: Faster R-CNN + MobileNet V3 Large 320 FPN, single class
  `onion`.
- Trained on 2,622 images, validated on 562, tested on 562 — leak-safe
  grouped split (near-duplicates kept together, no group spanning two
  splits).
- Test results: mAP@0.50 = 0.639, mAP@0.50:0.95 = 0.410, F1@0.5 = 0.656,
  precision@0.5 = 0.745, recall@0.5 = 0.586.
- Recommended score threshold 0.7 gives precision 0.858, recall 0.494.
- Limitations documented in the model card: single-class, no non-onion
  classes, CPU-trained, no mobile latency measured, split-source path
  recorded.

That means: the detector finds onions and mostly doesn't hallucinate onions
where there aren't any, but it is not a mature field model yet — and the
model card says so plainly.

### Vision attribute model
- Architecture: MobileNetV3-Small, three honest heads: 4-class commercial
  quality + rotten binary + sprout binary.
- Trained on real labels only: the 4-class head from Roboflow Onion Grading
  v7 (CC BY 4.0), the defect heads from Roboflow onions v1 (Public Domain).
- Test accuracy on the 4-class head is ~0.32, macro-F1 ~0.31 — low, and
  the documentation is honest about that.
- What it *can* do well in the carveout evaluation: rotten detection
  (precision 0.985, recall 0.877, F1 0.928) and sprout detection
  (precision 0.828, recall 0.744, F1 0.784) — those are the labels that
  actually exist in the source data.
- What it cannot do: damaged, undersized, bruising, freshness, shelf life.
  Those labels don't exist in the tracked data, so the model doesn't claim
  them. The old version did fabricate them; that was an audit finding and
  it's been removed.

### Acoustic model
- Classical baseline: RandomForestClassifier on real DSP features
  (rms, peak, dominant frequency, spectral centroid, bandwidth, rolloff,
  entropy, zero-crossing rate, band energies, resonance peak, decay rate,
  decay time).
- Today's artifact is a **synthetic demo**: trained on 16 oscillator-generated
  chirp responses, 11 train / 5 test. The model card says explicitly:
  "NOT an onion internal-defect classifier. Not clinically or industrially
  validated."
- The acoustic inference path has an **impact-presence gate** that runs
  before the model: if the recording doesn't contain a real tap or chirp
  excitation, it refuses to answer. That's the fix for "room noise got a
  defect prediction."

### What this means in plain language
- The vision model can find an onion and can tell you it's rotten or sprouted
  with reasonable confidence on the labels it was trained for.
- It cannot yet tell you Grade A / URS with authority, because the tracked
  labels are commercial-quality classes and defect flags, not procurement
  grades.
- The acoustic model today is a **demo** — it proves the pipeline works, but
  no judge should be told it diagnoses internal rot yet.

---

## 3 · What the policy engine actually does

The grading engine is separate from the models. It takes measurements and a
policy and returns a decision with reason codes.

The demo policy (`config/grading/demo_policy.json`):

- Grade A: 45–65 mm, no visible rot, no sprouting, internal defect
  probability ≤ 0.4.
- URS / relaxed: 35–70 mm, no visible rot, no sprouting, internal defect
  probability ≤ 0.6.
- Reject: visible rot allowed, sprouting allowed.
- Manual review below 0.65 model confidence, on multimodal disagreement,
  on missing calibration, above 0.35 occlusion.

The important honesty property: the policy source is marked
**source_verified: false** with the note that the 45–65 mm range follows a
press-reported Grade A figure but has not been verified against an official
government specification. The policy loader enforces that: if you set
source_verified to true, you must also supply source_url, verification_date,
and an official source_type — the code refuses to load a "verified" policy
without those. That's the guard against accidentally presenting demo
thresholds as procurement law.

There is also a strict-with-segmentation policy variant that requires a
measured defect surface-area percentage. Because the current detector outputs
boxes, not masks, that measurement is unavailable — and the engine correctly
escalates every onion to manual review with `MEASUREMENT_UNAVAILABLE`. That
file exists specifically to prove the architecture can represent stricter
future standards without retraining anything.

---

## 4 · How the non-onion case is handled

This is the case you most need to be able to demonstrate cleanly:
the user photographs a vegetable that is not an onion, and the system says
"not an onion," not "Grade A onion."

Today that flows like this:

1. The vision inference path produces an `is_onion` field. When a detector
   artifact is present and the embedding OOD gate is available, the gate
   contributes to that decision. When no detector is present, `is_onion` is
   `None` — "I can't tell" — not a guessed false.
2. Fusion short-circuits on `is_onion == False`: final label `not_onion`,
   freshness null, shelf-life "not_trained."
3. The server's `/scan/image` endpoint, when no detector artifact is loaded,
   returns `is_onion: False, status: model_unavailable` — it refuses, it
   doesn't fabricate.
4. There is a contract test (`test_non_onion_rejection`) asserting exactly
   that behavior, and a server test (`test_scan_image_requires_a_model_and_says_so`)
   asserting the API refuses when the model is missing.

The honest gap: the current attribute model's `is_onion` is primarily driven
by the embedding OOD reference, which is a machine-local artifact that isn't
in the repo (it's built from real onion images whose license is unresolved).
Without it, `is_onion` is `None`, meaning "unable to decide" rather than
"definitely not an onion." For a judge demo, the cleanest honest statement is:

- "The vision model detects onions and classifies visible defects; the
  non-onion rejection path exists and is tested; the most defensible
  non-onion answer today comes from the detector bounding boxes plus the
  OOD gate, and both are present when the detector artifact is loaded."

---

## 5 · How the acoustic case is supposed to work, and where it is today

The phone-only acoustic path is the technical differentiator. The design:

1. Phone speaker emits a logarithmic chirp, or the user gives a standardized
   tap.
2. Phone microphone records the response.
3. DSP extracts the features above.
4. An impact-presence gate checks that a real excitation event was captured —
   this is the gate that stops room noise from getting a prediction.
5. The classical model scores internal-defect probability.
6. Fusion only uses acoustic evidence when `grading_eligible` is true — which
   requires verified onion ground truth in the model's metadata. Today that
   flag is false, so acoustic results are reported but never fused into a
   grade.

The collection path to get real data exists and is wired:

- `POST /acoustic/collect` saves a recording into `raw/<ONION_ID>/` with a
  sidecar JSON.
- `POST /acoustic/ground-truth` sets the cut-open internal label — the only
  way `internal_label` is ever set.
- `GET /acoustic/collection-status` gives an honest trainability report
  against the 30-onion minimum.

The collection protocol, the ground-truth workflow, and the labeling tool
are all documented in `dataset-acoustic/` and `scripts/`. The collection-day
plan is in `dataset-acoustic/COLLECTION_DAY_PLAN.md`.

What's missing for a real acoustic model: 30 onions with phone taps, daily
chirp recordings, cut-open ground truth, and then a training run. Today there
are zero verified onions. That's stated plainly everywhere acoustic appears.

---

## 6 · The three things that must be true for a credible final demo

### (a) The vision model must not claim what it doesn't know
Say plainly: "The model detects onions, flags rot and sprout with the
reported precision/recall, and classifies into the four commercial quality
classes the source data actually defines. It does not claim Grade A / URS
by itself — that's the policy engine's job, and the policy thresholds are
clearly marked as demo until we verify them against an official spec."

### (b) The acoustic model must not be presented as validated
Say plainly: "The acoustic pipeline works end-to-end — capture, gate, feature
extraction, model, fusion. The model today is a synthetic demo that proves
the pipeline, not an internal-defect classifier. We have the collection
protocol and the ground-truth workflow to build the real model; that's the
next milestone, and the README says so."

### (c) The report must be evidence-backed, not just a number
The report generator produces: original + annotated image, per-onion reason
codes, policy id + version + hash, confidence, human-override audit trail,
QR code. That's the transparency deliverable the problem statement actually
asks for. If asked "why did this batch get this grade," the answer is a
policy decision with reason codes, not a model output you can't inspect.

---

## 7 · What to run right now, and what the result means

One command:

    python scripts/run_ci_gate.py

That runs:

1. **Reproducibility smoke test** — proves a clean clone has everything it
   needs, no hidden local paths, no untracked dependencies. Today: passes.
2. **Import every module** — every production module the app actually uses
   imports cleanly. Today: passes (PyYAML is now declared in requirements.txt,
   which was the real CI failure before this session).
3. **Unit + integration + contract tests** — 195 pass, the rest skip
   cleanly when artifacts are absent (that's intentional and documented).
4. **Grading + report-integrity gate** — the grading logic and report
   tamper-detection tests. Today: passes.

If all four pass, you have a green, reproducible, honest codebase to stand
on. If step 1 or 2 fails, the codebase depends on something local and you
need to fix that before any demo claim. If step 3 fails, the specific test
tells you what contract is broken.

---

## 8 · The real training commands, in case a judge asks

Vision detector:
    python training/train_detector.py --model-id vision-detector-v0.2 \
        --epochs 8 --min-size 320 --batch-size 4

Vision attribute model:
    python training/train_attribute_model.py --epochs 4 --split-mode grouped

Acoustic model (today: synthetic demo; real data path requires collection first):
    python training/train_acoustic.py --data dataset-acoustic/synthetic/demo_chirp_responses

Combined demo:
    python scripts/demo_onion_scan.py --image <path> [--audio <path>]

The demo script is self-contained: it takes image and audio from the command
line, imports only tracked inference modules, and never reaches into an
untracked local folder.

---

## 9 · The honest gaps, in order

1. **Non-onion rejection is honest but not maximally strong today.** The
   `is_onion` decision is best when the detector artifact and embedding OOD
   reference are both present. Without them it says "unable to decide," not
   "definitely not an onion." To strengthen this for the demo, load the
   detector artifact and have a difficult non-onion image ready.
2. **Grade A / URS is policy-driven, not model-driven, and the policy is
   marked unverified.** That's the honest state. To go further, obtain an
   official procurement specification and set source_verified to true with
   the required fields.
3. **The acoustic model is synthetic.** To make it real, run the 30-onion
   collection day, cut the onions open, label them, and train. Until then,
   present it as "pipeline proven, model not yet validated" — never as a
   working internal-defect classifier.
4. **The attribute model's 4-class head is weak (~0.32 accuracy).** The
   defect heads are the stronger story (rot F1 0.93, sprout F1 0.78). Lead
   with what's true and let the weakness be a documented limitation, not a
   hidden surprise.

---

## 10 · What to say when they ask the hardest questions

**"Is this a real model or a simulated result?"**
Every prediction comes from a trained artifact or returns an explicit
"model not available" / "insufficient data" / "retest required" status. The
test suite includes a contract that asserts the API refuses when the model
is missing. No hardcoded outputs, no random values, no fabricated accuracies.

**"How do you know it's not an onion?"**
The detector finds onion instances; the fusion path short-circuits to
`not_onion` when `is_onion` is false; the API returns `model_unavailable`
rather than guessing when the detector isn't loaded. The non-onion contract
test asserts that behavior. The honest caveat: the strongest non-onion
answer today uses the detector artifact plus the embedding OOD gate.

**"What grade is this onion?"**
The model doesn't assign a grade. The policy engine does, from measurements
and a versioned policy with reason codes. The policy thresholds are marked
unverified demo thresholds; the code enforces that verified policies need an
official source. That's the transparency the problem statement asks for.

**"Does the acoustic model detect internal rot?"**
Not yet. The model card says it's a synthetic demo. The pipeline that would
do it exists and is tested — capture, gate, features, model, fusion — but the
model needs verified onion ground truth, and today there are zero verified
onions. The collection protocol and ground-truth workflow are ready.

**"Where's the evidence?"**
Every decision records policy id, version, hash, reason codes, and confidence.
The report generator produces annotated images and an audit trail. The test
suite includes report-integrity tests that detect tampering. That's the
evidence trail procurement officers actually need.

---

## 11 · The short version for the demo table

- **What it does:** detects onions, flags rot and sprout, measures size with a
  calibration reference, applies a configurable Grade A / URS policy, produces
  batch percentages and an evidence-backed report with QR code.
- **What makes it different:** a phone-only acoustic pipeline that catches
  what the camera can't — implemented and gated, but with a clearly labelled
  synthetic-demo model until real labelled data exists.
- **What it doesn't claim:** it doesn't pretend the acoustic model is
  validated, it doesn't invent labels the data doesn't support, and it doesn't
  present demo policy thresholds as procurement law.
- **What's next:** verify the policy against an official spec, run the 30-onion
  collection day, train the real acoustic model.
- **Run it:** `python scripts/run_ci_gate.py` — one command, four checks,
  green means reproducible and honest.
