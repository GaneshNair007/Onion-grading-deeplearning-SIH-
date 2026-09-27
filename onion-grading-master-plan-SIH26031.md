# AI-Based Onion Quality Grading — Master Plan (SIH26031)

## 1. The Problem Statement, In Plain Terms

At onion procurement centres, grading is done manually — an inspector looks at a lot of onions and judges how much is acceptable. Different inspectors, or different centres, can reach different conclusions on the same lot. This causes:

- **Inconsistency** — one centre calls a batch Grade A, another doesn't.
- **Disputes** — farmers aren't told, in a verifiable way, why their lot was downgraded.
- **No evidence trail** — manual grading leaves no detailed, reviewable record.

**What is officially expected:** an AI-based **mobile application** that uses phone images to assess onion quality, identifies damaged, rotten, sprouted, and undersized onions, estimates **Grade A** and **Grade URS** percentages for a batch, and instantly generates a transparent, evidence-backed digital report.

**Important terminology correction carried forward from our research:** URS = **Under Relaxed Specification** — a real, officially defined, *accepted* relaxed-quality category (not "reject" and not an acronym for "undersized/rotten/sprouted"). It is enabled or disabled per active procurement policy, with its own diameter and defect thresholds distinct from Grade A.

---

## 2. Our Proposed Solution — Overview

We are not building a black-box classifier that outputs a single "good/bad" guess. We are building a **procurement-officer mobile tool** that:

1. Detects and grades **every individual onion** in a photographed tray (not just an overall image verdict).
2. Measures actual bulb size using an in-frame calibration reference, so "undersized" is a real millimeter measurement, not a guess.
3. Runs each onion's measurements through a **configurable rule engine** tied to the active Grade A / URS policy — so the officer sees *why* an onion was graded a certain way, and the same policy applies identically at every centre.
4. Generates an instant, evidence-backed digital report (annotated images, per-onion reason codes, policy version, audit trail) — this is what actually resolves disputes, because the grade is defensible against a stated rule, not an opinion.
5. **On top of this required core**, we add two enhancements the brief explicitly allows as valuable, time-permitting additions: an **acoustic hidden-defect check** (catches internal rot/hollowness invisible to the camera) and an **onion decay/shelf-life estimate** (predicts how long a graded batch remains sellable). Both stay clearly separated from the MVP so the core deliverable is never put at risk.

This keeps us fully aligned with what's actually being judged, while still giving us a genuine technical differentiator most other teams won't attempt.

---

## 3. Core MVP — What We Are Actually Judged On

### 3.1 Workflow

```
Officer opens app
      ↓
Creates/scans Batch ID + Farmer ID
      ↓
Selects active procurement policy (Grade A / URS thresholds, URS enabled or not)
      ↓
Spreads onions in a single layer on a tray
      ↓
Places calibration card / ruler in frame
      ↓
Captures 1–3 images
      ↓
AI detects each onion + visible defects
      ↓
App estimates bulb diameter from image scale
      ↓
Rule engine applies Grade A / URS rules
      ↓
App calculates batch percentages
      ↓
Digital report generated with evidence
      ↓
Officer reviews, approves, or flags for manual review
```

### 3.2 Per-onion output (what the model must produce for every detected onion)

```
Onion ID
Bounding box / segmentation mask
Estimated diameter (mm)
Damaged: yes/no + confidence
Rotten: yes/no + confidence
Sprouted: yes/no + confidence
Undersized: yes/no + confidence
Final result: Grade A / Grade URS / Rejected / Manual Review
Reason code
AI confidence score
```

### 3.3 Size calibration (required — this is what makes "undersized" a real measurement)

A phone photo alone can't give real-world size — apparent size changes with camera distance. Every capture must include a scale reference (printed calibration card, ArUco marker, or ruler on the same surface):

```
pixels_per_mm = reference_object_pixels / reference_object_known_mm
onion_diameter_mm = onion_diameter_pixels / pixels_per_mm
```

If no usable scale reference is visible in frame, the result must be **Manual Review** — never guessed as undersized or rejected.

### 3.4 Grading rule engine

The rule table is **configurable, not hardcoded** — stored with policy ID, version, effective date, and URS enabled/disabled status, saved into every report:

