# AI-Based Onion Quality Grading
## Frontend Design Specification — Home + About

> **Design direction:** Lockheed Martin-inspired industrial technology aesthetic  
> **Product identity:** AI + Computer Vision + Agricultural Procurement  
> **Primary feeling:** Precision · Trust · Engineering · Transparency · Intelligence

---

# 1. Design Philosophy

The website should **not look like a normal agriculture website**.

Avoid:
- Generic green agriculture templates
- Cartoon vegetables
- Stock photos of farmers
- Excessive rounded cards
- Bright green/yellow agricultural palettes
- "AI startup" purple gradients
- Overly playful animations

Instead, position the project as:

> **A precision-engineered AI inspection platform for onion procurement.**

The visual language should communicate:

**Industrial technology + computer vision + aerospace-grade precision + agricultural intelligence.**

The website should feel like a company that could be presenting its technology to:
- Government procurement departments
- Agricultural agencies
- Large procurement centres
- Engineering evaluators
- Hackathon judges
- Enterprise customers

---

# 2. Visual Inspiration

Use the **design principles** of sites such as Lockheed Martin:

- Dark navy backgrounds
- Large cinematic hero section
- Strong geometric typography
- Thin technical lines
- Grid overlays
- High-contrast white typography
- Blue/cyan technology accents
- Large photography
- Full-width sections
- Structured information hierarchy
- Subtle motion
- Technical data visualisation

Do **NOT** directly copy Lockheed Martin's:
- Logo
- Branding
- Exact layouts
- Proprietary graphics
- Exact typography
- Exact visual assets

Create an original identity around onion inspection and AI.

---

# 3. Brand Identity

## Suggested product name

Use the actual project/product name once decided.

Temporary name:

**ONION VISION**

Alternative styling:

**ONION//VISION**

or

**OVISION**

The branding should feel technological rather than agricultural.

Example:

```text
ONION
VISION
AI QUALITY INTELLIGENCE
```

---

# 4. Colour System

## Primary

```text
Deep Navy       #06111F
Midnight Blue   #091A2A
Technical Blue  #0B4F71
Electric Cyan   #27C7E8
White           #F4F7FA
Soft White      #DCE5EA
```

## Supporting

```text
Muted Blue      #557080
Border          rgba(255,255,255,0.12)
Panel           rgba(255,255,255,0.045)
Success         #35D07F
Warning         #F2B84B
Danger          #FF5D5D
```

Do not use bright green as the dominant brand colour.

Agriculture is represented through the **content**, while technology is represented through the **visual identity**.

---

# 5. Typography

Use a modern technical sans-serif.

Preferred:

```text
Inter
```

Alternative:

```text
Space Grotesk
IBM Plex Sans
Manrope
```

Use:

### Hero heading

Large:

```text
72–96px desktop
48–60px tablet
38–46px mobile
```

Weight:

```text
600–700
```

### Section headings

```text
42–56px
```

### Body

```text
16–19px
```

### Technical labels

Use:

```text
11–13px
```

with:

```text
letter-spacing: 0.12em
text-transform: uppercase
```

Example:

```text
AI QUALITY INTELLIGENCE
COMPUTER VISION SYSTEM
PROCUREMENT TECHNOLOGY
```

---

# 6. Global Layout

Use a wide desktop layout.

```text
┌─────────────────────────────────────────────────────────┐
│ NAVIGATION                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                  HERO                                   │
│                                                         │
│          LARGE HEADLINE                                 │
│          DESCRIPTION                                    │
│          CTA                                           │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                  TECHNOLOGY STRIP                       │
├─────────────────────────────────────────────────────────┤
│                  PLATFORM                               │
├─────────────────────────────────────────────────────────┤
│                  HOW IT WORKS                           │
├─────────────────────────────────────────────────────────┤
│                  DATA / INTELLIGENCE                    │
├─────────────────────────────────────────────────────────┤
│                  ABOUT                                  │
├─────────────────────────────────────────────────────────┤
│                  FOOTER                                 │
└─────────────────────────────────────────────────────────┘
```

Content should generally occupy:

```text
max-width: 1400px
```

with:

```text
padding: 24px → 80px
```

depending on viewport.

---

# 7. Navigation

The navigation should be minimal and premium.

### Desktop

```text
┌─────────────────────────────────────────────────────────────┐
│ ONION//VISION      PLATFORM   TECHNOLOGY   ABOUT   CONTACT │
│                                             [OPEN APP →]   │
└─────────────────────────────────────────────────────────────┘
```

