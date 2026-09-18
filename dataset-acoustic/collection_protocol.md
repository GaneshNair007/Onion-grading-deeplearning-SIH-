# Collection Protocol — Phone-Only Onion Acoustic Data

This protocol operationalizes Sections 2, 5, 7 (Architecture A) and 9 of
`onion-master-plan-updated.md` and incorporates the controlled-acquisition
and cultivar-aware validation requirements discussed in Landahl et al. 2022
(DOI `10.1016/j.biosystemseng.2022.07.004`, see
`research/landahl_2022_onion_ldv.json`).

**Status:** protocol for data that does not exist yet. Nothing in this
repository may be called an onion internal-defect result until recordings
collected under this protocol — with cut-open ground truth — are in `raw/`.

## 1. Why a protocol at all

Acoustic grading is only meaningful if recordings are repeatable and labels
are real. The published onion vibrometry work relied on controlled
excitation, fixed sensor geometry, and validation split by cultivar; a phone
microphone is noisier, so *our* procedure must be at least as disciplined.

## 2. Equipment (nothing external to the phone)

- One stock smartphone (record its model and OS version every session).
- The `capture_app`/demo in this repository (records WAV + metadata JSON).
- A quiet room; a soft mat to standardize onion placement.
- Kitchen scale + ruler (mass and diameter per onion — stored in metadata).
- Knife and cutting board for ground-truth sessions.

## 3. Subjects

1. Obtain 30–40 onions of **one cultivar per batch** (record `variety`).
2. Assign each a durable ID: `ONION_000001`, `ONION_000002`, …
   (mark it on the onion's papers/plate, never on the bulb).
3. Record per-onion static attributes on day 0: mass (g), equatorial
   diameter (mm), `variety`, source/shop.

## 4. Session schedule (longitudinal)

- Run sessions **daily for 10–14 days** per onion (per the master plan).
- Each session captures, per onion:
  - one photo (fixed distance/background — feeds the vision model);
  - **3 acoustic recordings** (below);
  - ambient baseline recording (first item every session).
- Cut open a subset on staggered days (e.g. 25% at day 4, 25% at day 7,
  remainder at day 10–14) to establish `internal_label` by
  `ground_truth_method: cut_open`.

## 5. Per-recording procedure (the standard measurement)

For each of the 3 recordings per onion per session:

1. **Position:** place the onion against the bottom edge of the phone,
   mic end, on the mat. Use the `equator` position for recording 1,
   `base` for recording 2, `neck` for recording 3 (schema `position`).
2. **Quiet check:** confirm ambient noise; the app's ambient score must be
   below the configured threshold before continuing.
3. **Ambient baseline:** app records ~1.0 s of room silence (saved as
   `..._ambient.wav`, linked in metadata).
4. **Excitation — Method A (chirp):** phone plays the 100 Hz–8 kHz
   logarithmic chirp (~1.0 s) while the mic records ~1.5 s
   (`capture_method: phone_chirp`).
5. **Excitation — Method B (tap fallback):** if chirp playback is
   unavailable or the leakage check fails, the app prompts a standardized
   knuckle tap on the onion at the marked spot while recording
   (`capture_method: phone_tap`). Use the same tap location and roughly the
   same force every time; 3 taps → 3 files.
6. The app runs its quality gate immediately (clipping, silence, SNR,
   duration) and asks for a re-record if any check fails. Never save a
   failed recording as a dataset row.

## 6. Naming and metadata

- Audio: `raw/onion_bulbs/ONION_000001/AUDIO_000123.wav`
  (WAV, 16-bit PCM, device default rate — record actual rate).
- Sidecar JSON per recording, one per `metadata_schema.json`, including the
  `capture_metadata` block (device model, OS, app, volume setting, ambient
  score, distance, contact, timestamp).
- `internal_label` stays **empty** until the cut-open session assigns it
  with `ground_truth_method: cut_open`. Never infer it from acoustics or
  filenames.

## 7. Ground truth (cut-open) sessions

For each onion cut open:
1. Photograph the cut cross-section (same photo pipeline; it becomes the
   vision-model label evidence).
2. Record the internal condition using the fixed vocabulary:
   `firm`, `early_rot`, `hollow`, `rotten` (extend the schema vocabulary
   only deliberately and document the change).
3. Update the sidecar JSONs of **all** recordings of that onion
   (`internal_label`, `ground_truth_method: cut_open`, cut date in notes).

## 8. Repeatability checks (before any modelling)

- Re-measure 5 onions a second time on the same day; compare the extracted
  features (resonant peak, damping, centroid). Report within-onion vs
  between-onion variation before claiming any separability.
- If within-onion variation swamps between-onion differences, fix the
  procedure — do not train a model on noise.

## 9. Split policy

- Splits are assigned **by `onion_id`** (e.g. 60/20/20 of onions), never by
  recording, to prevent leakage across days of the same bulb.
- The split tool assigns the `split` field; hand-edits are prohibited.

## 10. After collection

1. Run `tools/prepare_acoustic_dataset.py` to refresh `parts/`,
   `MANIFEST.csv`, `checksums.sha256`.
2. Only models trained on these recordings, with cut-open ground truth and
   onion-level splits, may be described as onion internal-defect models —
   and must state cultivar, sample size, and validation design.
