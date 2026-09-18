# Acoustic Model — Status and Usage

## THE HEADLINE

> **The acoustic model in this repository is NOT an onion internal-defect
> detector. It is not clinically or industrially validated.**

No verified onion acoustic recordings exist (see
`dataset-acoustic/README.md` and `dataset-acoustic/SOURCES.md`). Nothing in
this directory may be presented as capable of detecting onion internal rot
until it is trained on real onion recordings with cut-open ground truth,
collected per `dataset-acoustic/collection_protocol.md`.

## What exists here

### 1. Classical baseline (Random Forest + Logistic Regression) — `training/train_acoustic.py`

- Extracts the full feature set from `src/acoustic/features.py` for every
  training WAV.
- Splits **by onion_id** (or by synthetic source group), never by recording.
- Trains a `RandomForestClassifier` (and optionally Logistic Regression)
  with class weighting.
- Reports accuracy, precision, recall, F1, and a confusion matrix.
- Saves the fitted pipeline to `models/acoustic/acoustic_baseline.joblib`
  together with a `model_card.json` that records **exactly which
  `dataset_type` values the training data carried**.

### 2. Deep audio model — deliberately NOT implemented yet

A compact log-mel CNN is only justified with enough **verified labelled
onion recordings**. The repository's data is synthetic (16 demo clips), so
training a CNN now would produce an overfit toy. The hook is documented in
the training script and will be enabled when `dataset-acoustic/raw/`
contains real data.

### 3. Inference — `inference/acoustic_inference.py`

- Runs the same DSP/QC path used at training time.
- Returns `internal_defect_probability`, `confidence`, `audio_quality`,
  and `model_version`, or `"retest_required"` when the quality gates fail.
- If no trained model file exists, it reports
  `status: "model_not_trained"` instead of inventing a prediction.

## Training data status

| Source | dataset_type | Used for | Onion ground truth? |
|---|---|---|---|
| 16 synthetic demo WAVs (`dataset-acoustic/synthetic/`) | `synthetic` | Pipeline smoke-test demo model | **No** |
| Coconut Mendeley dataset (not redistributed) | `related_produce_acoustic` | Nothing here; local pipeline reference only | **No** |
| Future `dataset-acoustic/raw/` recordings | `verified_onion_acoustic` | The future real model | Yes (cut-open protocol) |

The demo model trained by `train_acoustic.py` on the synthetic clips is
labelled end-to-end as a **synthetic demonstration classifier** — it learns
the generator's own two classes ("firm-like" vs "defect-like" resonance
parameters). That is useful to prove the plumbing works and nothing more.

## Usage

```bash
# Train the labelled synthetic demo baseline (smoke test):
python training/train_acoustic.py --data dataset-acoustic/synthetic/demo_chirp_responses

# Inspect a recording through the full pipeline:
python inference/acoustic_inference.py path/to/recording.wav
```

## What must happen before any real claim

1. Collect recordings per `dataset-acoustic/collection_protocol.md`
   (≥ 30 onions, longitudinal, one cultivar per batch, 3 recordings per
   onion per session, ambient baselines).
2. Cut-open ground truth with the fixed label vocabulary.
3. Repeatability analysis (within-onion vs between-onion variation).
4. Train on `verified_onion_acoustic` data only, split by onion_id.
5. Report metrics with sample size, cultivar, and validation design —
   then, and only then, may the README headline be updated.
