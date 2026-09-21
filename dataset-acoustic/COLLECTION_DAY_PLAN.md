# Collection Day Plan — 30 onions, taps, cut-open labels (one day)

**Goal:** reach `ready_for_training` — 30 onions with verified cut-open
labels — in a single day, using only the tools already in this repository.
This is the **cross-sectional baseline**: it trains the binary
internal-defect screening model. The longitudinal protocol
(`collection_protocol.md`, daily sessions × 10–14 days with staggered
cut-open) remains the research-grade extension for a later batch; the same
tooling runs it unchanged.

**Honesty rules that apply all day** (they are enforced by the tools):

- `internal_label` exists only after the onion is cut open. Appearance
  guides *purchasing diversity*, never labels.
- Every recording is saved with a per-WAV sidecar whose label fields stay
  `null` until the ground-truth step fills them.
- Metrics printed at the end of the day are **pilot numbers on 30 onions** —
  the minimum to quote at all, never "validated performance".

---

## 0. Shopping (evening before, ~30 min)

| Item | Qty | Notes |
|---|---|---|
| Onions, **one cultivar** | 30 + 6 spares | Same lot where possible. **Deliberately buy a mix of conditions**: fresh firm bulbs AND advanced ones (soft neck, sprouted, sunken/flabby sides). Target roughly **half sound / half defective** after cut-open. If all 30 cut out `sound`, the trainer refuses to train (one class only) and the day is wasted. |
| Paper plates + marker | 36 | One ID per plate: `ONION_000001` … |
| Kitchen scale (g) | 1 | Static attribute per onion |
| Ruler or caliper (mm) | 1 | Equatorial diameter |
| Knife, board, gloves | — | Cut-open station |
| Phone/camera | 1 | Cut-surface photographs |
| Charger, spare cables | — | A dead phone ends the day early |

Note the cultivar name and shop once — it goes into every onion's notes.

## 1. Setup & smoke test (30 min, before any onion is spent)

```bash
# Smoke test against a SCRATCH dir first (never pollutes the real dataset):
ONIONQ_ACOUSTIC_RAW_DIR="$PWD/local_data/smoke" \
  python -m uvicorn server.app:app --port 8900
```

1. Open `http://127.0.0.1:8900/dashboard/app/scan.html`
   (from a phone on the same Wi-Fi use the laptop's LAN IP — real phone
   hardware makes the "phone-only" story literally true).
2. Click **Record guided tap** with an onion 2–5 cm from the mic, tap firmly
   3×. Expect `status: valid` (research-only probability shown) — this proves
   mic + gate + model all work. `no_impact_detected` on the *smoke* onion is
   a mic/technique problem to fix now, not later.
3. Try **Record + SAVE tap** once against the scratch dir; confirm the saved
   filename appears in `local_data/smoke/`.
4. **Restart the server with NO override** — from here every save lands in
   the real `dataset-acoustic/raw/`:

```bash
python -m uvicorn server.app:app --port 8900
```

Roles (solo works too, ~4–6 min/onion): one person on onions/IDs/scale, one
on the laptop (record + label forms), one cutting/photographing.

## 2. Check-in & static attributes (45 min for 36 onions)

For each onion, on its plate:

1. Weigh it (g), measure equatorial diameter (mm).
2. In the page's **Device**/notes fields record structured text — the page
   has no dedicated weight/variety inputs, so use machine-parseable notes:

```
notes: variety=<cultivar> mass_g=182 diameter_mm=71 source=<shop>
```

3. Leave the plate ID visible next to the onion for the whole session.

## 3. Per-onion measurement block (~3 min each → ~100 min for 30)

For `ONION_xxxxxx` (use **Next free ONION id** once, then type the rest):

1. Onion on the hard table, mic 2–5 cm away.
2. **Record ambient baseline** once per hour or whenever the room changes
   (fan on/off, door open).
3. **Three recordings**, changing Position each time:
   - equator → *Record + SAVE tap* → tap firmly 3× during the 3 s window
   - base → repeat
   - neck → repeat
   Same spot, similar force every time (the collector's repeatability check
   uses CV ≤ 0.35 across taps — consistency is data quality).
4. **Cut it open** (cross-section through the equator), photograph the cut
   surface with the ID plate in frame.
