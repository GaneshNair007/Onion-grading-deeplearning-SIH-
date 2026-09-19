# ONION-Q — Datasets

## 1. Image dataset (tracked, partitioned)

Stored under `dataset/` as size-balanced parts (`part-001` … `part-018`,
1.74 GB, no file above 100 MB), described by `dataset/MANIFEST.csv`
(`part`, `path_in_repo`, `source_group`, `bytes`, `sha256`, `duplicate_of`).

| `source_group` | Contents | Images | Licence | Licence status |
|---|---|---|---|---|
| `onion-grading-coco-segmentation` | Roboflow *Onion Grading v7* — commercial grades `Class 1`, `Class 2`, `Extra Class`, `Reject`, plus `Onions` | ~2,900 | CC BY 4.0 | **verified** |
| `onion-coco-mmdetection` | Roboflow *onions v1* — `rotten`, `sprout` | ~780 | Public Domain | **verified** |
| `onion-leaves-and-bulb` | *Onion Leaves and Bulb* — Healthy/Unhealthy leaves and bulbs | ~16,300 | *none detected* | **unresolved** |

Full per-file detail: `dataset/MANIFEST.csv`, `dataset/LICENSES_AND_SOURCES.md`,
`dataset/checksums.sha256` (verify with `sha256sum -c dataset/checksums.sha256`).

**Licence governance.** `src/data/provenance.py` maps
`license_status → training_allowed`. The unresolved source is
**excluded from training** and reported under `excluded_sources` in
`dataset/training_manifest.csv`. It is not silently used.

```bash
python -m src.data.provenance              # writes dataset/training_manifest.csv
python scripts/inspect_dataset.py          # counts, splits, licence status
```

### Splits

* Attribute training uses a **grouped, near-duplicate-aware** split
  (`src/data/splits.py`): 3,746 images → 2,272 groups → 2,622 / 562 / 562.
  Augmented copies of one photograph never straddle train/test.
* Detector training uses the **official source splits** (documented as
  `source_split_may_leak` in the registry).
* Future locally collected data must split **by `onion_id`**, never by image,
  and all views of one onion stay in one split.

### Known dataset limitations

* No tray/batch photographs: images are single onions, so batch scanning is
  exercised with a composed fixture (`scripts/compose_tray_image.py`) whose
  provenance file states it is a fixture, not a field photograph.
* No non-onion photographs are licensed in this repository, so rejection is
  validated against the detector gate plus **artificial** negatives only
  (`src/vision/rejection.py`). A real negative set (potato, apple, garlic,
  hands, empty tray) is still required — see `scripts/build_negative_set.py`
  and `docs/LIMITATIONS.md`.
* No calibration-mat photographs from the field yet.

## 2. Acoustic dataset (`dataset-acoustic/`)

See `dataset-acoustic/README.md`, `SOURCES.md`, `LICENSES.md` and
`collection_protocol.md` for the full record. Summary:

| Item | Type | Status |
|---|---|---|
| Landahl et al. 2022, *Biosystems Engineering* 221:258–273 (onion LDV vibrometry, DOI `10.1016/j.biosystemseng.2022.07.004`) | `paper_only` | Cited; data not published. Used to design the collection protocol only. |
| Related onion papers (e-nose, internal-rot spectral) | `paper_only` | Citation metadata only |
| Coconut tapping dataset (Mendeley `hxh8kd3snj`, CC BY-NC-ND 4.0) | `related_produce_acoustic` | **Not redistributed** (no-derivatives licence + 278 MB single file). Metadata + manual download script only. |
| Synthetic demo chirp responses (16 WAVs, project-generated) | `synthetic` | Tracked, clearly labelled |
| Verified onion acoustic recordings | `verified_onion_acoustic` | **Empty — none exist.** Collection protocol ready. |

**Headline:** no public, redistributable onion acoustic dataset was found. The
project therefore contains **zero** verified onion acoustic ground truth, and
the acoustic model cannot influence a grade. Any statement to the contrary
would be false.

## 3. Non-onion negatives (to be collected)

`dataset-negatives/` is a placeholder for a small, licence-documented negative
set. `scripts/build_negative_set.py` ingests locally photographed negatives
(phone photos of potatoes, apples, garlic, hands, empty trays, balls, brown
objects) and writes a provenance sidecar per image. Self-collected photographs
are the only source that can be redistributed without licence doubt, which is
why the script asks for a licence/consent statement per batch.
