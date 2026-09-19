# ONION-Q — AI-assisted onion procurement grading

**SIH26031.** A measure → decide → audit workflow for onion procurement-centre
inspectors: a phone camera (and optionally the phone's own speaker/microphone)
produces *measurements*, a **versioned standards engine** turns them into a
procurement decision, and every uncertain onion is escalated for human review
with the reason attached.

> Models measure. Policy decides. Uncertainty is never hidden.

```bash
python -m venv .venv && . .venv/Scripts/activate      # Windows (bash)
pip install -r requirements.txt
python scripts/clean_clone_smoke_test.py              # proves the clone is self-contained
python -m pytest tests server/tests -q                # full suite
python scripts/demo_batch_scan.py --compose 9 --lot LOT-2026-0182
```

---

## What it does

| Mode | Input | Output |
|---|---|---|
| **Quick Batch Scan** | one or more tray images (calibration mat in frame) | onions detected, per-onion size + visible attributes, capture-quality warnings, policy decision, batch percentages |
| **Deep Scan** | 4 guided views of one onion (neck / base / side A / side B) + optional phone acoustic test | multi-view fusion, acoustic evidence with quality score, confidence-aware fusion, decision or `manual_review` |
| **Report** | any batch | tamper-evident JSON + farmer-language markdown + QR verification payload |
| **Sync** | field device | offline-first journal → idempotent API ingest → centre dashboard |

## The one architectural idea

```
IMAGE / AUDIO  →  MODELS  →  MEASUREMENTS  →  POLICY ENGINE  →  DECISION  →  REPORT
                                (numbers)      (JSON, hashed)    (grade/reject/review)
```

Because the standards live in `config/grading/*.json` and every decision records
`policy_id`, `policy_version` and `policy_hash`:

* changing a government threshold is a **configuration change**, not retraining;
* old measurements can be re-evaluated under a future standard;
* an auditor can see *why* produce was rejected, in plain language.

```bash
make batch                                   # demo policy
python scripts/demo_batch_scan.py --images demo/tray_calibrated.png \
    --policy strict_with_segmentation        # stricter rules, same models
```

## Honest status (read before believing any number)

| Item | Status |
|---|---|
| Onion detector | **Real**, trained on 2,622 leak-free images. AP@0.50 = 0.639 on a grouped leak-safe split (`experimental`, not field-ready — `docs/MODEL_CARDS.md`) |
| `rotten` / `sprout` attributes | **Real signal**: F1 0.928 / 0.784 on a leak-free split |
| 4-class commercial grade | macro-F1 0.312 (chance ≈ 0.25) — reported, **not used** for decisions |
| Size measurement | ArUco-calibrated only; otherwise an explicitly labelled pixel estimate |
| Acoustic internal defects | **Not validated.** No public onion acoustic dataset exists; the shipped model is a **synthetic demo** and cannot change a grade |
| Shelf-life / freshness score | **Does not exist** — no longitudinal labels. `freshness_score` is `null` everywhere |
| Reports | **Tamper-evident**, not tamper-proof |
| Field validation | **None yet** |

Full detail: [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) ·
[`docs/MODEL_CARDS.md`](docs/MODEL_CARDS.md) ·
[`docs/AUDIT_REPORT.md`](docs/AUDIT_REPORT.md)

## Layout

```
src/data/         dataset registry, label mapping, leak-free splits, provenance
src/vision/       detector, attribute model, multi-view fusion, size, capture QC, rejection
src/acoustic/     WAV loading, quality gates, FFT/STFT/log-mel features
src/fusion/       confidence-aware multimodal fusion
src/grading/      policy engine, reason codes, batch aggregation
src/reporting/    report generator, canonical hashing, QR payload
src/mobile/       guided capture protocol, offline-first journal
inference/        app-facing API (batch / deep / combined scan)
training/         detector, attribute and acoustic trainers
server/           FastAPI service (same functions the app calls)
dashboard/        static centre dashboard
mobile/android/   Kotlin reference implementation (not compiled)
docs/             architecture, datasets, model cards, workflow, demo script, judge Q&A
config/grading/   versioned procurement policies
dataset/          partitioned image dataset (MANIFEST.csv, part-001…018)
dataset-acoustic/ acoustic sources, protocol, synthetic demo, research notes
```

## Commands

```bash
make smoke                 # clean-clone self-containment check
make test                  # all tests
make fixtures              # calibration mat + composed tray fixture
make batch                 # batch scan demo → report
make deep                  # deep scan demo (views + audio)
make report && make verify # generate and verify a report hash
make registry              # regenerate models/registry.json
make train-detector        # longer detector training (documented improvement)
make api                   # uvicorn server.app:app --port 8000
make dashboard             # static dashboard on :8081
```

## What the inspector must still do

Place the calibration mat, keep onions separated, act on capture-quality
guidance, and resolve every `manual_review` onion by hand. The system never
forces a decision on uncertain evidence — that is a design decision, not a
missing feature.

## Repository branches

* `dataset` — the partitioned image dataset
* `acoustic-data` — acoustic sources, protocol and DSP pipeline
* `sih-winning-system` — this consolidated build

## Licence and data notice

Training images: Roboflow *Onion Grading v7* (CC BY 4.0) and *onions v1*
(Public Domain), recorded in `dataset/LICENSES_AND_SOURCES.md`. The
*Onion Leaves and Bulb* source has **no detected licence** and is excluded from
training until verified. Acoustic sources: see `dataset-acoustic/LICENSES.md`
(coconut tapping data is CC BY-NC-ND and is **not** redistributed).
GitHub is not a dataset repository; `dataset/` is a convenience mirror, not a
DOI-bearing archive.