Navigation background:

```text
transparent
```

Initially.

On scroll:

```text
rgba(6,17,31,0.88)
backdrop-filter: blur(16px)
```

Add a very thin bottom border.

---

# 8. HOME PAGE

# 8.1 Hero Section

The hero is the most important part of the website.

Height:

```text
85–100vh
```

Background should be a cinematic image/video showing:

- Onion procurement
- Onion inspection
- Tray of onions
- Close-up of onion surface
- Computer vision detection
- Industrial/agricultural facility

The image should have a dark navy overlay.

---

## Hero layout

Left:

```text
PRECISION AGRICULTURE
AI QUALITY INTELLIGENCE

See every onion.
Measure every decision.

AI-powered onion quality grading
for transparent and consistent
procurement.
```

CTA:

```text
[ EXPLORE THE PLATFORM ]
[ VIEW HOW IT WORKS ]
```

Right side:

Show a futuristic computer-vision interface.

Example:

```text
┌──────────────────────────────┐
│ LIVE INSPECTION              │
│                              │
│   ◯ Onion 01                 │
│      GRADE A                 │
│      57.2 mm                 │
│                              │
│   ◯ Onion 02                 │
│      URS                     │
│      38.7 mm                 │
│                              │
│   ◯ Onion 03                 │
│      REVIEW                  │
│                              │
│ AI CONFIDENCE     96.4%      │
└──────────────────────────────┘
```

This should look like a real inspection interface.

---

# 8.2 Hero Technical Overlay

Add subtle technical elements:

```text
SYSTEM STATUS              ONLINE
VISION ENGINE              ACTIVE
CALIBRATION                READY
POLICY                     ACTIVE
```

Use tiny cyan indicators.

Also add:

```text
01
AI INSPECTION SYSTEM
```

in the corner.

This creates the aerospace/engineering feel.

---

# 8.3 Hero Animation

On page load:

1. Background fades in.
2. Technical grid appears.
3. Headline slides upward.
4. Inspection boxes appear sequentially.
5. Small system indicators activate.
6. CTA becomes visible.

Keep animations subtle.

No excessive bouncing.

---

# 9. Technology Strip

Immediately below the hero.

Dark slightly lighter section.

Example:

```text
COMPUTER VISION       SIZE CALIBRATION       RULE ENGINE
AI DETECTION          DIGITAL EVIDENCE       AUDIT TRAIL
```

Use thin vertical separators.

---

# 10. "THE PROBLEM" SECTION

Heading:

```text
PROCUREMENT SHOULD NOT
DEPEND ON OPINION.
```

Supporting text:

```text
Manual grading can produce inconsistent decisions,
limited evidence, and disputes between procurement
centres and suppliers.
```

Then show three large panels.

### 01

```text
INCONSISTENCY

Different inspectors can reach
different conclusions on the
same batch.
```

### 02

```text
NO EVIDENCE TRAIL

Manual grading does not naturally
produce a detailed, reviewable
record.
```

### 03

```text
UNEXPLAINED DECISIONS

Farmers and suppliers may not have
a transparent explanation for why
a batch was downgraded.
```

These directly reflect the project's problem definition.

---

# 11. "THE SOLUTION" SECTION

Large statement:

```text
FROM VISUAL INSPECTION
TO DIGITAL EVIDENCE.
```

Then introduce the system.

```text
Our platform combines computer vision,
calibrated size measurement and a
configurable grading rule engine to
standardise onion procurement decisions.
```

Visual:

A large onion image with detection boxes.

Example:

```text
             ┌─────────────┐
             │   ONION 01  │
             │   GRADE A   │
             │   58.2 mm   │
             └─────────────┘

      ┌─────────────────────────┐
      │        ONION            │
      │                         │
      │    computer vision      │
      │       boundary          │
      └─────────────────────────┘
```

---

# 12. Platform Architecture Section

Title:

```text
ONE CAPTURE.
MULTIPLE INTELLIGENCE LAYERS.
```

Show a horizontal pipeline:

```text
CAPTURE
   ↓
VISION
   ↓
CALIBRATION
   ↓
RULE ENGINE
   ↓
BATCH ANALYSIS
   ↓
DIGITAL REPORT
```

Each stage should be an interactive node.

When hovering over a node, show its description.

Example:

### VISION

```text
Detects every individual onion
and identifies visible defects.
```

### CALIBRATION

```text
Converts image measurements
into estimated real-world diameter.
```

### RULE ENGINE

