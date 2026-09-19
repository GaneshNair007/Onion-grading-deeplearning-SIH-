# Onion Quality & Freshness Grading — Master Plan

## 0. Project Scope (current direction)

Grading is done **per individual onion**, not per tray/batch. Primary use case is **household/consumer** — a person scans onions they own (e.g. from a kitchen or pantry) to know:
1. Current quality (damaged / rotten / sprouted / undersized)
2. **Decay factor** — an estimated remaining shelf-life ("good for ~X more days") for that specific onion
3. Which onions to use first, to cut household food waste

Two mobile-based models are being built, both with **zero external hardware** — only what's already on a stock smartphone:

| Model | Sensors used | What it adds |
|---|---|---|
| **Model 1 — Vision-Only (Lite)** | Camera only | Works on any phone, any condition, lightweight, always available |
| **Model 2 — Vision + Acoustic (Full)** | Camera + built-in speaker + built-in mic | Adds internal-defect detection (rot/hollowness invisible to the camera) for a more accurate decay estimate |

A third, separate track is the **Industry Model** — a dedicated purpose-built hardware device (not a phone, not constrained by phone sensors) aimed at procurement centers / processing lines, described in Section 4. It shares the underlying AI approach but is architecturally independent.

---

## 1. Model 1 — Vision-Only Mobile Model (Lite)

**Goal:** grade a single onion and estimate remaining shelf life using only a photo. No mic, no speaker, no extra step — works instantly, on every device.

### Pipeline
1. **Capture:** user photographs one onion (guided on-screen frame + lighting tip for consistency).
2. **Defect detection:** CNN classifier (MobileNetV3 or EfficientNet-Lite, on-device via TFLite) flags damaged / sprouted / undersized / visibly rotten from surface features (bruising, discoloration, sprout tips, skin translucency, size relative to a reference).
3. **Decay estimation (visual-only):** a regression head trained on your own longitudinal photo dataset (Section 5) predicts **estimated days remaining before the onion crosses into "use soon" / "spoiled"**, using early visual precursors (skin translucency, faint discoloration gradient, subtle softening visible as light reflection changes) — this is the same "decay trajectory" idea from earlier, just scoped to one onion instead of a batch.
4. **Output:** a simple freshness score/label + "good for ~N more days" + explanation (Grad-CAM highlight on the exact spot that lowered the score).

### Why this tier matters
- Zero friction — no extra action needed beyond a photo, so it's the version that actually gets used daily.
- Works even on low-end phones with no reliable mic isolation or weak speakers.
- This is your fallback demo if the acoustic pipeline isn't reliable yet — always have Model 1 working end-to-end first.

---

## 2. Model 2 — Vision + Acoustic Mobile Model (Full)

**Goal:** catch what Model 1 structurally cannot — internal rot or hollowness that produces no visible surface sign yet, which is exactly the kind of onion that "looked fine yesterday, was rotten today" at home.

### Pipeline
1. Run Model 1's vision pipeline first (defect flags + initial decay estimate).
2. **Acoustic test, using only the phone's own speaker and mic — no piezo, no external contact sensor:**
   - Phone speaker emits a **logarithmic chirp** (~100 Hz–8 kHz).
   - Phone mic records the response with the onion held close to / against the phone (guided on-screen: "hold the onion against the bottom of your phone").
   - Compute the transfer function via FFT: resonant peak frequency, damping/decay rate, spectral centroid.