```
IF visible rot OR severe damage: REJECTED
ELSE IF image unclear OR calibration marker missing OR low confidence: MANUAL REVIEW
ELSE IF size + quality meet active Grade-A rules: GRADE A
ELSE IF URS enabled AND size + quality meet active URS rules: GRADE URS
ELSE: REJECTED or MANUAL REVIEW, per policy
```

Suggested starting defaults (editable settings, never claimed as a fixed universal standard):

| Rule | Grade A | Grade URS (if enabled) |
|---|---:|---:|
| Diameter | 45–65 mm | 35–70 mm |
| Visible rot | Not allowed | Not allowed |
| Severe damage | Not allowed | Not allowed |
| Sprouting | Not allowed (unless policy says otherwise) | Per active URS policy |

### 3.5 Batch percentages

```
Grade A % = N_GradeA / N_Total × 100
Grade URS % = N_URS / N_Total × 100
Rejected % = N_Rejected / N_Total × 100
Manual Review % = N_ManualReview / N_Total × 100
```

### 3.6 Instant digital report — the actual transparency deliverable

Minimum fields:

```
Report ID + QR code
Batch ID + farmer/supplier ID
Procurement centre + officer ID
Date/time (+ optional GPS)
Active policy version, URS enabled/disabled
Original + annotated images (onion outlines, labels)
Total detected / Grade A / URS / Rejected / Manual Review — counts and %
Defect breakdown: damaged, rotten, sprouted, undersized
Size distribution summary
AI confidence score
Human override + reason, if used
```

### 3.7 MVP tech stack

| Component | Option |
|---|---|
| Mobile frontend | Flutter or React Native |
| Vision model | YOLO (detection/segmentation) |
| Defect labels | healthy, damaged, rotten, sprouted |
| Size estimation | Segmentation + calibration marker |
| Backend | FastAPI / Flask / Node.js |
| Database | Firebase, Supabase, or PostgreSQL |
| Report | PDF/HTML with QR code + annotated image |

---

## 4. Our Differentiators — Explicitly Within Allowed Scope

The brief itself lists "acoustic testing for hidden-defect screening" as a valid time-permitting addition, and separately says storage/decay prediction is *not* required for the MVP but doesn't forbid it either. We treat both as clearly-labeled bonus layers, never as a replacement for Section 3.

### 4.1 Acoustic hidden-defect check (main technical differentiator)

**Why it matters:** a camera can only ever see the outside. Internal rot or hollowness — exactly the kind of defect that causes a dispute days after grading — is invisible to Section 3's vision pipeline. This is the one addition that solves a real gap in the required MVP itself, not just a nice-to-have.

**How it works, using only the phone's built-in speaker and mic (no added hardware):**
1. Phone speaker emits a logarithmic chirp (~100 Hz–8 kHz) at/near the onion.
2. Phone mic records the response.
3. FFT extracts resonant peak frequency, damping/decay rate, spectral centroid.
4. A small Random Forest / gradient-boosted regressor (trained on our own ground-truth dataset) flags likely internal defects and can optionally downgrade a visually-Grade-A onion to Manual Review.

**Grounding:** this mirrors published acoustic impulse-response research already used for firmness and internal-quality assessment in apples, pears, and watermelon (including hollow-heart detection), and at least one study used an almost identical small-speaker/small-mic reflected-signal setup for tomatoes and mandarins. We are applying a validated method to onions, not inventing unproven physics.

**Constraints to design around:** ambient noise (procurement centres are loud — use a noise-gated window or baseline subtraction), consistent phone-to-onion contact (solve via a guided on-screen step, not hardware), and a necessarily small initial training set (use explainable, low-data-friendly models, not deep audio nets).

### 4.2 Decay / shelf-life estimate (secondary, clearly-labeled stretch goal)

**Why it matters:** most real disputes happen after transport, not at the grading moment — a batch may be correctly Grade A at scan time and simply decay in transit. Predicting a decay trajectory ("Grade A now, likely URS in ~5 days") gives the officer and the buyer a shared, testable expectation instead of a single static verdict.

**Approach:** reframe as a time-to-event regression — predict days remaining before the batch's grade is likely to drop, using visual precursors (skin translucency, early discoloration gradient) plus the acoustic internal-condition signal where available.

**Positioning:** present this explicitly as beyond-MVP, built only if Section 3 and 4.1 are solid — it's the most ambitious piece and should never risk the core deliverable.

---

