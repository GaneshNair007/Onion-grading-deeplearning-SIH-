# ONION-Q — AI-Assisted Onion Quality Grading (SIH26031)

## What this is

A procurement-grade onion inspection system built around three honest
principles:

- **No black-box output.** Every decision comes from a trained model, a
  configurable policy, or an explicit "I can't answer yet" status.
- **No fabricated labels.** Models are trained only on the labels that exist
  in the tracked datasets; the rest are deliberately absent and documented.
- **No hidden local data.** A clean clone runs the full test suite; the
  reproducibility smoke test enforces that.

## Two-tier design

**Tier 1 (required):** camera-only onion detection, visible-defect
classification, calibrated size measurement, configurable Grade A / URS rule
engine, batch percentages, and an evidence-backed digital report with QR
code, policy version, and audit trail.

**Tier 2 (differentiator):** phone-only acoustic hidden-defect screening
using the built-in speaker and microphone — with a clearly labelled
synthetic-demo acoustic model until real labelled onion data exists.

## Current model status (honest)

- **Vision detector:** Faster R-CNN + MobileNet V3 Large 320 FPN, single
  class `onion`. Test mAP@0.50 = 0.639, F1@0.5 = 0.656. Model card documents
  the limitations.
- **Vision attribute model:** MobileNetV3-Small with 4-class commercial
  quality head + rotten + sprout binary heads, trained on real labels only.
  Defect heads are the strong story: rot F1 0.928, sprout F1 0.784 on the
  carveout evaluation. The 4-class head is weak (~0.32 accuracy) and that is
  documented, not hidden.
- **Acoustic model:** classical Random Forest on real DSP features, **synthetic
  demo only** today. Model card says explicitly it is not an onion
  internal-defect classifier. The pipeline (capture → gate → features → model
  → fusion) works and is tested; the model needs verified onion ground truth.
- **Policy engine:** separate from the models. Converts measurements + a
  versioned policy into a decision with reason codes. Demo policy thresholds
  are marked `source_verified: false` and the code enforces that verified
  policies need an official source.

## Honest gaps

- Non-onion rejection is tested and honest, strongest when the detector
  artifact and embedding OOD reference are both present.
- Grade A / URS is policy-driven, not model-driven; demo thresholds are marked
  unverified.
- The acoustic model is synthetic until the 30-onion collection day produces
  cut-open ground truth.
- Shelf life / decay is not modelled — no longitudinal labels exist.

## Run the CI gate locally

    python scripts/run_ci_gate.py

That replays exactly what GitHub Actions runs: reproducibility smoke test,
module imports, unit + integration + contract tests, and the grading /
report-integrity gate.

## Training commands

    python training/train_detector.py --model-id vision-detector-v0.2 \
        --epochs 8 --min-size 320 --batch-size 4

    python training/train_attribute_model.py --epochs 4 --split-mode grouped

    python training/train_acoustic.py \
        --data dataset-acoustic/synthetic/demo_chirp_responses

    python scripts/demo_onion_scan.py --image <path> [--audio <path>]

## Repository status

- Branch: `sih-winning-system`
- Latest commit: `1dfaed2c467629439c7a68368fca71337ff9b9b4`
- GitHub Actions on that commit: **success**
  (<https://github.com/GaneshNair007/Onion-grading-deeplearning-SIH-/actions/runs/35667007608>)

## Dataset

- Partitioned onion training dataset: 20,054 files, 18 parts
  (`dataset/part-001`…`dataset/part-018`), every file below GitHub's 100 MB
  limit, largest single file under 2 MB.
- Sources inside the parts:
  - `onion-grading-coco-segmentation` (CC BY 4.0, Roboflow)
  - `onion-coco-mmdetection` (Public Domain, Roboflow)
  - `onion-leaves-and-bulb` (no license metadata — verify before
    redistribution)
- Acoustic data directory `dataset-acoustic/` is a separate, clearly labelled
  pipeline for the phone-only acoustic path. No verified onion acoustic data
  exists yet; the directory documents exactly what is and isn't there.

## Documentation

- `docs/JUDGE_REHEARSAL.md` — what to say, what's true, what's missing.
- `docs/ONION_Q_TECHNICAL_WHITEPAPER.md` — full technical writeup.
- `dataset/README.md` — dataset provenance, part sizes, checksums.
- `dataset-acoustic/README.md` — acoustic pipeline status and collection
  protocol.
- `config/grading/demo_policy.json` — the active demo policy with reason
  codes.
