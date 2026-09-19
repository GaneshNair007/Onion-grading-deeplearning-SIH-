# ONION-Q — Procurement Workflow

## 1. Who this is for

**Primary user: the procurement-centre inspector** (NAFED/NCCF-style field
officer, quality-inspection staff, agricultural procurement operator).

Secondary: farmer (sees the plain-language summary), centre supervisor,
regional auditor, ministry administrator (see aggregated dashboard data).

The household "scan an onion in your kitchen" idea remains a possible future
expansion and does **not** drive navigation, data model, demo or pitch.

## 2. The operational flow

```
PROCUREMENT BATCH (lot arrives at the centre)
        ↓
TRAY IMAGE CAPTURE (calibration mat in frame)
        ↓
ONION DETECTION (instance boxes)
        ↓
PER-ONION VISUAL ATTRIBUTES + SIZE
        ↓
CAPTURE-QUALITY GATES (blur / glare / crowding / calibration)
        ↓
POLICY ENGINE  →  grade_a | relaxed | reject | manual_review
        ↓
BATCH AGGREGATION (counts + explicit percentages)
        ↓
TAMPER-EVIDENT REPORT (model + policy versions, hash, QR)
        ↓
OFFLINE STORAGE  →  SYNC  →  SUPERVISOR / MINISTRY DASHBOARD
```

Suspicious, borderline or low-confidence onions are escalated, and can be
re-examined with **Deep Scan** (four guided views + optional phone acoustic
test). Deep Scan is never run for every onion: it would destroy throughput.

## 3. What the inspector sees

```
Batch: MH-NSK-2026-00182        Lot: LOT-2026-0182

Scanned onions:      126
Accepted Grade A:     91   (72.2%)
Relaxed / Policy B:   20   (15.9%)
Rejected:             11   ( 8.7%)
Manual review:         4   ( 3.2%)

Policy: ONIONQ_DEMO_STRICT_V1 v1.0.0  (DEMO — not an official standard)
Models: vision-detector-v0.1, vision-attributes-v0.1
Report hash: sha256:41d6ab…
```

Percentages always use `total_detected` as the denominator and manual-review
onions are **never** silently excluded — the report states the rule
(`denominator_note`).

## 4. Decision rules (current demo policy)

`config/grading/demo_policy.json`, `source_verified = false`:

| Rule | Value |
|---|---|
| Grade A diameter | 45–65 mm (**calibration required**) |
| Relaxed (URS-style) diameter | 35–70 mm |
| Visible rot | not allowed → reject |
| Sprouting | not allowed → reject |
| Surface damage | `null` — the pipeline cannot measure it (boxes, not masks) |
| Max internal defect probability | 0.4 (Grade A) — inactive while acoustic evidence is unvalidated |
| Manual review if model confidence < | 0.65 |
| Manual review if calibration missing | yes |
| Manual review if multilayer disagreement | yes |

Strictness is a **configuration choice**, not a code change:

```bash
python scripts/demo_batch_scan.py --images tray.png --policy strict_with_segmentation
# → every onion becomes manual_review / MEASUREMENT_UNAVAILABLE, by design,
#   because that policy requires a defect-area measurement the pipeline cannot yet produce.
```

## 5. Standards provenance

`config/grading/POLICY_SOURCES.md` records where the numbers came from and what
was **not** verified. Current state: the 45–65 mm Grade-A figure and the 35–70 mm
relaxed band come from public reporting on the 2026 procurement cycle
(news context URLs, access date recorded) — **not** from an official
specification document. Hence `source_verified = false` and the
`POLICY_UNVERIFIED` reason code on every decision.

The `relaxed` grade exists because the real "URS" class has been introduced and
withdrawn repeatedly; that volatility is exactly why grading must be
policy-driven rather than baked into model weights.

## 6. Auditing a past batch

Every decision stores `policy_id`, `policy_version`, `policy_hash` and a
machine-readable reason-code histogram of the batch, so:

* the same measurements can be re-evaluated under a future policy;
* an auditor can see **which** rules rejected the produce, in plain language;
* a QR code on the printed report carries the report id + hash for verification
  (`scripts/generate_report.py --verify <report.json>`).

## 7. What the inspector must still do (no autopilot)

* Place the calibration mat and keep onions separated on the tray.
* Act on capture-quality guidance (blur/glare/crowding/framing) before grading.
* Resolve every `manual_review` onion by hand; the system never forces a
  decision on uncertain evidence.
* Treat the acoustic result as supporting information until cut-open ground
  truth exists.
