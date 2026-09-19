# Dataset Governance

Generated from `dataset/MANIFEST.csv` by `python scripts/dataset_governance.py`. Every source group present in the manifest is listed, whether or not it carries COCO annotations.

* Manifest files: **20054**
* Manifest bytes: **1,745,023,690**
* Duplicate files (skipped by SHA-256): **29**
* Dataset fingerprint: `2443539beb938064b6f2e1e0594c000b31da519d8f2f017b0beb878ad8c3507b`
* Generated: 2026-09-18T18:41:08.691402+00:00

## Source groups

| Source group | Files | Images | Bytes | License | Status | Trained on | Format |
|---|---|---|---|---|---|---|---|
| `onion-coco-mmdetection` | 786 | 783 | 35,957,280 | Public Domain | verified | yes | coco_json |
| `onion-grading-coco-segmentation` | 2968 | 2963 | 73,349,356 | CC BY 4.0 | verified | yes | coco_json |
| `onion-leaves-and-bulb` | 16300 | 16300 | 1,635,717,054 | License not detected | unresolved | no | none |

## Exclusions

* **`onion-leaves-and-bulb`** — Redistribution/training permission not sufficiently verified (license_status=unresolved; license: License not detected). The source also carries no COCO annotations, so it cannot be used for supervised training as packaged.

## Categories

* `training_sources`: `onion-coco-mmdetection`, `onion-grading-coco-segmentation`
* `excluded_sources`: `onion-leaves-and-bulb`
* `unresolved_sources`: `onion-leaves-and-bulb`
* `restricted_sources`: (none)
* `auxiliary_sources`: `onion-leaves-and-bulb`

A source group appears under training_sources only when its licence could be verified from bundled metadata. Groups whose rights are unresolved are listed explicitly under unresolved_sources and are never used for training.