3. **Internal-condition model:** small regressor/classifier (Random Forest, since your training set will be modest) trained on these acoustic features against real ground truth (onions you've cut open, see Section 5) — outputs an internal-defect probability and adjusts the decay estimate down if internal spoilage is detected early.
4. **Fused output:** final freshness score = vision decay estimate refined by acoustic internal-condition signal. This is the moment worth demoing live: an onion that Model 1 alone rates "fine" gets correctly downgraded once Model 2's acoustic test runs.

### Why "phone speaker + mic only" is the right constraint, not a limitation
This mirrors a real, published research method — acoustic impulse-response / reflected-signal testing has established literature for firmness and internal-quality assessment in fruit (apples, pears, watermelon hollow-heart detection), including at least one paper using essentially this exact setup (small speaker emits a signal, small mic captures the reflection, regressor estimates firmness/storage time) for tomatoes and mandarins. You're not inventing unproven physics — you're applying a validated technique to a device that already has the right components built in, with no added part.

### Honest technical challenges to design around
- **Ambient noise** (kitchen noise, TV, etc.) — use a noise-gated recording window or a quick ambient-baseline recording to subtract before the chirp.
- **Contact/positioning consistency** — solve with the guided UI step, not hardware; always test the same way (e.g., phone flat, onion pressed to the speaker/mic end).
- **Small training set** — use simple, explainable models (Random Forest over hand-engineered FFT features) rather than deep audio nets; they generalize better with limited data and are easier to justify in a demo.

---

## 3. Shared: Household Features Layer

Both models feed into a household-facing app layer, not just a one-shot scanner:

- **Personal pantry log:** each scanned onion is saved with its freshness score and predicted "use by" window.
- **"Use these first" sorting:** app surfaces onions closest to spoiling so none get wasted at the back of the pantry.
- **Freshness re-check reminders:** optional periodic nudge to rescan onions nearing their predicted decay point.
- **Food-waste tracking (nice-to-have):** simple running count of onions "saved" by using them before spoilage vs. historical household waste — gives the project a measurable consumer-impact story, not just a technical demo.

---

## 4. Industry Perspective — Dedicated Hardware Model (separate track)

This is explicitly **not** the mobile app scaled up — it's a different product for a different context (procurement centers, processing lines, exporters), where phone-sensor constraints no longer apply and purpose-built hardware makes sense.

### Concept
A standalone benchtop/inline device that automates what the mobile app does manually, at much higher throughput and with sensors that outperform a phone's stock speaker/mic/camera.

### Suggested hardware components
| Component | Purpose | Why better than phone equivalent |
|---|---|---|
| Multi-angle camera rig (or a single camera + rotating tray) | Full-surface visual inspection, no blind spots | Phone photo only sees one side per shot |
| **Piezoelectric contact transducer + contact microphone** | Acoustic excitation and pickup directly through the onion's skin, not through air | Far cleaner signal than a phone's air-coupled speaker/mic — no ambient noise contamination, much stronger resonance signal |
| NIR (near-infrared) sensor or low-cost spectral sensor *(optional, higher tier)* | Non-destructive internal-quality estimate via light absorption, a technique already used commercially for produce | Something a phone camera fundamentally cannot do (RGB-only) |
| Load cell | Precise weight-to-size ratio for density/maturity estimation | More accurate and consistent than app-based size estimation |
| Small conveyor / singulation feed + pneumatic or mechanical sorting gate | Feeds onions one at a time under the sensors and physically sorts them into Grade A / URS / Reject bins | Enables actual automated grading at line speed, not just a report — this is what turns it into an industrial product rather than a diagnostic tool |

### Software layer (shared lineage with the mobile models)
- Same core AI approach: vision defect detection + acoustic/spectral internal-condition model + the standards/rules engine (Grade A vs URS thresholds from real NAFED/BIS specs, config-driven so it updates instantly when official norms change) + decay prediction.
- Runs on an embedded compute unit (e.g. Raspberry Pi / Jetson Nano class device) instead of a phone, so it can handle continuous inference at conveyor speed.
- Central dashboard for procurement center supervisors: live throughput, aggregate Grade A/URS %, digital tamper-evident reports with QR codes, same as the mobile report generator.

### How to position this relative to the mobile models in your pitch
"We're proving the AI on a phone first — cheap, zero-capex, deployable today for households and small-scale use. The same underlying intelligence, given better sensors and automation, becomes an industrial sorting line for procurement centers and exporters." This keeps your mobile work as the credible, working core of the demo, while showing judges you understand the hardware path to real industrial deployment without pretending a phone alone can do that job.

---

## 5. Data Collection Plan (feeds Models 1 & 2)

1. Acquire 30–40 onions spanning visibly different conditions.
2. **Daily for 10–14 days**, for each onion individually:
   - Photograph (consistent lighting/background) → feeds Model 1.
   - Run the phone chirp/mic acoustic test, save raw audio + extracted features → feeds Model 2.
3. **Periodically cut open a subset** to get real ground truth on internal rot/hollowness — this is what makes the acoustic model and the decay-estimation regressor trainable and credible, rather than guessed.
4. One dataset, tracked per individual onion over time, feeds: the defect classifier, the acoustic internal-condition model, and the decay/shelf-life regressor for both models.

---

## 6. Build Priority

1. **Model 1 end-to-end working first** (camera → defect flags → decay estimate). This must work reliably — it's your safety net.
2. **Model 2 acoustic pipeline** as the demo's wow-moment, even if accuracy is proof-of-concept level — the live contrast ("camera says fine, acoustic test catches the problem") is what's memorable.
3. **Household layer** (pantry log, "use first" sorting) — relatively simple UI/state work, high narrative value for the consumer-use-case framing.
4. **Industry hardware section** stays a pitch-deck/roadmap slide, not something you build during the hackathon — present it as the scaling vision, backed by the fact that your mobile AI core is architecture-compatible with it.

---

## 7. Acoustic Architecture — Detailed Implementation Paths

This section is an addition to the existing architecture and does **not replace Models 1 or 2** above. Model 2 remains the primary phone-only acoustic concept. Architecture B is an optional hardware-assisted research/prototype path for cases where the phone-only acoustic signal is not sufficiently clean or repeatable.

### Architecture A — Mobile-Only Acoustic Model

**Constraint:** zero external hardware.

The smartphone itself provides all sensing and processing:

- Built-in speaker
- Built-in microphone
- Camera
- Flash
- On-device processing

#### A1. Primary acoustic method — controlled tapping

```text
USER
  │
  │ standardized tap
  ▼
ONION
  │
  │ airborne acoustic response
  ▼
PHONE MICROPHONE
  │
  ▼
AUDIO BUFFER
  │
  ▼
NOISE / BASELINE PROCESSING
  │
  ▼
FFT / STFT
  │
  ▼
ACOUSTIC FEATURES
  │
  ▼
ACOUSTIC MODEL
  │
  ▼
INTERNAL-CONDITION SCORE
```

The app should guide the user so that:

- The onion is held/placed consistently.
- The phone is kept at a defined approximate distance.
- The tap occurs at a defined location.
- Multiple taps are recorded.
- Poor-quality or inconsistent recordings trigger a retest.

The first objective is to determine whether the microphone signal contains repeatable information about internal condition.

#### A2. Optional phone-speaker excitation

The phone speaker can also emit a controlled stimulus, such as a logarithmic chirp, while the microphone records the response.

```text
PHONE SPEAKER
     │
     ▼
CONTROLLED CHIRP
     │
     ▼
    ONION
     │
     ▼
PHONE MICROPHONE
     │
     ▼
FFT / TRANSFER-FUNCTION ANALYSIS
     │
     ▼
ACOUSTIC FEATURES
```

This is attractive because it requires no extra hardware, but it is more sensitive to:

- Direct speaker-to-microphone leakage
- Room reflections
- Ambient noise
- Phone-to-onion positioning

Therefore the mobile-only method should be experimentally compared rather than assuming the speaker-based method will outperform tapping.

#### A3. Mobile-only processing

```text
Raw audio
   ↓
Ambient baseline / noise estimation
   ↓
Filtering
   ↓
Windowing
   ↓
FFT / STFT
   ↓
Spectrogram
   ↓
Feature extraction
   ↓
Random Forest / other lightweight model
   ↓
Internal-defect probability
```

Potential features include:

- Peak amplitude
- RMS amplitude
- Decay time
- Dominant frequency
- Spectral centroid
- Spectral bandwidth
- Spectral entropy
- Energy in frequency bands
- Frequency decay characteristics

Architecture A remains the **zero-cost fallback and deployable phone-only version**.

---

### Architecture B — Piezo + USB Audio ADC

**Purpose:** create a higher-quality research/prototype acoustic path without turning the main product into a hardware-dependent system.

```text
                         ONION
                           │
                 mechanical vibration
                           ▼
                  ┌────────────────┐
                  │ PIEZO CONTACT  │
                  │    SENSOR      │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ HIGH-Z PREAMP  │
                  │ + GAIN         │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ ANALOG FILTER  │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ USB AUDIO ADC  │
                  │ 16-bit         │
                  │ 44.1/48 kHz    │
                  └───────┬────────┘
                          │
                        USB-C
                          │
                          ▼
                  ┌────────────────┐
                  │ ANDROID PHONE  │
                  │    ONION-Q     │
                  └────────────────┘
```

#### B1. Why this architecture is different

Architecture A measures airborne sound through the phone microphone.

Architecture B measures **mechanically coupled vibration** through a piezoelectric contact sensor.

The intended benefit is:

- Better mechanical coupling
- Less dependence on room acoustics
- Higher-bandwidth waveform capture
- More controlled signal acquisition
- Potentially better repeatability

It must still be validated experimentally; the hardware should not be assumed to improve classification until testing demonstrates that it does.

#### B2. Hardware components

| Component | Purpose |
|---|---|
| 27 mm piezoelectric disc/contact pickup | Mechanical vibration sensing |
| High-impedance preamplifier | Buffer and amplify piezo output |
| Analog filter | Control unwanted bandwidth/noise |
| USB Audio ADC/interface | Convert analog waveform to digital audio |
| USB-C/OTG cable | Connect acquisition device to Android |
| Breadboard | Prototype signal-conditioning circuit |
| Resistors/capacitors | Bias, gain and filtering |
| Standardized striker | Repeatable mechanical excitation |
| Sensor holder/mount | Consistent piezo contact |
| Optional actuator/solenoid | Automated repeatable tapping |

#### B3. ADC requirements

The USB Audio ADC should provide:

- Actual ADC/audio input
- USB Audio Class operation
- Android/USB OTG compatibility
- 44.1 kHz or 48 kHz sampling
- 16-bit or 24-bit conversion

A 48 kHz sampling rate gives a theoretical Nyquist frequency of:

\[
f_N = 24\,kHz
\]

This provides substantially more bandwidth for acoustic experimentation than a low-speed general-purpose ADC.

A dedicated audio ADC/interface is therefore preferred for Architecture B.

#### B4. Why ADS1115 is not the primary Architecture B ADC

ADS1115 is useful as a low-cost electronics experiment, but it is not the preferred acquisition device for this acoustic architecture because its maximum data rate is 860 samples/s.

At 860 samples/s:

\[
f_N = 430\,Hz
\]

That restricts the frequency range that can be studied.

If an ADS1115 is used during early electronics experimentation, its architecture would be:

```text
PIEZO
  ↓
PREAMP
  ↓
ADS1115
  ↓ I²C
ESP32
  ↓
USB
  ↓
PHONE
```

This can be useful for low-frequency/mechanical-response experiments, but the main acoustic research path should use a USB audio ADC when higher-frequency waveform information is required.

---

### Architecture B5. Signal-processing pipeline

```text
PIEZO
  ↓
PREAMP
  ↓
USB AUDIO ADC
  ↓
USB-C
  ↓
ANDROID
  ↓
AUDIO BUFFER
  ↓
DC / NOISE PROCESSING
  ↓
DIGITAL FILTER
  ↓
FFT / STFT
  ↓
SPECTROGRAM
  ↓
FEATURE EXTRACTION
  ↓
ACOUSTIC ML
```

The model can initially use classical machine learning such as:

- Random Forest
- XGBoost
- SVM
- Logistic Regression

A deep neural network should only be considered if the dataset becomes large enough to justify it.

---

### Architecture B6. Standardized excitation

The sensor itself is only one part of the measurement problem. The mechanical excitation must also be repeatable.

A simple standardized striker can be used:

```text
       SPRING
         │
         ▼
       ┌───┐
       │ ● │
       └─┬─┘
         │
         ▼
        ONION
         │
       PIEZO
```

The experiment should control, as far as practical:

- Impact location
- Impact force
- Sensor location
- Sensor contact pressure
- Onion orientation
- Number of measurements

An automated actuator can be considered later if manual excitation proves too variable.

---

### Architecture B7. Recommended acoustic experiment

Before integrating acoustic information into grading:

1. Collect onions covering relevant conditions.
2. Record several measurements per onion.
3. Maintain an individual onion ID.
4. Record images and acoustic signals together.
5. Establish ground truth using the project's defined inspection/validation process.
6. Measure repeatability.
7. Compare acoustic features between conditions.
8. Train a simple baseline model.
9. Test on held-out onions.
10. Compare acoustic-only, vision-only and fused performance.

The critical experiment is:

```text
VISION ONLY
     vs
ACOUSTIC ONLY
     vs
VISION + ACOUSTIC
```

The purpose is to establish whether acoustic sensing adds information beyond the camera.

---

### Architecture B8. Confidence-based use

The acoustic test should ideally be triggered selectively rather than for every onion.

```text
VISION
  │
  ├── HIGH CONFIDENCE ─────► normal result
  │
  └── UNCERTAIN
          │
          ▼
    ACOUSTIC TEST
          │
          ▼
      EVIDENCE FUSION
          │
     ┌────┴────┐
     ▼         ▼
 CONFIDENT   UNCERTAIN
     │         │
     ▼         ▼
 RESULT     HUMAN REVIEW
```

This keeps the system fast while making acoustic sensing a meaningful secondary verification method.

---

### Architecture A vs Architecture B

| Feature | Architecture A — Mobile Only | Architecture B — Piezo + USB Audio ADC |
|---|---|---|
| External hardware | None | Required |
| Cost | ₹0 additional | Low |
| Sensor | Built-in microphone | Piezo contact sensor |
| Excitation | Tap / phone speaker experiment | Standardized mechanical tap |
| Signal | Airborne acoustic | Mechanically coupled vibration |
| Bandwidth | Phone-dependent | Typically 44.1/48 kHz audio acquisition |
| Environmental noise sensitivity | Higher | Potentially lower |
| Setup | Very simple | Moderate |
| Main purpose | Zero-cost deployable model | Research/prototype enhancement |
| Recommended role | Core mobile option | Optional advanced acoustic path |

---

## 8. Project Prospects — Questions for the Team

These questions are intended to be answered by the team before committing to the final implementation. They focus on feasibility, differentiation, validation, deployment and judging potential.

### 1. What is our strongest differentiator?

If another team builds a phone camera that detects rotten/sprouted onions, **what specific capability makes ONION-Q substantially different?**

### 2. Can we actually prove that acoustic sensing adds value?

What experiment will demonstrate that:

```text
Vision + Acoustic > Vision only
```

rather than simply showing that the acoustic feature exists?

### 3. What is our primary target user?

Are we ultimately optimizing for:

- Household consumers
- Farmers
- Procurement centers
- Traders
- Exporters
- Processing facilities

The answer affects the product, dataset and success metrics.

### 4. How will we establish ground truth?

How will we determine whether an onion is genuinely:

- Internally rotten
- Hollow/abnormal
- Firm
- Soft
- Near spoilage

rather than relying only on visual judgement?

### 5. How realistic is our shelf-life prediction?

What data will allow us to defend a statement such as:

> "Good for approximately X more days"

and how will we communicate uncertainty instead of presenting an unsupported exact number?

### 6. How will the system handle different phones?

Camera, microphone, speaker, processing and sensor characteristics vary considerably between devices.

Do we:

- Calibrate per device?
- Normalize signals?
- Limit supported devices?
- Train across multiple phone models?

### 7. How will we make the acoustic test repeatable?

What will control:

- Tap force
- Tap location
- Onion position
- Phone position
- Sensor contact
- Background noise

and what repeatability metric will we report?

### 8. What happens when the AI is uncertain?

Will ONION-Q:

- Ask for another image?
- Ask for an acoustic test?
- Request a manual inspection?
- Produce an "uncertain" result?

The team should define this before designing the final UI.

### 9. What can we realistically complete for the competition?

Which features are:

**Must-have**

**Should-have**

**Demo differentiator**

**Future roadmap**

so that the team does not spread development effort across too many features?

### 10. What evidence will convince a judge that the project works?

What will we demonstrate quantitatively?

Possible metrics include:

- Defect detection performance
- Shelf-life prediction error
- Vision vs multimodal improvement
- Acoustic repeatability
- Manual-review reduction
- Inspection time
- Food-waste reduction
- User/inspector agreement

The team should agree on the **3–5 metrics that define success** before final development.

---

## 9. Recommended Decision Gate

Before committing significant development time to Architecture B:

```text
PHONE-ONLY ACOUSTIC EXPERIMENT
             ↓
      Does signal show
       useful patterns?
             │
       ┌─────┴─────┐
       ▼           ▼
      YES           NO
       │             │
       ▼             ▼
PIEZO + USB ADC   Keep acoustic
       │          as experimental/
       ▼          optional feature
Does it improve
repeatability?
       │
   ┌───┴───┐
   ▼       ▼
  YES      NO
   │        │
   ▼        ▼
Integrate  Reassess/
into fusion remove
```

The final project should only make acoustic sensing part of the grading decision if the team has experimental evidence that it improves the system.

---

## 10. Final Architecture Direction

The current recommended direction is:

### Model 1

```text
CAMERA
  ↓
VISION AI
  ↓
VISIBLE QUALITY
  ↓
DECAY ESTIMATE
```

### Model 2 — Architecture A

```text
CAMERA
  +
PHONE MIC/SPEAKER
  ↓
VISION + MOBILE ACOUSTIC
  ↓
FUSED DECAY ESTIMATE
```

### Model 2 — Architecture B

```text
CAMERA
  +
PIEZO
  ↓
PREAMP
  ↓
USB AUDIO ADC
  ↓
USB-C
  ↓
PHONE
  ↓
VISION + HIGH-BANDWIDTH ACOUSTIC
  ↓
FUSED RESULT
```

Architecture B should remain an **optional advanced prototype path**, while Architecture A preserves the zero-hardware product vision already established in the master plan.

