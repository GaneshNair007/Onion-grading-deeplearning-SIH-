# Adding real data (team playbook)

The system improves only when real labelled data is added. These commands are
the supported way to do it. Every one of them records provenance; none of them
overwrites or deletes existing data, and none of them retrains automatically.

The rule that makes all of this work: **a measurement is only as good as its
label, and a label is only as good as its source.** If you cannot name the
source and the person who verified it, the sample is not training data yet.

---

## 1. Add labelled onion images (visible condition)

```bash
# Put the photographs in a folder, then register them:
python scripts/add_labelled_images.py \
    --source /path/to/photos \
    --label rotten            # one of: rotten | sprout | sound
    --dataset-type verified_onion_image \
    --license "self-collected (team-owned)" \
    --collector "your name" \
    --notes "Nashik APMC, 2026-09-20, Red N-53, photographed on a mat"
```

The script copies (never moves), hashes each file, appends a row to
`dataset/training_manifest.csv`, and refuses duplicates by SHA-256.

## 2. Add non-onion (negative) images

```bash
python scripts/build_negative_set.py \
    --source /path/to/negatives \
    --provenance docs/negative_provenance.json \
    --out dataset-negatives
```

Negatives must contain potato, tomato, apple, garlic, hands, trays, bags and
background surfaces. Never scrape images whose licence you cannot state. This
set is what calibrates the OOD gate — without it, "not an onion" is a guess.

## 3. Add acoustic samples (one folder per onion)

```bash
python scripts/collect_acoustic_sample.py \
    --onion-id ONION_000123 \
    --variety "N-53" \
    --device "Pixel 7a / Android 14" \
    --capture-method phone_tap \
    --position equator \
    --audio tap_equator_01.wav tap_equator_02.wav tap_equator_03.wav \
    --ambient ambient.wav \
    --out dataset-acoustic/raw
```

Three taps are expected, not one: repeatability is part of the data quality.
If the coefficient of variation across taps is high, the sample is marked
`retest_required` instead of being quietly averaged.

## 4. Add destructive (cut-open) ground truth — the step that matters

```bash
python scripts/add_cut_open_ground_truth.py \
    --onion-id ONION_000123 \
    --internal-label soft_rot \
    --ground-truth-method cut_open \
    --photograph cut_surface.jpg \
    --notes "outer scales sound; neck soft, watery" \
    --labelled-by "your name"
```

Internal labels: `sound`, `neck_rot`, `soft_rot`, `internal_sprouting`,
`hollow`, `watery_translucent`, `other`, `uncertain`. Use `uncertain` when the
cut surface is ambiguous. Guessing here poisons the only dataset that can ever
justify an acoustic claim.

## 5. Rebuild derived artefacts

```bash
python scripts/dataset_governance.py                 # manifest + governance report
python tools/prepare_dataset_parts.py --dry-run      # repack parts under 100 MB
python scripts/inspect_dataset.py --verify-hashes
```

## 6. Retrain (only after the data is labelled)

```bash
# Vision attributes (rot / sprout), leak-safe grouped split:
python training/train_attribute_model.py --grouped-split --epochs 12

# Detector, leak-safe grouped split with checkpointing:
python training/train_detector.py --epochs 8 --batch-size 4 --min-size 320

# Acoustic baseline — runs only when real onion recordings exist:
python training/train_acoustic.py --require-verified-onion-data
```

`training/train_acoustic.py --require-verified-onion-data` **refuses to train**
unless `dataset-acoustic/raw` contains `verified_onion_acoustic` recordings with
recorded ground truth. That refusal is deliberate: a synthetic model that
reports an onion metric is worse than no model.

## 7. Evaluate and publish honestly

```bash
python scripts/audit_detection_dataset.py      # leakage + geometry audit
python training/train_detector.py --eval-only --weights <checkpoint>
python scripts/benchmark_inference.py          # latency with sample sizes
python scripts/export_onnx.py                  # ONNX export + parity check
python scripts/build_model_registry.py         # refresh models/registry.json
```

Every retrain changes `models/registry.json`; every metric must state dataset,
split, sample count and date. If a number cannot be reproduced, do not put it
in the pitch.

## 8. Active learning loop

```bash
python scripts/export_review_queue.py     # low-confidence, overrides, OOD
```

Work the queue by hand. Promote a case to training data only after a human
labels it with one of the commands above.
