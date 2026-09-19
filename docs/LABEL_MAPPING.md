# ONION-Q — Label Mapping

The **only** place a source category becomes a model label is
`src/data/labels.py`. Unmapped categories become `unknown` and are excluded
rather than guessed.

## 1. Mapping table

| Source (`source_group`) | Source category | Model target | Evidence | Limitation |
|---|---|---|---|---|
| `onion-grading-coco-segmentation` | `Onions` | `is_onion = true` | source annotation | Generic onion class; no grade information |
| | `Class 1` | `quality_class = class_1` | source annotation | Commercial grade, not a defect statement |
| | `Class 2` | `quality_class = class_2` | source annotation | as above |
| | `Extra Class` | `quality_class = extra_class` | source annotation | as above |
| | `Reject` | `quality_class = reject` | source annotation | **Not** treated as "rotten": the source does not define it that way |
| `onion-coco-mmdetection` | `rotten` | `rotten = 1` | source annotation | Binary only; no severity, no surface area |
| | `sprout` | `sprout = 1` | source annotation | Binary only |
| `onion-leaves-and-bulb` | any | **excluded** | licence unresolved | Not used for training at all |

## 2. Labels that deliberately do not exist

| Attribute | Why it is absent |
|---|---|
| `damaged` | No source category. The pre-audit trainer hard-coded `damaged = 1.0` for **every** image — removed (audit finding P0.2) |
| `undersized` | No physical-scale label; size is a *measurement* (ArUco), not a learned class |
| `bruising` | No labelled source |
| `cleanliness` | No labelled source |
| `open_neck` / bottle-neck | No labelled source |
| `shelf_life_days` / freshness score | Requires longitudinal re-inspection labels; none exist. `freshness_score` is `null` everywhere |
| internal rot / hollow / watery | Requires cut-open ground truth; none exists (see `dataset-acoustic/collection_protocol.md`) |

## 3. Task supervision matrix

| Source | `is_onion` | `quality_class` | `rotten` | `sprout` |
|---|---|---|---|---|
| `onion-grading-coco-segmentation` | ✓ | ✓ | – | – |
| `onion-coco-mmdetection` | ✓ | – | ✓ | ✓ |

A missing `–` means **"not annotated"**, never "absent in the object". Training
code must therefore skip unlabelled samples per task rather than supplying a
zero; `src/data/labels.py::map_categories` omits absent targets for exactly
this reason.

## 4. Grade semantics (policy, not labels)

`grade_a` / `relaxed` / `reject` / `manual_review` are **not** dataset classes.
They are decisions produced by `config/grading/*.json` from measurements.
`reject` as a *source annotation* (`quality_class = reject`) and `reject` as a
*decision* are different things and are never conflated in reports: the report
records both the measured probability and the policy-derived decision.

## 5. Changing the mapping

Any change here changes:
1. the mapping signature inside `DatasetRegistry.fingerprint()` (so training
   runs record a different `dataset_fingerprint`), and
2. the effective training targets, requiring retraining and a refreshed
   `models/registry.json`.

Both are intentional: the fingerprint is what makes a metric reproducible.
