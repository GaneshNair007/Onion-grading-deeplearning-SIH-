# ONION-Q — Demo Script (4 minutes)

Everything below is runnable exactly as written. Nothing depends on an
untracked local folder. If a model artifact is missing, the command **says so**
instead of printing fake numbers.

## 0. Setup (once, before the judges arrive)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate elsewhere
pip install -r requirements.txt
python scripts/clean_clone_smoke_test.py     # proves the clone is self-contained
python -m pytest tests -q                    # full suite
```

## 1. "The dataset is real and traceable" (30 s)

```bash
python scripts/inspect_dataset.py
```

Show: two licensed sources (CC BY 4.0, Public Domain), one source with an
**unresolved licence that is excluded from training**, per-source counts, and
the dataset fingerprint that every model card records.

> "Every training metric can be traced to a fingerprint of this manifest."

## 2. "The model measures; the policy decides" (60 s)

```bash
python scripts/demo_batch_scan.py --images demo/tray_calibrated.png --lot LOT-2026-0182
```

Show the per-onion lines, then the batch summary:

```
detected: 6     grade_a / relaxed / reject / manual_review  with explicit %
capture quality: per-image status + actionable guidance
```

Then change **only** the policy, without touching any model:

```bash
python scripts/demo_batch_scan.py --images demo/tray_calibrated.png \
    --policy strict_with_segmentation
```

> "A stricter standard escalates every onion to `manual_review /
> MEASUREMENT_UNAVAILABLE`, because that policy requires a defect-area
> measurement the current detector cannot produce. The system refuses to invent
> a number — and no retraining was needed to change the standard."

## 3. "Uncertainty is never hidden" (45 s)

```bash
# The same tray without the calibration mat:
python scripts/demo_batch_scan.py --images demo/tray_composed.png
```

> "Without the mat there is no millimetre value and every onion is escalated
> with `CALIBRATION_MISSING`. The system will not present pixels as
> millimetres."

## 4. "Deep Scan is the differentiator" (60 s)

```bash
python scripts/demo_deep_scan.py --demo-views 4 --audio dataset-acoustic/synthetic/demo_chirp_responses/synthetic_firmlike_001.wav
```

Then the honest part:

> "That run used four **different** onions to rehearse the pipeline, and it says
> so. In the field the four guided views are neck, base, side A and side B of
> one onion. The acoustic result is reported but **cannot change a grade**,
> because no validated onion acoustic ground truth exists anywhere public —
> that is what the `ACOUSTIC_NOT_VALIDATED` code means."

## 5. "Every report is auditable" (45 s)

```bash
python scripts/generate_report.py --from-scan local_data/scans/MH-NSK/scans.jsonl --qr
python scripts/generate_report.py --verify reports/REPORT-*.json

# Prove it is tamper-EVIDENT: edit one number, then verify again
python - <<'PY'
import json, glob
p = sorted(glob.glob("reports/REPORT-*.json"))[-1]
d = json.load(open(p)); d["summary"]["counts"]["grade_a"] = 99
json.dump(d, open("reports/tampered.json", "w"), indent=2)
PY
python scripts/generate_report.py --verify reports/tampered.json
```

> "The hash fails. Reports are tamper-**evident**, not tamper-proof — we do not
> overclaim."

## 6. "Offline first" (30 s)

```bash
python -m pytest tests/e2e -q          # scan → report → journal → sync-with-failure
```

> "Field work happens without connectivity: every scan is journalled locally,
> sync failures are retryable, and a synced record is marked — never deleted."

## 7. "The inspector stays in charge" (30 s)

```bash
# Start the API and the dashboard in two terminals:
uvicorn server.app:app --port 8000
dashboard/index.html        # open in a browser, click Load

# Record an inspector override next to the machine decision:
curl -X POST http://127.0.0.1:8000/review/override -H "Content-Type: application/json" -d "{\"onion_id\":\"ONION_SCAN_0003\",\"batch_id\":\"MH-NSK-20260919-0001\",\"inspector_id\":\"INSP-001\",\"machine_decision\":\"manual_review\",\"human_decision\":\"grade_a\",\"machine_confidence\":0.55,\"reason_code\":\"LOW_MODEL_CONFIDENCE\",\"note\":\"firm bulb, no soft spots\"}"
curl http://127.0.0.1:8000/dashboard/overrides
```

> "The override never replaces the machine decision: it is stored beside it, so
> the disagreement rate and the reasons become evidence about where the model
> is actually weak."

## 8. "Failure is a feature" (45 s)

Deliberately show what the system refuses to do. Judges score this higher than
another green checkmark:

| Input | Expected output | Why it matters |
|---|---|---|
| Blurred / crowded tray | `manual_review` + capture guidance | no grade from an unusable photo |
| Tray without the calibration mat | `CALIBRATION_MISSING`, `diameter_mm = null` | no pixels presented as millimetres |
| Non-onion image | rejected (`NOT_AN_ONION`) | the OOD gate exists; its calibration is still a limitation we state |
| Noisy / silent recording | `retest_required`, vision-only result | poor audio never changes a grade |
| Acoustic + vision disagree | `manual_review`, `MULTIMODAL_DISAGREEMENT` | disagreement is escalated, not averaged |
| Model artifact missing | `model_unavailable`, nothing graded | a missing model is never faked |
| Network down | record stays in the local journal | offline-first is tested, not asserted |

```bash
python -m pytest tests/e2e/test_production_safety.py -q   # the contracts behind this table
```

## 9. The one-slide claim

> "ONION-Q converts subjective onion procurement grading into a measurable,
> auditable digital workflow: models measure, a versioned standards engine
> decides, and every uncertain case is escalated for human review with the
> reason attached."

## Questions to expect

See `docs/JUDGE_QA.md` — including the hardest ones (detector accuracy,
acoustic honesty, licence status, and why the 4-class grade head is reported as
unusable).