```text
Applies the active procurement
policy consistently.
```

The master plan explicitly defines this pipeline.

---

# 13. "SEE THE INTELLIGENCE" Section

This should be visually impressive.

Use a large image of a tray of onions.

Overlay detection boxes.

Example:

```text
 ┌─────────────────────────────────────┐
 │                                     │
 │   ┌────────┐       ┌──────────┐     │
 │   │ A 57mm │       │ URS 39mm │     │
 │   └────────┘       └──────────┘     │
 │                                     │
 │          ┌────────────┐             │
 │          │ REVIEW     │             │
 │          │ LOW CONF.  │             │
 │          └────────────┘             │
 │                                     │
 └─────────────────────────────────────┘
```

Add a side information panel:

```text
BATCH ANALYSIS

TOTAL DETECTED
48

GRADE A
31

URS
9

REVIEW
4

REJECTED
4
```

Use animated counters.

---

# 14. Batch Intelligence Section

Heading:

```text
FROM INDIVIDUAL ONIONS
TO BATCH-LEVEL DECISIONS.
```

Show a dashboard-style visualization.

```text
GRADE A              64.6%
████████████████████████████

GRADE URS            18.7%
███████

MANUAL REVIEW         8.3%
███

REJECTED              8.3%
███
```

Important:

Do not use fake real-world data in the production website.

If this is a demo visualization, label it:

```text
DEMO DATA
```

---

# 15. Transparency Section

This is one of the most important sections because transparency is central to the project.

Large statement:

```text
EVERY DECISION
LEAVES A TRACE.
```

Show a digital report mockup.

Report contains:

```text
REPORT ID
BATCH ID
FARMER / SUPPLIER
PROCUREMENT CENTRE
OFFICER
DATE / TIME
POLICY VERSION

GRADE A
64.6%

URS
18.7%

REJECTED
8.3%

MANUAL REVIEW
8.3%

AI CONFIDENCE
96.4%
```

Then:

```text
[ VIEW SAMPLE REPORT ]
```

The actual master plan specifies annotated images, reason codes, policy version, QR code and audit trail as core report components.

---

# 16. Acoustic Intelligence Section

This is the "wow" section.

Use a darker section.

Heading:

```text
THE CAMERA SEES THE SURFACE.
WE GO FURTHER.
```

Description:

```text
Our enhanced inspection layer explores acoustic
signals from the phone's built-in speaker and
microphone to identify potential hidden defects
that may not be visible externally.
```

Visual:

```text
PHONE
  │
  │ acoustic signal
  ▼
~ ~ ~ ~ ~ ~ ~
     ONION
~ ~ ~ ~ ~ ~ ~
  │
  ▼
SIGNAL ANALYSIS
  │
  ▼
HIDDEN-DEFECT SCREEN
```

Add:

```text
ENHANCED MODE
CAMERA + AUDIO
```

Important:

Clearly mark this as:

```text
ENHANCED / RESEARCH MODULE
```

because the master plan treats acoustic inspection as a Tier 2 differentiator rather than the core MVP.

---

# 17. About Preview

Home page should contain a short About section.

Heading:

```text
ENGINEERED FOR
CONSISTENT PROCUREMENT.
```

Text:

```text
We are building a mobile-first AI inspection
system that turns onion quality assessment into
a measurable, explainable and auditable process.
```

CTA:

```text
[ OUR APPROACH → ]
```

---

# 18. HOME PAGE FINAL SECTION

Large cinematic section.

Text:

```text
A BETTER WAY
TO GRADE.
```

Small text:

```text
AI • COMPUTER VISION • CALIBRATION • EVIDENCE
```

CTA:

```text
[ EXPLORE THE PLATFORM ]
```

Background:

Close-up macro onion texture / procurement centre.

Dark overlay.

---

# 19. ABOUT PAGE

The About page should feel more like an **engineering mission page** than a conventional "Our Team" page.

---

# 20. About Hero

Full-screen hero.

```text
ABOUT THE SYSTEM

ENGINEERING
TRANSPARENCY
INTO PROCUREMENT.
```

Supporting text:

```text
A computer-vision driven approach to
standardising onion quality assessment
at procurement centres.
```

---

# 21. Our Mission

Heading:

```text
THE MISSION
```

Large text:

```text
MAKE QUALITY
MEASURABLE.
```

Body:

```text
The goal is not simply to classify onions.

The goal is to create a consistent,
evidence-backed process in which every
grading decision can be understood,
reviewed and audited.
```

---

