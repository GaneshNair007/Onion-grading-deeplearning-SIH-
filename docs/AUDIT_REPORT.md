# ONION-Q — PHASE 0 AUDIT REPORT

**Audit date:** 2026-09-18
**Audited branch:** `acoustic-data` @ `2e281484a584b4b93c29a556204ac08315c873e1`
**Auditor method:** independent verification of every claim by reading files and running
commands; no claim below is inherited from an earlier report without re-verification.

---

## 1. Git state

```
origin   https://github.com/GaneshNair007/Onion-grading-deeplearning-SIH-.git (fetch/push)
branches: acoustic-data (local+remote, HEAD), dataset (local+remote, origin/HEAD)
HEAD:     2e281484a584b4b93c29a556204ac08315c873e1  "Add acoustic dataset pipeline and multimodal grading"
parent:   ea78532e858696c125507b4670cbd3f2c12ae727  "Add partitioned onion training dataset"
```

`git fetch --all --prune` performed. No `sih-winning-system` branch exists locally or on
the remote. Working tree has untracked local-only material (see §3).

## 2. Tracked repository content (what a clean clone actually gets)

Top level (10 entries): `.gitignore`, `dataset/`, `dataset-acoustic/`, `inference/`,
`models/`, `scripts/`, `src/`, `tests/`, `tools/`, `training/` — **20,118 tracked files**,
~1.75 GB (dominated by the partitioned image dataset).

**Not present in the repository at all:** `backend/`, `README.md`, `requirements.txt`,
`pyproject.toml`, `config/`, `docs/`, `mobile/`, `dashboard/`, `evaluation/`, CI workflows.

## 3. Hidden local dependencies (clean-clone breakers)

Untracked locally but referenced by tracked code:

