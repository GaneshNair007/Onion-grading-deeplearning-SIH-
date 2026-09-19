# Non-onion negative set (`dataset-negatives/`)

**Status: empty.** No licence-clean non-onion photograph set is bundled with
this repository, and inventing one would be worse than admitting the gap.

## Why this directory exists

Non-onion rejection (`src/vision/rejection.py`) must be validated against real
negatives: a potato, a tomato, an apple, garlic, a cricket ball, a brown
object, an empty tray, a hand, a bag. Currently only **artificial** negatives
(flat colours, noise, geometric shapes) are used, which can prove the gate
detects nonsense but **cannot** prove it rejects the objects an inspector will
actually confuse with an onion.

## How to fill it

Photograph the negatives yourself — self-collected images are the only source
whose redistribution you can state with confidence.

```bash
python scripts/build_negative_set.py \
    --source ~/negatives/potato \
    --label potato \
    --consent "Self-photographed by <name>, <date>, on a tray in the centre" \
    --dry-run
```

Remove `--dry-run` to copy the images and write
`dataset-negatives/negatives_manifest.json`, which records for every image:
label, stored path, SHA-256, byte size, original path, the consent statement and
the timestamp. Exact duplicates are skipped; nothing is ever moved or deleted.

## Rules

1. Every image needs a consent/provenance statement. No statement, no copy.
2. Do not download copyrighted product photos.
3. Keep negatives in the same lighting/tray conditions as real scans — a
   negative that never occurs in the field proves nothing.
4. After collecting, run the rejection tests and record the measured
   false-onion rate in `docs/MODEL_CARDS.md` (replacing the current
   "artificial negatives only" limitation).