## 5. Two Mobile Model Tiers

To keep development risk low, we build in two clear tiers, both zero-added-hardware:

| Tier | Sensors | Covers |
|---|---|---|
| **Tier 1 — Core (must work)** | Camera only | Section 3 in full: detection, defects, calibrated size, rule engine, batch %, report |
| **Tier 2 — Enhanced (differentiator)** | Camera + built-in speaker + built-in mic | Tier 1 + Section 4.1 acoustic hidden-defect check, feeding into an improved confidence/decay estimate |

Tier 1 must be demo-ready first and independently — it is the actual graded deliverable. Tier 2 is what elevates the pitch.

---

## 6. Beyond This Hackathon — Future Directions (not build targets now)

- **Household variant:** the same per-onion vision + acoustic pipeline could be repackaged as a consumer app (individual freshness scoring, pantry tracking, "use these first" suggestions) — a plausible secondary market, but out of scope for the actual PS deliverable.
- **Dedicated industrial hardware:** a fixed-camera + piezo-contact-mic + conveyor device for high-throughput procurement/export lines, running the same core AI models at line speed with mechanical sorting output. Positioned purely as a scaling roadmap slide — "we're proving the AI cheaply on a phone before it needs dedicated hardware" — not something built during the hackathon.
- **Digital scale integration, GPS geotagging, QR batch traceability, multilingual UI, procurement manager dashboard, farmer appeal workflow** — all valid "if time remains" additions per the brief, roughly in that priority order after Section 4 is done.

---

## 7. Data Collection Plan

1. Acquire a spread of real onions (mixed condition — healthy, damaged, sprouted, rotten) and a printed calibration card/ArUco marker.
2. Photograph batches on a tray with the calibration marker in frame — this builds and validates the Section 3 detection/sizing/rule-engine pipeline.
3. For a subset, additionally run the acoustic chirp test daily over ~10–14 days, and periodically cut a few open to get real internal-condition ground truth — this trains Section 4.1's acoustic model and, if attempted, the Section 4.2 decay regressor.

---

## 8. Build Priority

1. **Tier 1 core, end-to-end** — detection → defect flags → calibrated size → rule engine → batch % → report. This is what gets judged; it must be reliable.
2. **Digital report polish** — annotated images, reason codes, QR code, policy version stamp. This is the actual "transparency" deliverable the PS cares about — don't underinvest here relative to the model.
3. **Tier 2 acoustic module** as the demo's standout moment, even at proof-of-concept accuracy.
4. **Decay estimate**, only if 1–3 are solid with time to spare.

---

## 9. Demo Script (under two minutes)

1. Officer creates a new batch in the app.
2. Officer places a calibration card beside a tray of mixed onions, captures an image.
3. App highlights each onion, flags defects, shows estimated sizes and undersized bulbs.
4. App displays Grade A / Grade URS / Rejected / Manual Review percentages.
5. **Differentiator moment:** pick one onion the camera rated fine → run the acoustic test live → show it gets correctly flagged for a hidden internal issue.
6. Officer opens the digital report: original + annotated image, policy version, reasons, QR code.
7. Officer manually overrides one uncertain item — override is recorded in the audit log.

**Pitch line:** *"We standardise onion procurement decisions through image-based defect detection, calibrated size measurement, configurable Grade A and URS rules, and evidence-based digital reports — with an acoustic check that catches what the camera can't. The officer keeps authority for difficult cases, but every decision becomes consistent, explainable, and auditable."*

---

## 10. Scope Boundaries

**Must build (this is what's graded):**
- Mobile image capture, onion detection/segmentation
- Damage, rot, sprout, undersize identification
- Calibrated size measurement
- Grade A / Grade URS batch percentages via a configurable rule engine
- Instant digital quality report with visual evidence and audit trail

**Add only if time remains, in priority order:**
- Acoustic testing for hidden-defect screening *(our chosen differentiator)*
- Offline on-device inference
- QR-based batch traceability
- GPS geotagging
- Digital scale integration / weight-based settlement
- Multilingual interface
- Procurement manager dashboard
- Onion decay/shelf-life prediction *(our chosen secondary differentiator)*
- Farmer appeal/review workflow
- Blockchain/immutable ledger

**Not required, don't build:** exact weight-only settlement, onion variety recognition, a farmer marketplace, a full agriculture platform.