# 22. Why We Built It

Three-column section.

```text
01
CONSISTENCY

Apply the same active grading
policy across procurement centres.


02
TRANSPARENCY

Show the evidence and reason
behind every decision.


03
ACCOUNTABILITY

Create a digital record that
can be reviewed later.
```

These three themes should be visually dominant throughout the site.

---

# 23. How It Works — About Version

Create a large vertical timeline.

```text
01
CAPTURE
↓
02
DETECT
↓
03
MEASURE
↓
04
CLASSIFY
↓
05
ANALYSE
↓
06
REPORT
```

For each:

### CAPTURE

```text
The officer photographs onions arranged
in a single layer with a calibration reference.
```

### DETECT

```text
Computer vision identifies individual onions
and visible defects.
```

### MEASURE

```text
The calibration reference allows image
measurements to be converted into estimated
diameter in millimetres.
```

### CLASSIFY

```text
The configurable rule engine applies the
active Grade A / URS policy.
```

### ANALYSE

```text
The system calculates batch-level percentages.
```

### REPORT

```text
The application generates an evidence-backed
digital report.
```

This follows the documented MVP workflow.

---

# 24. Technology Stack

Use a technical grid.

```text
COMPUTER VISION
YOLO / SEGMENTATION

MOBILE
FLUTTER / REACT NATIVE

BACKEND
FASTAPI / FLASK / NODE.JS

DATABASE
FIREBASE / SUPABASE / POSTGRESQL

REPORTING
PDF / HTML + QR
```

Do not make this section look like a generic developer portfolio.

Make it look like an engineering system specification.

---

# 25. Core vs Enhanced Architecture

Create a visual split.

## TIER 01

```text
CORE INSPECTION

CAMERA
↓
VISION
↓
SIZE CALIBRATION
↓
RULE ENGINE
↓
BATCH REPORT
```

Badge:

```text
MVP
```

---

## TIER 02

```text
ENHANCED INSPECTION

CAMERA
+
SPEAKER
+
MICROPHONE
↓
ACOUSTIC ANALYSIS
↓
HIDDEN DEFECT SCREEN
```

Badge:

```text
ENHANCED
```

The two-tier architecture is explicitly defined in the master plan.

---

# 26. Engineering Principles

About page section:

```text
DESIGNED AROUND FIVE PRINCIPLES
```

### 01 — MEASURABLE

```text
Size is estimated using a physical
calibration reference rather than
visual approximation.
```

### 02 — CONFIGURABLE

```text
Grading thresholds belong to an
active procurement policy.
```

### 03 — EXPLAINABLE

```text
Each result is associated with
a reason code.
```

### 04 — AUDITABLE

```text
Reports preserve the evidence
behind the decision.
```

### 05 — HUMAN-IN-THE-LOOP

```text
Uncertain cases can be sent
for manual review or override.
```

The master plan specifically requires manual review for missing calibration or low-confidence cases and records human overrides in the report.

---

# 27. Future Vision

Do not present future features as already implemented.

Heading:

```text
WHERE THIS CAN GO
```

Create a horizontal roadmap:

```text
TODAY
AI MOBILE INSPECTION
        │
        ▼
NEXT
OFFLINE INFERENCE
QR TRACEABILITY
GPS
        │
        ▼
FUTURE
INDUSTRIAL VISION SYSTEM
        │
        ▼
SCALE
FIXED CAMERA
CONVEYOR
AUTOMATED SORTING
```

Clearly label future concepts.

The master plan identifies industrial hardware, digital scale integration, GPS, QR traceability, multilingual UI and dashboards as future/if-time-remains directions.

---

# 28. Footer

Large footer.

```text
ONION//VISION

AI QUALITY INTELLIGENCE
FOR PROCUREMENT

────────────────────────────────

PLATFORM
TECHNOLOGY
ABOUT
CONTACT

────────────────────────────────

SIH26031
AI-BASED ONION QUALITY GRADING

© 2026
```

Add a tiny technical status:

```text
SYSTEM STATUS ● ONLINE
```

---

# 29. Animation System

Animations should communicate technology.

## Page transitions

```text
opacity: 0 → 1
transform: translateY(20px) → 0
```

Duration:

```text
500–800ms
```

---

## Hover effects

Buttons:

```text
border → cyan
background → subtle cyan
arrow → moves 4–8px
```

Cards:

```text
translateY(-4px)
border becomes slightly brighter
```

---

## Technical scanning effect

For AI visualisations:

```text
vertical scanning line
```

