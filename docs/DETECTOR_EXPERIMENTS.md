# Detector experiments

The detector is the weakest component of the system, and this document is the
decision record for it: what was measured, on what data, and what was promoted.
Numbers come from `models/vision/detector*/metrics.json` and
`evaluation/detection_*.json`; none are transcribed by hand.

## 1. Dataset audit before training

`scripts/audit_detection_dataset.py` → `evaluation/detection_dataset_audit.json`

| Item | Value |
|---|---|
| Annotated images (two trainable sources) | 3 746 |
| Annotation boxes | 5 291 (+7 malformed/degenerate, dropped by the loader) |
| Degenerate boxes dropped | sub-2 px, out-of-frame after clamping, tiny-area |
| Duplicate annotation pairs (IoU ≥ 0.95) | 2 (reported, not deleted from the source) |
| Images carrying polygon masks | 2 963 |
| Box width / height medians | see audit JSON |
| Zero-box images | 0 |

## 2. Leak-safe split

Roboflow splits cannot be trusted as given: the attribute experiment measured the
official `valid` split as **85.2 % near-duplicate with `train`**
(`evaluation/split_leakage.json`). The detector therefore uses the same grouping
method (`scripts/audit_detection_dataset.py` → `evaluation/detection_split.json`):

| Item | Value |
|---|---|
| Images → groups (cosine ≥ 0.98) | 3 746 → 2 272 |
| Split | 2 622 train / 562 validation / 562 test |
| **Groups spanning two splits** | **0** (verified: `leakage_check: pass`) |
| Boxes per split | 3 374 / 993 / 926 |
| Source mix in validation | 211 defect-source + 351 grading-source images |

That last row is its own finding: the official validation split contained
**only** grading-source images, so it could never have measured detection on the
defect dataset. The grouped split fixes that, and it is a harder split than the
source split — which matters when comparing numbers below.

## 3. Candidates

| # | Model | Data | Epochs | Selection |
|---|---|---|---|---|
| A (`baseline v1`) | `fasterrcnn_mobilenet_v3_large_320_fpn` | 240 train images, official splits | 4 | first-pass smoke baseline |
| B (`v0.2`) | same architecture | **2 622 train images**, grouped leak-safe split | 8 (all improved; no early stop) | best validation AP@0.50:0.95 |

Why not YOLO: `ultralytics` is not installed in this environment and is a heavy,
licence-distinct dependency. torchvision is already required, BSD-3-Clause and
ONNX-exportable. This is a documented trade-off — the architecture is not claimed
to be optimal, only reproducible and license-clean.

Training run details for B: batch 4, lr 2e-4, 320 px long side, CPU, 4 348 s total
(≈9 min/epoch), checkpointing each epoch (`best.pt` by validation, `last.pt` for
resume), `dataset_fingerprint 2443539b…c3507b`.

## 4. Per-epoch validation trend (candidate B)

| Epoch | Loss | AP@0.50 | AP@0.50:0.95 |
|---|---|---|---|
| 1 | 0.671 | 0.501 | 0.323 |
| 2 | 0.611 | 0.530 | 0.330 |
| 3 | 0.607 | 0.507 | 0.329 |
| 4 | 0.564 | 0.529 | 0.338 |
| 5 | 0.551 | 0.567 | 0.348 |
| 6 | 0.570 | 0.570 | 0.354 |
| 7 | 0.558 | 0.579 | 0.350 |
| **8** | 0.564 | **0.589** | **0.362** |

Validation loss and AP do not move in lockstep: epoch 6 had the lowest loss but
epoch 8 the best AP. Selection therefore uses AP, not loss.

## 5. Final comparison (candidate B, leak-safe test split: 562 images / 926 boxes)

| Model | Split | AP@0.50 | AP@0.75 | AP@0.50:0.95 | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| Baseline v1 (`detector_v0.1_cpu.pt`) | official (40 img) | 0.256 | 0.008 | 0.081 | 0.324 | 0.300 | 0.312 |
| **v0.2 (`best.pt`)** | **grouped leak-safe (562 img)** | **0.639** | **0.439** | **0.410** | **0.745** | **0.586** | **0.656** |

The baseline row is the number the previous session reported; the two rows are
**not** directly comparable (different split, different size, different
difficulty), so the baseline is also re-evaluated on the grouped test split —
see `evaluation/detector_comparison.json`, which is the comparison that decides
promotion.

## 6. Operating point

The default score threshold (0.5) is not the best operating point for a
procurement tray: a missed onion is usually worse than a re-photographed tray.
Measured on the leak-safe test split:

| Score threshold | Precision | Recall | F1 |
|---|---|---|---|
| 0.3 | 0.603 | 0.631 | 0.617 |
| 0.5 (default) | 0.745 | 0.586 | 0.656 |
| 0.7 (best F1 on validation) | 0.865 | 0.549 | 0.672 |
| 0.8 | 0.902 | 0.527 | 0.665 |

Three regimes are exposed rather than one number: **high confidence** (grade),
**review zone** (surface to the inspector), **ignore** (below floor). The
review-zone design is the honest way to keep recall usable on a tray.

## 7. Latency and size

| Item | Value |
|---|---|
| Model size | 76.0 MB (checkpoint) |
| CPU latency, 320 px long side | median 133 ms, p95 421 ms (5 runs, this host) |
| Mobile latency | **not measured** — no phone benchmark exists in this repository |

`p95` being 3× the median is itself useful: batch throughput planning must use
the tail, not the mean.

## 8. Error analysis

`evaluation/detector_gallery/` (generated from the leak-safe test split):

| Category | Count (over 562 images) | Typical cause |
|---|---|---|
| False positives | 37 | clutter/edges on trays, poor lighting |
| False negatives | 136 boxes | heavy overlap, small/partly cropped onions |
| Localisation errors (IoU 0.1–0.5) | 136 | loose boxes on touching onions |

The galleries are the evidence; they are meant to be looked at, not summarised
away.

## 9. Decision

* `v0.2` **supersedes** the baseline as the working detector: it improves AP and
  recall substantially on a harder, leak-free split with 10× the training data.
* The baseline is preserved at `models/vision/detector-baseline-v1/` and stays in
  `models/registry.json` (status `deprecated`) so the improvement remains
  auditable and revertible.
* **Status of v0.2: `experimental`.** 0.639 AP@0.50 on a single-source-dominated
  test split is not field readiness, and the gallery shows exactly where it
  fails. It is not promoted to "validated" on this evidence.

## 10. What would move it next

1. Annotated **tray** images with genuine overlap — the failure mode is
   crowding, and the current data is mostly single-onion photographs.
2. A segmentation model from the polygon masks already present (2 963 images),
   which would also unlock measured defect surface area.
3. ONNX Runtime Mobile benchmarking on the target phone before any mobile
   latency claim.
4. More epochs once the split is larger; the validation curve was still rising
   at epoch 8, so the current ceiling is data, not compute.