| Local-only path | Referenced by | Consequence on clean clone |
|---|---|---|
| `backend/` (whole FastAPI app, 22 .py) | `inference/vision_inference.py`, `training/train_vision.py` | both **fail to import** |
| `backend/models/artifacts/vision_mobilenet_v1.0.0.pt` | `inference/vision_inference.py` (default model path) | vision inference unavailable |
| `backend/models/artifacts/acoustic_rf_v1.0.0.joblib` | nothing tracked (tracked acoustic code has its own path) | harmless |
| `C:\SIH\Onion Grading.v7i.coco-segmentation\` (untracked) | `training/train_vision.py` (hard-coded root path) | training script **aborts** |
| `C:\SIH\onions.v1i.coco-mmdetection\` (untracked) | `training/train_vision.py` | second dataset silently skipped |
| `C:\SIH\onion-master-plan-updated.md` | nothing (documentation only) | none |

Grep equivalents found: `sys.path.append(str(BACKEND_DIR))` (inference),
`sys.path.append(str(PROJECT_ROOT / "backend"))` (training), absolute Windows paths in
smoke-testing notes. **P0.1 confirmed.**

## 4. P0.2 — Vision training label fabrication (CONFIRMED)

`training/train_vision.py::load_coco_records` builds:

```python
records.append({..., "defects": [1.0, sprouted, 0.0, rotten], ...})
#                            ^^^ damaged hard-coded 1.0
```

- `damaged = 1.0` for **100 %** of training images → the model is taught that every onion
  is damaged. The head is worse than useless; it is anti-correlated with reality.
- `undersized = 0.0` always → constant label, zero information.
- Additional defect: `"has_onion": 1.0 if any(c.lower() == "onions" for c in cats) or cats else 0.0`
  — the trailing `or cats` makes the flag 1.0 whenever *any* category exists, so it never
  expresses "no onion".
- `rotten` also folds `Reject` (a **commercial grade**, not necessarily rot) into the rot
  label without documentation.

**Severity:** critical. Any metric produced by this script is meaningless.
**Not present in:** `training/train_acoustic.py` (verified — it derives labels from sidecar
metadata or explicit synthetic class tokens only).

## 5. P0.3 — Dataset path mismatch (CONFIRMED)

Real tracked layout (from `dataset/MANIFEST.csv`, columns
`part,path_in_repo,source_group,bytes,sha256,duplicate_of`; 20,054 rows):

```
dataset/part-001/onion-grading-coco-segmentation/train/_annotations.coco.json
dataset/part-001/onion-coco-mmdetection/train/_annotations.coco.json
dataset/part-002/onion-grading-coco-segmentation/valid/_annotations.coco.json
dataset/part-001/onion-grading-coco-segmentation/test/_annotations.coco.json
```

Actual repo path = `dataset/<part>/<path_in_repo>` (the part is a **separate column**; it is
not prefixed into `path_in_repo`). Training code instead expects
`<root>/Onion Grading.v7i.coco-segmentation/train/...`. **No registry exists** to bridge the
two. Images: 20,046 `.jpg`; annotations: 4 COCO JSON + 4 Roboflow README `.txt`.

## 6. P0.4 / P0.5 — Model provenance (CONFIRMED)

| Artifact (local only, untracked) | Training data | Status |
|---|---|---|
| `vision_mobilenet_v1.0.0.pt` | synthetic PIL-drawn onions (`backend/scripts/seed_dataset.py`) | not usable as final model |
| `acoustic_rf_v1.0.0.joblib`, `acoustic_rf_v1.7.597.joblib` | synthetic oscillator WAVs | smoke-test only |
| `models/acoustic/acoustic_baseline.joblib` (gitignored) | 16 synthetic demo clips | smoke-test only |

Honesty framing for these is already correct in tracked docs
(`models/vision/README.md`, `models/acoustic/README.md`, `dataset-acoustic/SOURCES.md`).

## 7. Available real labels (basis for honest task design)

| Source (tracked, under `dataset/part-*`) | Categories | Counts |
|---|---|---|
| `onion-grading-coco-segmentation` | `Onions`(0), `Class 1`, `Class 2`, `Extra Class`, `Reject` | train 2,380 imgs / 2,404 anns (+valid 292, test 293) |
| `onion-coco-mmdetection` | `rotten`(1), `sprout`(2) | 783 imgs / train only |

Derived **supported** tasks: onion **instance detection/segmentation** (single class),
`rotten` (binary), `sprout` (binary), commercial **quality class** (4-class).
**Unsupported** (must not be trained or claimed): `damaged`, `undersized`, `bruising`,
`cleanliness`, `open-neck`, shelf-life/decay, internal rot from vision.

## 8. Environment capability probe (this machine)

`torch 2.13.0+cpu`, `torchvision 0.28.0+cpu`, `opencv(cv2) 5.0.0`, `numpy 2.5.2`,
`scipy 1.17.1`, `scikit-learn 1.4.2`, `PIL 12.3.0`, `onnxruntime 1.28.0`, `fastapi 0.141.1`,
`pandas 2.2.2`. **Missing:** `ultralytics` (no YOLO), `onnx` (no ONNX export), `qrcode`.

Consequences recorded for planning: detector must come from **torchvision**
(`fasterrcnn_mobilenet_v3_large_320_fpn` is the mobile-oriented, licence-clean choice),
ONNX export code must degrade gracefully, QR generation needs a pure-python fallback or the
dependency to be declared.

Also observed: **two conflicting torch installations** (`...\Python312\site-packages` and
`...\Python312\Roaming\...site-packages`). Importing the second inside an already-initialised
process raises a Windows DLL access violation. Tracked code must therefore import torch
**once, lazily, behind a guard**, and tests must skip cleanly when that happens (already true
in `tests/test_multimodal.py`).

## 9. Duplicate / competing implementations found

- `backend/app/acoustic/dsp.py` vs `src/acoustic/features.py` — same DSP intent, two copies.
  Decision: keep `src/acoustic` as the canonical tracked pipeline (it has the quality gates,
  log-mel and tests); `backend/` is untracked and will either be imported from a tracked
  re-location or retired. No third copy will be created.
- `backend/app/fusion/fusion_engine.py` vs `src/fusion/fusion.py` — same roles. Decision:
  `src/fusion/fusion.py` is canonical (implements the spec contract with explicit statuses).

## 10. Missing pieces (gap list, priority order)

1. Any tracked backend/API layer (only the untracked `backend/` exists).
2. `README.md`, dependency manifest, `.env.example`, CI.
3. Dataset registry + provenance layer (`src/data/`).
4. Real trained vision model + model card with honest metrics.
5. Detector + non-onion rejection (no negative-class dataset exists anywhere).
6. Size calibration (ArUco mat) — cv2 5.0 provides `cv2.aruco`, so implementable offline.
7. Policy/standards engine + versioning (no config layer exists; URS/PSF values unverified).
8. Batch aggregation, reporting (hash + QR), verification endpoint.
9. Human-in-the-loop override store + review queue.
10. Mobile app, dashboard, offline sync.
11. Real acoustic collection tooling (protocol exists; capture tool does not).

## 11. Licence risks

| Source | Licence (as recorded) | Training use | Redistribution |
|---|---|---|---|
| Roboflow *Onion Grading* v7 | CC BY 4.0 | permitted with attribution | permitted |
| Roboflow *onions* v1 | Public Domain | permitted | permitted |
| *Onion Leaves and Bulb Dataset* | **not detected** | **unresolved — excluded from model training** | not redistributed |
| Coconut acoustic (Mendeley) | CC BY-NC-ND 4.0 | no (and not downloaded) | no |
| Landahl 2022 paper | © Elsevier | n/a (paper only) | citation only |

The leaves-and-bulb set is already committed under `dataset/` from the earlier branch; the
audit does **not** remove it, but marks `license_status = unresolved` and excludes it from
any training manifest until a licence is verified.

## 12. Verdict and first actions

Reproducibility is broken (P0.1/P0.3), the only vision trainer fabricates labels (P0.2), and
no real-photograph model exists (P0.4). The acoustic DSP, quality gates, fusion logic,
protocol and dataset-provenance documentation from the previous iteration are sound and are
preserved.

Execution order (as mandated): **PHASE 1 reproducibility → PHASE 2 dataset registry →
PHASE 3 label repair → PHASE 4 real detector → PHASE 5 attributes.** No dashboard or UI work
starts before a real model exists.

---

# 13. Resolution status (post-audit)

| # | Finding | Status | Evidence |
|---|---|---|---|
| P0.1 | Tracked code imported untracked `backend/` | **fixed** | `src/vision/model.py` is self-contained; `inference/vision_inference.py` and `training/*` no longer reference `backend/`. `scripts/clean_clone_smoke_test.py` asserts no tracked file mentions the forbidden paths. |
| P0.2 | Fabricated labels (`damaged = 1.0`, `undersized = 0.0`, `or cats` onion flag, `Reject` → rot) | **fixed** | `training/train_vision.py` replaced with a deprecation stub; `src/data/labels.py` is the only mapping; `training/train_attribute_model.py` trains only the heads that have labels. |
| P0.3 | Trainers required untracked folders at repo root | **fixed** | `src/data/dataset_registry.py` reads `dataset/MANIFEST.csv` and resolves images across parts (`scripts/inspect_dataset.py --verify-hashes`). |
| P0.4 | Only vision artifact was synthetic-trained | **fixed** | `models/vision/detector/detector_v0.1_cpu.pt` and `models/vision/attributes/attributes_v0.1_128px.pt` trained on real dataset images, with model cards, metrics and `models/registry.json`. |
| P0.5 | Acoustic model synthetic-only | **preserved and labelled** | Kept as `synthetic` demo; `metrics_confidence = synthetic_demo_no_real_ground_truth`; cannot change a grade. |
| §5 | Data leakage between official splits | **found and quantified** | `evaluation/split_leakage.json`: official `valid` is 85.2 % near-duplicates of train (median cosine 0.9986) vs 1.0 % for test; official-split metrics kept beside leak-free ones. |
| §10.1 | No tracked backend/API | **fixed** | `server/` (FastAPI) exposes the same functions the app calls, with tests. The untracked legacy `backend/` is left untouched and is not imported anywhere. |
| §10.2 | No README / dependency manifest / `.env.example` | **fixed** | `README.md`, `requirements.txt`, `.env.example`, `Makefile`, `scripts/clean_clone_smoke_test.py`. |
| §10.3–§10.9 | Registry, model, detector, rejection, size calibration, policy engine, batch, reporting | **implemented** | `src/data/`, `src/vision/`, `src/grading/`, `src/reporting/`, `inference/`, `config/grading/`. |
| §10.10 | Mobile app, dashboard, offline sync | **partially implemented** | `src/mobile/offline_store.py` + `capture_protocol.py` + tests; `dashboard/` static client; `mobile/android/` Kotlin reference (not compiled). |
| §10.11 | Real acoustic collection tooling | **partial** | Protocol + metadata schema + `scripts/build_negative_set.py` analogue for acoustic capture are present; the capture instrument itself requires a phone. |

## 14. Findings that remain open (stated plainly)

1. **Detector accuracy is weak** — AP@0.50 = 0.256 on 40 test images (first-pass run, 240 images × 4 epochs). Field use requires the longer training run documented in `docs/MODEL_CARDS.md`.
2. **No non-onion photo negatives** — rejection is validated against artificial negatives only.
3. **No verified onion acoustic ground truth** — no public dataset exists; acoustic evidence cannot influence a grade.
4. **Print-scale accuracy of the calibration mat is unverified** — geometry is self-checked (0.21 % px/mm error on the rendered mat), but a ruler check on a real print is still required.
5. **No mobile benchmark** — all latency figures are desktop CPU.
6. **Policy values are DEMO values** — `source_verified = false`; no official procurement specification document was obtained.
