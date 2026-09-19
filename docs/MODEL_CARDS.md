# ONION-Q — Model Cards

Every number below was produced by a run in this repository and is copied from
the run's own `metrics.json` / `model_card.json`. Metrics that cannot support a
claim are marked **not usable** rather than omitted.

`models/registry.json` is generated from the artifacts on disk by
`python scripts/build_model_registry.py`, and each entry carries
`metrics_confidence`:

| Value | Meaning |
|---|---|
| `leak_free` | Trained/evaluated on a near-duplicate-aware grouped split |
| `source_split_may_leak` | Official source splits; augmented siblings may straddle the split |
| `synthetic_demo_no_real_ground_truth` | Demo plumbing only — never onion intelligence |

---

## 1. `vision-detector-v0.1` — onion instance detection

| Field | Value |
|---|---|
| Task | Single-class (`onion`) instance detection with boxes |
| Architecture | `torchvision` Faster R-CNN + MobileNetV3-Large-320 FPN (COCO-pretrained, fine-tuned) |
| Why this architecture | `ultralytics`/YOLO is unavailable in this environment; torchvision is licence-clean (BSD-3), mobile-exportable and stable. Chosen for reproducibility, not novelty. |
| Artifact | `models/vision/detector/best.pt` (76.0 MB); first baseline preserved at `models/vision/detector-baseline-v1/` |
| Input | 320 px long side |
| Latency | 133 ms/image median, 421 ms p95 (CPU, this host) — mobile latency not measured |
| Training data | 2,622 train images (both COCO sources, leak-safe grouped split: 2,622 / 562 / 562) |
| Training | 8 epochs, batch 4, lr 2e-4, CPU, 4,348 s |
| Dataset fingerprint | `2443539b…c3507b` |

**Measured metrics (leak-safe grouped test split: 562 test images / 926 GT
boxes, score threshold 0.5)**

| Metric | v0.2 (current) | baseline v1 on the same split |
|---|---|---|
| AP@0.50 | **0.639** | 0.134 |
| AP@0.75 | 0.439 | 0.001 |
| AP@0.50:0.95 | 0.410 | 0.030 |
| Precision@0.5 score | 0.745 | 0.235 |
| Recall@0.5 score | 0.586 | 0.186 |
| F1@0.5 score | 0.656 | 0.208 |

The baseline's official-split row (AP@0.50 = 0.256, 40 test images) is retained
in `evaluation/detector_comparison.json`; it is **not comparable** to the leak-safe
numbers above — different data and difficulty. Apples-to-apples, v0.2 wins on
every metric on identical data.

**Honest reading:** this detector finds roughly two thirds of onions on unseen
photographs at IoU 0.5 with usable precision (0.87 precision / 0.55 recall at the
recommended 0.7 threshold). Its dominant failures, documented with image
galleries in `evaluation/detector_gallery/`, are crowded trays (overlap) and
tight crops. It exercises the full batch pipeline and beats the preserved
baseline on identical data, but **it is not field-ready** — status
`experimental`.

**Improvement path (no code change needed):**

```bash
python training/train_detector.py --epochs 12 --patience 3
```

The validation curve was still rising at epoch 8 (`docs/DETECTOR_EXPERIMENTS.md`,
§4), so more epochs and more tray-style annotated images are the known levers.

**Limitations**

* `metrics_confidence = source_split_may_leak` — official splits may contain
  augmented siblings of train images (documented in its own model card), so
  the reported AP may still be optimistic.
* Boxes only, no masks → defect surface-area percentage is unavailable and is
  reported as `null` (the policy engine escalates rather than guessing).
* No non-onion classes trained: rejection relies on the confidence gate plus the
  embedding-OOD fallback.

---

## 2. `vision-attributes-v0.1` — visible attributes

| Field | Value |
|---|---|
| Tasks | 4-class commercial grade (`extra_class`/`class_1`/`class_2`/`reject`) + binary `rotten` + binary `sprout` |
| Architecture | MobileNetV3-Small (torchvision, BSD-3) with a shared 576-d embedding and two heads |
| Artifact | `models/vision/attributes/attributes_v0.1_128px.pt` (4.44 MB) |
| Input | 128×128 |
| Latency | 10.9 ms/image (CPU, this host) |
| Split | **grouped / near-duplicate-aware**: 3,746 images → 2,272 groups → 2,622 / 562 / 562 |
| Training | 3 epochs, batch 32, lr 8e-4, CPU, 35.6 s |
| Dataset fingerprint | `2443539b…c3507b` |
| `metrics_confidence` | **`leak_free`** |