5. **Ground truth form** (same page, lower section): the onion id, the
   verified interior label, your real name, upload the cut photo → Submit.

Label vocabulary (fixed; pick the closest, `uncertain` is a valid answer):

| Label | Use when the interior shows |
|---|---|
| `sound` | firm flesh, no discolouration, no odor |
| `internal_defect` | any rot — brown/black/watery flesh, fungal growth |
| `hollow_or_abnormal` | hollow centre, double centre, internal sprouting cavity |
| `sprouted` | interior sprout core visible (interior otherwise sound) |
| `external_defect_only` | interior sound; damage was skin/scale only |
| `uncertain` | genuinely ambiguous after inspection |

**Mid-day checkpoint (15 min):** press **Collection status** — expect
`onions_started ≈ 15–18`, `recordings ≈ 3×` that, `recordings_labelled`
equal to completed onions. Check your running class balance: if you already
have 20 `sound` and 3 defective, prioritise the advanced-looking spares for
the afternoon. Copy `dataset-acoustic/raw/` to a USB stick (copy-only) —
a second copy of the day's data before you leave the table.

## 4. End-of-day verification (30 min)

```bash
# 1. Status: at exactly 30 verified onions this flips to ready_for_training.
curl -s http://127.0.0.1:8900/acoustic/collection-status | python -m json.tool

# 2. Train the first real model on the day's data.
python training/train_acoustic.py --data dataset-acoustic/raw \
    --require-verified-onion-data --out-dir models/acoustic/pilot_day1
```

Reading the output honestly:

- `verified onion recordings: ~90` and zero `SKIPPED (quality)` lines means a
  clean day; skipped lines name exactly which recordings to re-record (rare).
- Confusion matrix / F1 on 30 onions is a **pilot number** — record it in the
  model card context, never present it as validated accuracy.
- The 5-onion repeatability re-check (protocol §8): for 5 onions record 3
  fresh taps into a scratch folder and run
  `python scripts/collect_acoustic_sample.py --onion-id <id> --audio tap1.wav tap2.wav tap3.wav --device "<same device>" --out local_data/repeatability`
  — the printed CV per feature is your within-onion variation. If it exceeds
  the 0.35 limit, fix technique before the next session.

## 5. Wrap-up (20 min)

```bash
git status --short dataset-acoustic/raw | head     # ~90 WAVs + sidecars, ~30–60 MB
git add dataset-acoustic/raw dataset-acoustic/COLLECTION_DAY_PLAN.md
git commit -m "data: day-1 collection — 30 onions with cut-open ground truth"
git push origin sih-winning-system
```

Committing the WAVs directly is correct here — the whole day fits far below
GitHub's 100 MB-per-file limit; the `parts/` machinery is only for large sets.

## Contingencies

| Problem | Answer |
|---|---|
| Gate keeps saying `no_impact_detected` on classify | Collection saves anyway (the gate runs at *analysis* time, not save time) — but stop and fix mic distance/force; use the smoke onion until a tap reads `valid`. |
| Everything is cutting out `sound` | Purchasing problem, not labelling. Send someone for advanced onions; better an unbalanced honest day than a fake one. |
| Server crashes mid-day | Data is already on disk. Restart, continue; ids from **Next free ONION id**. |
| A label was entered wrongly | Never re-submit GT via the page (it refuses re-labelling by design). Correct with `python scripts/add_cut_open_ground_truth.py --onion-id <id> --internal-label <correct> --photograph cut.jpg --labelled-by <name> --force --notes "correction: <reason>"`. |
| Team member wants to enter labels later at a laptop | Files-first path works identically: `scripts/collect_acoustic_sample.py` for taps, then the same GT script — both write the identical trainer format. |

## After the day

- 30 verified onions → the trainer runs and the acoustic model's
  `research_only` status can be upgraded **only** in the sense the data
  supports: a *pilot* internal-defect screening model, split by
  `onion_id`, metrics quoted with n=30 attached.
- Next increments: the longitudinal batch (10–14 days, staggered cut-open,
  per `collection_protocol.md`), cultivar #2 for the cultivar-aware
  validation the Landahl paper demands, and enough data to move from the
  30-onion minimum toward a test set that deserves the word.