moving slowly over an onion image.

Do not run continuously on every element.

---

# 30. Background System

Use three layers:

```text
Layer 1
Dark navy background

Layer 2
Subtle technical grid

Layer 3
Large photographic / AI visual
```

Technical grid:

```text
background-image:
linear-gradient(...)
```

Opacity:

```text
0.03–0.06
```

It should barely be visible.

---

# 31. Image Treatment

Photography should have:

```text
high contrast
dark shadows
cool blue tone
cinematic crop
```

Avoid bright stock-photo aesthetics.

Good subjects:

- Onion trays
- Procurement centres
- Close-up onion skins
- Inspection officers
- Smartphone camera
- Agricultural warehouses
- Computer vision overlays
- Industrial sorting environments

When using photos, apply a dark gradient overlay so typography remains readable.

---

# 32. UI Components

Build reusable components:

```text
Navbar
Hero
TechnicalLabel
PrimaryButton
SecondaryButton
SectionHeading
StatCard
TechnologyCard
InspectionOverlay
PipelineNode
BatchDashboard
ReportPreview
Timeline
Roadmap
Footer
```

---

# 33. Button Design

Primary:

```text
┌──────────────────────────────┐
│ EXPLORE THE PLATFORM     →   │
└──────────────────────────────┘
```

Transparent/outlined secondary:

```text
┌──────────────────────────────┐
│ VIEW HOW IT WORKS        →   │
└──────────────────────────────┘
```

Avoid pill-shaped buttons.

Use slightly squared corners:

```text
border-radius: 2–4px
```

This helps maintain the industrial aesthetic.

---

# 34. Cards

Avoid:

```text
border-radius: 24px
huge shadows
glassmorphism everywhere
```

Prefer:

```text
border: 1px solid rgba(...)
background: rgba(255,255,255,0.03)
border-radius: 2–6px
```

Cards should feel like technical panels.

---

# 35. Responsive Behaviour

## Desktop

Use:

```text
12-column grid
```

Hero:

```text
7 columns text
5 columns visual
```

---

## Tablet

Use:

```text
6-column grid
```

---

## Mobile

Everything becomes a single column.

Hero:

```text
headline
↓
description
↓
CTA
↓
inspection visual
```

Navigation becomes:

```text
LOGO                         ☰
```

Do not simply shrink the desktop layout.

Recompose it for mobile.

---

# 36. Mobile Hero

Example:

```text
PRECISION
AGRICULTURE

SEE EVERY
ONION.

Measure.
Classify.
Explain.

[ EXPLORE → ]

┌─────────────────────┐
│ AI INSPECTION       │
│                     │
│ ● GRADE A           │
│ ● URS               │
│ ● REVIEW            │
│                     │
│ CONFIDENCE 96.4%    │
└─────────────────────┘
```

---

# 37. Overall UX Rule

Every major section should answer one question.

```text
HERO
What is this?

PROBLEM
Why does it matter?

SOLUTION
What are we building?

PLATFORM
How does it work?

INTELLIGENCE
What does the AI actually see?

TRANSPARENCY
Why should the result be trusted?

ACOUSTIC
What makes this different?

ABOUT
Why are we building it?

ROADMAP
Where can it go?
```

---

# 38. Critical Product Accuracy Rules

The frontend must never visually imply that the system does something that the project does not actually support.

### Do not claim:

```text
100% accuracy
```

### Do not show:

```text
REAL-TIME AI
```

unless the implemented system actually performs real-time inference.

### Do not present:

```text
Acoustic detection
```

as a completed production capability if it is still the enhanced prototype.

### Do not describe:

```text
URS = Reject
```

URS means:

```text
Under Relaxed Specification
```

and is an accepted relaxed-quality category when enabled by the active procurement policy.

---

# 39. Website Personality

The website should feel:

```text
85% Engineering
10% Agriculture
5% AI Futurism
```

NOT:

```text
50% Agriculture
30% AI startup
20% Engineering
```

The core message is:

> **We are engineering a reliable inspection system for agricultural procurement.**

---

# 40. Final Visual Direction

The final site should feel like:

```text
LOCKHEED MARTIN
        +
PALANTIR
        +
INDUSTRIAL COMPUTER VISION
        +
PRECISION AGRICULTURE
```

But with an entirely original visual identity.

The user should land on the homepage and immediately think:

> **"This looks like serious technology."**

Then after reading the content:

> **"I understand exactly what this system does."**

And after seeing the inspection interface:

> **"I can see how the technology actually works."**