**Measured metrics**

| Head | Metric | Value | Test support |
|---|---|---|---|
| `rotten` | F1 / precision / recall / ROC-AUC | **0.928** / 0.985 / 0.877 / 0.975 | 211 (154 positive) |
| `sprout` | F1 / precision / recall / ROC-AUC | **0.784** / 0.828 / 0.744 / 0.866 | 211 (129 positive) |
| commercial grade (4-class) | accuracy / macro-F1 | 0.318 / **0.312** | 381 |

(Defect figures are the mmdetection-carve-out evaluation set; grade figures are
the grouped test split.)

**What this means for the product**

* `rotten` and `sprout` carry **real signal** and are used as measured
  attributes feeding the policy engine.
* The 4-class commercial grade head is at approximately chance (chance ≈ 0.25).
  It is reported for transparency and **is not used to decide a grade**. This
  measurement is precisely why the architecture is *attributes → policy* rather
  than *image → grade*.
* The `damaged`, `undersized`, `bruising`, `cleanliness`, `open_neck` and
  shelf-life outputs do **not exist** — no dataset labels support them. The
  pre-audit code hard-coded `damaged = 1.0` for every image; that bug is gone
  (audit P0.2).

**Data-leakage finding (kept on purpose)**

Training once on the *official* splits produced `quality_valid` accuracy
**0.938** but `quality_test` accuracy **0.168**. A diagnosis
(`scripts/diagnose_split_leakage.py`, results in `evaluation/split_leakage.json`)
showed the official `valid` split is **85.2 % near-duplicates of train**
(median embedding cosine similarity 0.9986) while `test` is 1.0 %. The 0.938
figure was leakage, not skill. Both the leaky and leak-free metric files are
kept side by side to document the finding.

**How to retrain**

```bash
python training/train_attribute_model.py --epochs 6 --input-size 160 --split-mode grouped
python scripts/build_model_registry.py     # refresh registry.json
```

---

## 3. `acoustic-v1-synthetic-demo` — **synthetic demo, not onion intelligence**

| Field | Value |
|---|---|
| Task | Classical baseline over DSP features (Random Forest, optional logistic regression) |
| Artifact | `models/acoustic/acoustic_baseline.joblib` (not committed; regenerate locally) |
| Training data | 16 **synthetic** chirp-response WAVs generated by `tools/generate_synthetic_acoustic_demo.py` |
| `metrics_confidence` | `synthetic_demo_no_real_ground_truth` |

**What it is:** a plumbing demonstration that the DSP → features → classifier
path runs, and a way to test the retest/quality flow. Its near-perfect scores
are an artefact of two oscillator-generated classes being separable by
construction.

**What it is not:** an onion internal-defect detector. There is **no public
onion acoustic dataset** (see `dataset-acoustic/README.md`); the only
onion-specific vibrometry study found is `paper_only`
(DOI `10.1016/j.biosystemseng.2022.07.004`) and its data is not published. The
pipeline therefore reports `ACOUSTIC_NOT_VALIDATED` and cannot change a grade.

**How to retrain the demo baseline**

```bash
python training/train_acoustic.py --data dataset-acoustic/synthetic/demo_chirp_responses
```

---

## Cross-cutting limitations

* All numbers are from **one CPU host** (Windows 11, AMD64). Latency is not a
  mobile measurement; no phone benchmark exists yet.
* No field validation of any kind has been performed. No claims are made about
  real procurement accuracy.
* Everything is trained on Roboflow-labelled photographs:
  *Onion Grading v7* (CC BY 4.0) and *onions v1* (Public Domain). The third
  directory in `dataset/` has **unresolved licensing** and is excluded from
  training by `src/data/provenance.py`.
* Detection and attribute metrics are reported for the exact split, sample
  counts, metric definition and date listed above. Nothing is extrapolated.
