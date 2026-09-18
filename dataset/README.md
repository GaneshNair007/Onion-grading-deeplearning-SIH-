# Onion Training Dataset (Partitioned)

This directory contains the complete training dataset for the onion grading
project, repackaged into `part-001` … `part-018` so that every file stays well
below GitHub's 100 MiB per-file limit. All files are **whole original files,
copied unmodified** — nothing was split, re-encoded, or renamed.

## Summary

| Metric | Value |
|---|---|
| Source root | `C:\SIH` (this repository checkout) |
| Files collected | 20,054 |
| Unique files stored | 20,025 |
| Exact-duplicate references skipped | 29 (2,889,416 bytes saved) |
| Images | 20,046 `.jpg` (manifest rows incl. duplicate refs) |
| Annotations / metadata | 4 `.json` (COCO), 4 `.txt` (Roboflow READMEs) |
| Total stored bytes | 1,742,134,274 (≈ 1,742 MB / 1.62 GiB) |
| Parts | 18 |
| Largest single file | < 95 MiB |
| Checksums | `checksums.sha256` (SHA-256, one line per stored file) |
| Full file listing | `MANIFEST.csv` (path, part, source group, bytes, SHA-256, duplicate_of) |
| Run report | `SUMMARY.txt` |

## Part size policy

Each `part-NNN` directory holds a deterministic, non-overlapping subset of
whole files and never exceeds **100,000,000 bytes** (decimal; 1 MB =
1,000,000 bytes). Parts target 95–99 MB. The packing is deterministic:
running `tools/prepare_dataset_parts.py` twice on identical sources produces
identical parts, manifest, and checksums.

| Part | Files | Bytes |
|---|---|---|
| part-001 | 3,376 | 99,994,015 |
| part-002 | 1,227 | 99,982,766 |
| part-003 | 736 | 99,907,959 |
| part-004 | 746 | 99,985,965 |
| part-005 | 826 | 99,973,456 |
| part-006 | 689 | 99,887,351 |
| part-007 | 968 | 99,943,000 |
| part-008 | 1,109 | 99,801,176 |
| part-009 | 1,074 | 99,952,424 |
| part-010 | 1,207 | 99,967,362 |
| part-011 | 1,041 | 99,873,726 |
| part-012 | 1,068 | 99,900,429 |
| part-013 | 1,033 | 99,992,383 |
| part-014 | 1,362 | 99,908,146 |
| part-015 | 1,024 | 99,920,612 |
| part-016 | 1,001 | 99,939,716 |
| part-017 | 1,092 | 99,950,113 |
| part-018 | 446 | 43,253,675 |

## Source datasets included (inside the parts)

1. **`onion-grading-coco-segmentation/`** — Roboflow project
   *Onion Grading* v7 (2024-07-11), COCO segmentation export.
   Source URL (from bundled `README.dataset.txt`):
   <https://universe.roboflow.com/edward-csxhu/onion-grading>.
   Splits: `train/` (2,381 files), `valid/` (292), `test/` (293) plus COCO
   JSON annotations. License: CC BY 4.0 (per bundled README).

2. **`onion-coco-mmdetection/`** — Roboflow project *onions* v1 (2023-01-29),
   COCO MMdetection export. Source URL (from bundled `README.dataset.txt`):
   <https://universe.roboflow.com/onion-grading/onions-ciqkj>.
   `train/` (784 images + COCO JSON). License: Public Domain (per bundled
   README).

