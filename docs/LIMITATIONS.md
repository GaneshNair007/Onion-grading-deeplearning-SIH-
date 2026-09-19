# ONION-Q — Limitations

This file exists so that no claim in a pitch exceeds what the repository can
demonstrate. Every item names the evidence or the missing evidence.

## 1. Cannot be claimed (and why)

| Statement | Why it cannot be made |
|---|---|
| "Detects onion internal rot from phone audio" | No verified onion acoustic recordings exist anywhere public; the acoustic model is a **synthetic demo**. Verified cut-open ground truth is required (`dataset-acoustic/collection_protocol.md`). |
| "Predicts shelf life / freshness score" | No longitudinal re-inspection labels exist. `freshness_score` is `null` in every contract, and fusion refuses to synthesise one. |
| "X % accurate onion grading" | The only head that could produce "grade" output (4-class commercial grade) scores macro-F1 **0.312** (chance ≈ 0.25) on a leak-free split. Grading is done by measured attributes + policy, never by that head. |
| "Detects damage (bruising / undersized / open-neck)" | No labelled source. The pre-audit `damaged` label was a hard-coded `1.0`; it was removed. |
| "Exact size in millimetres from a photo" | Only when an ArUco calibration mat is visible. Without it, the system reports an explicitly-labelled pixel estimate and escalates to manual review. |
| "Fraud detection" | The system produces anomaly/statistical flags only (e.g. batch reason histograms). No fraud inference exists. |
| "Tamper-proof reports" | Reports are **tamper-evident** (SHA-256 over canonical JSON). Anyone can edit a file; the hash then fails verification. Not forgery-proof. |
| "Field-validated / industrial-grade" | No field trial has been run. All metrics come from dataset images on one CPU host. |
| "Works on any phone" | Phone speaker/microphone responses differ per device; the capture protocol records device metadata precisely because consistency is unproven. No mobile benchmark exists. |

## 2. Measured weaknesses (numbers, not adjectives)

* **Detector:** AP@0.50 = 0.256, recall@0.5 = 0.30 on 40 test images (240 train
  images, 4 epochs). In the 9-onion composed tray it found 6 instances. Improve
  with `python training/train_detector.py --max-images 1600 --epochs 10`.
* **4-class grade head:** macro-F1 0.312 on the leak-free test split — reported,
  not used.
* **`rotten` / `sprout` heads:** F1 0.928 / 0.784 on real labelled photographs
  (leak-free split). These are the two attributes the policy engine trusts.
* **Data leakage history:** training on official splits gave `valid` accuracy
  0.938 vs `test` 0.168. The official `valid` split is 85.2 % near-duplicates of
  train. Metrics from that run are kept only as a leakage record.
* **Capture-quality thresholds** (blur 60 Laplacian variance, glare 6 %,
  crowding 60 % coverage) are engineering defaults, not standards. They need
  field calibration.

## 3. Structural gaps

1. **No real tray photograph** in any licensed dataset → batch scanning is
   demonstrated on a *composed fixture* whose provenance file says so. The
   composed fixture also means measured diameters reflect the **fixture's**
   scale, not the photographed onions' true sizes.
2. **No non-onion negatives** → rejection relies on the detector confidence gate
   and an embedding-OOD fallback validated against artificial negatives.
3. **No acoustic ground truth** → the acoustic branch is quality-gated and
   recorded, but cannot change a grade (`ACOUSTIC_NOT_VALIDATED`).
4. **No segmentation masks** → defect *surface-area percentage* is unavailable;
   a strict policy that requires it escalates every onion with
   `MEASUREMENT_UNAVAILABLE` (this is demonstrated by
   `config/grading/strict_with_segmentation.json`).
5. **No human-in-the-loop review UI yet** → decisions and reason codes are
   produced and stored, but an inspector's override is not yet captured in the
   mobile flow.
6. **Licence gap** → the *Onion Leaves and Bulb* source has no detected licence
   and is excluded from training until verified.

## 4. What would remove each limitation

| Limitation | Concrete next step |
|---|---|
| Weak detector | Longer training run on more images; re-run `scripts/build_model_registry.py` |
| No negatives | `scripts/build_negative_set.py` with self-photographed negatives |
| No acoustic ground truth | Collect ≥30–40 onions per the protocol, then cut open and label |
| Surface area | Swap the detector for a mask-capable model and populate `damage_surface_pct` |
| Calibration accuracy | Print the mat, verify with a ruler, record the residual in `docs/MODEL_CARDS.md` |
| Policy verification | Obtain an official procurement specification; set `source_verified = true` only then |
| Mobile performance | Benchmark on the target device; record latency and sample rate |