3. **`onion-leaves-and-bulb/`** — local dataset *Onion Leaves and Bulb*,
   folder-per-class layout (no bundled metadata; see
   `LICENSES_AND_SOURCES.md`). Class tree (leaf folders, file counts):

   ```
   1. Leaves/1. Healthy/1. Single              1,010
   1. Leaves/1. Healthy/2. Multiple            1,010
   1. Leaves/2. Unhealthy/1. Single            1,010
   1. Leaves/2. Unhealthy/2. Multiple          1,010
   2. Bulb/1. Healthy/1. Red Onion/1. Single   3,000
   2. Bulb/1. Healthy/1. Red Onion/2. Multiple 1,110
   2. Bulb/1. Healthy/2. White Onion/1. Single 3,000
   2. Bulb/1. Healthy/2. White Onion/2. Multiple 1,110
   2. Bulb/2. Unhealthy/1. Red Onion/1. Single 1,010
   2. Bulb/2. Unhealthy/1. Red Onion/2. Multiple 1,010
   2. Bulb/2. Unhealthy/2. White Onion/1. Single 1,010
   2. Bulb/2. Unhealthy/2. White Onion/2. Multiple 1,010
   ```

   The original local folder name was `Onion Leaves and Bulb Dataset/New
   Onion - Copy/`; inside the parts it is shortened to
   `onion-leaves-and-bulb/New Onion - Copy/…` (original filenames and class
   folder names are preserved exactly).

## Excluded from this dataset (intentionally)

* `Onion Leaves and Bulb Dataset.zip` (1,608,618,402 bytes ≈ 1.61 GB) —
  exceeds GitHub's 100 MiB limit. It was **CRC-32-verified bit-identical** to
  the extracted folder that *is* included, so no content is lost. The
  original stays on local disk, untouched.
* `Onion Grading.v7i.coco-segmentation.zip` (72.8 MB) and
  `onions.v1i.coco-mmdetection.zip` (35.8 MB) — also CRC-32-verified
  bit-identical duplicates of the included extracted folders; skipped to
  avoid uploading duplicate copies.
* `backend/` application code and trained model artifacts (`.joblib`) —
  not dataset content; model weights (`*.pt`, `*.pth`, `*.onnx`, `*.h5`,
  `*.tflite`), caches, logs, and virtualenvs are excluded by `.gitignore`.

## Verifying checksums

From the repository root:

```bash
# Linux / macOS / Git Bash (sha256sum)
sha256sum -c dataset/checksums.sha256

# Windows PowerShell
Get-Content dataset/checksums.sha256 | ForEach-Object {
  $h, $p = $_ -split '  ', 2
  $p = $p -replace '%20', ' '
  if ((Get-FileHash $p -Algorithm SHA256).Hash.ToLower() -ne $h) { "FAIL $p" }
}
```

Any `FAIL` line means the file differs from the original. `MANIFEST.csv`
additionally records the SHA-256 of every logical dataset file, including
duplicate rows whose `duplicate_of` column points at the part that holds the
first physical copy.

## Training instructions

* **Folder-per-class data** (`onion-leaves-and-bulb/…`) loads directly with
  `torchvision.datasets.ImageFolder`, after pointing the root at
  `dataset/part-00N/onion-leaves-and-bulb/New Onion - Copy` for whichever
  parts you need — or after joining all parts back into one tree locally
  (copy all `part-*/` contents into a single folder; paths do not collide).
* **COCO exports** (`onion-grading-coco-segmentation/{train,valid,test}`,
  `onion-coco-mmdetection/train`) load with `pycocotools` or any COCO-capable
  trainer (MMDetection, Detectron2, Ultralytics via COCO conversion). Each
  split's images and its `_annotations.coco.json` stay together inside the
  same part.
* Part boundaries never separate an annotation file from its images: each
  COCO split is fully contained in one part.

## Important notes

* **GitHub storage is not a replacement for a proper dataset repository.**
  A ~1.7 GB blob set on GitHub is convenient for provenance and backup, but
  for real training use a dataset host (Roboflow, Hugging Face Datasets,
  Kaggle, Zenodo, or institutional storage) with proper versioning and
  access control.
* **License and redistribution.** The Roboflow exports carry CC BY 4.0 and
  Public Domain notices bundled with them (`README.dataset.txt` /
  `README.roboflow.txt`, included in the parts). The leaves-and-bulb dataset
  arrived with **no license metadata** — see
  `LICENSES_AND_SOURCES.md`. Verify license terms before any redistribution.
* **Label semantics.** The folder labels here (`Healthy`/`Unhealthy`,
  `Leaves`/`Bulb`, COCO categories) are **not** guaranteed to correspond to
  Grade A / URS procurement grading labels. Do not treat them as procurement
  grades unless those labels are separately established and documented.
