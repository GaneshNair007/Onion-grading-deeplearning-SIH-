Onion Acoustic Intelligence — Website Master Specification
SIH26031 | Front-End / UX / Visual-System Handoff
For Claude verification → Google Antigravity implementation

0. PURPOSE OF THIS DOCUMENT
This document is the website-specific master specification derived from the project's master plan and the requested visual direction.
The website must not look like a conventional agriculture, farming, onion, or generic AI website.
It should feel like a precision sensing and instrumentation platform whose application happens to be onion procurement and grading.
The visual and interaction language should combine:
Apple-style glassmorphism
Sonar and radar interfaces
Aerospace instrumentation
Acoustic signal analysis
Scientific visualization
Modern industrial sensing
Minimal editorial web design
The emotional impression should be:
"This is an advanced sensing instrument, not an agricultural website."
The central technological identity is:
ACOUSTIC INTELLIGENCE
The core message is:
Hear what the eye can't see.
The website should communicate that computer vision is the required procurement-grading foundation, while acoustic hidden-defect screening is the project's chosen technical differentiator.
The website must therefore make the acoustic system visually dominant without falsely presenting the acoustic module as the entire MVP.

1. SOURCE-OF-TRUTH PROJECT CONTEXT
The project master plan defines the problem as inconsistent manual onion grading at procurement centres, creating inconsistency, disputes, and a lack of an evidence trail.
The required MVP is a mobile procurement-officer tool that:
Detects and grades individual onions in a photographed tray.
Measures bulb size using an in-frame calibration reference.
Applies a configurable Grade A / URS rule engine.
Generates an evidence-backed digital report.
Provides reason codes, policy versioning, auditability, and human review.
The acoustic system is a Tier-2 enhancement/differentiator:
Phone speaker emits a logarithmic chirp approximately 100 Hz–8 kHz.
Phone microphone records the response.
FFT extracts signal characteristics such as resonant peak frequency, damping/decay rate, and spectral centroid.
A small Random Forest / gradient-boosted model can flag likely hidden internal defects.
The acoustic result may trigger Manual Review or alter confidence rather than replacing the core grading workflow.
The master plan explicitly positions acoustic screening as the chosen differentiator because internal rot/hollowness cannot be directly observed by the camera.
Do not redesign the project as an "acoustic-only onion classifier."
The correct architecture is:
Vision-based procurement grading + configurable rules + evidence report + acoustic hidden-defect screening
Source: project master plan, sections 2–4 and 10.

2. PRIMARY WEBSITE OBJECTIVE
The website should accomplish five things immediately:
2.1 Explain the problem
Manual grading can produce inconsistent decisions and weak evidence trails.
2.2 Explain the required solution
Phone-based computer vision identifies individual onions, visible defects, and calibrated size, then applies configurable procurement rules.
2.3 Explain the differentiator
Acoustic sensing attempts to detect internal conditions that a camera cannot see.
2.4 Demonstrate technical depth
Show that the project involves:
acoustic excitation
microphone capture
signal processing
Fourier/FFT analysis
resonance
spectral features
computer vision
calibration
configurable rule engines
confidence scoring
digital reporting
audit trails
future ML models
2.5 Communicate scalability
Show a credible path from:
phone prototype → procurement-centre workflow → dedicated industrial sensing → high-throughput grading
The website should make the project look technically ambitious while remaining honest about what is currently built, what is prototype-level, and what is future scope.

3. WEBSITE INFORMATION ARCHITECTURE
Exactly three primary navigation tabs:
HOME
ABOUT
PROTOTYPE
Optional CTA buttons may route into these three sections, but do not create unnecessary top-level pages.
Suggested top navigation:
┌─────────────────────────────────────────────────────────────┐
│  ONION / ACOUSTIC INTELLIGENCE                              │
│                                                             │
│  Home       About       Prototype             ● SYSTEM      │
└─────────────────────────────────────────────────────────────┘
The navbar should be:
floating
translucent
blurred
rounded
thin bordered
sticky on scroll
subtly animated
The top-left brand should be textual, not a generic onion logo.
Preferred identity:
ONION // ACOUSTIC INTELLIGENCE
Secondary micro-label:
SIH26031

4. DESIGN PHILOSOPHY
4.1 Core aesthetic
Use:
Apple × Sonar × Aerospace × Scientific Instrumentation
Avoid:
farm stock photos
cartoon onions
green agricultural dashboards
generic AI gradients
excessive orange/green
generic SaaS cards
excessive icons
conventional admin-dashboard appearance
cliché circuit-board backgrounds
The website should feel closer to:
a premium Apple product page
an aerospace sensor interface
a sonar console
a scientific instrument
an advanced radar visualization
than an agricultural portal.

5. VISUAL REFERENCES / INSPIRATION LANGUAGE
The requested visual references are:
F-22 Raptor
Akula-class submarine
Ohio-class submarine
sonar systems
radar systems
acoustic sensing
aerospace instrumentation
military-grade telemetry aesthetics
These are visual/conceptual references, not claims that the onion system uses military hardware or military algorithms.
Do not use official military logos, insignia, classified-looking interfaces, or imply endorsement or technological lineage.
Instead borrow the design principles:
F-22-inspired visual language
precision
situational awareness
sensor fusion
restrained HUD-like elements
telemetry
technical typography
information hierarchy
clean tactical minimalism
Akula-inspired visual language
underwater acoustics
passive listening
resonance
low-noise sensing
waveform visualization
sonar concepts
Ohio-class-inspired visual language
large-scale systems engineering
sensor architecture
mission-critical reliability
structured technical displays
Radar-inspired visual language
circular scanning
target detection
range rings
sweep animations
signal acquisition
confidence indicators
The result should feel inspired by advanced sensing systems, not like a military fan page.

6. COLOUR SYSTEM
Use a very soft pastel palette.
Base
Background:
#F7F8FC

Primary surface:
#FFFFFF / 55–75% opacity

Secondary surface:
#EEF1F7

Soft blue:
#DDE8F5

Soft lavender:
#E8E1F4

Soft cyan:
#DDF1F2

Soft mint:
#DDEFE8

Graphite:
#1B1D24

Secondary text:
#626875

Border:
rgba(255,255,255,0.65)
Do not use highly saturated neon colours.
For signal/acoustic highlights, use restrained cyan/blue/lavender tones.
A small amount of brighter cyan may be used for:
active sensor state
microphone recording
scan pulse
selected data
system status

7. TYPOGRAPHY
Use a premium modern sans-serif.
Preferred:
Inter
SF Pro Display equivalent
Geist
Manrope
Hierarchy:
Hero
Very large, approximately:
clamp(4rem, 9vw, 9rem)
with tight line-height.
Section heading
clamp(2.5rem, 5vw, 5rem)
Body
18–21px desktop.
Technical labels
10–13px uppercase with letter spacing.
Example:
ACOUSTIC SENSOR
SIGNAL ACQUISITION
FFT ANALYSIS
VISION PIPELINE
GRADE ENGINE
Use monospace sparingly for telemetry/data:
JetBrains Mono
IBM Plex Mono
SF Mono equivalent

8. GLASSMORPHISM SYSTEM
Glass cards should have:
translucent white surface
backdrop blur
subtle border
very soft shadow
rounded corners
internal highlight
Example conceptual style:
background: rgba(255,255,255,0.55);
backdrop-filter: blur(24px);
border: 1px solid rgba(255,255,255,0.70);
box-shadow:
  0 20px 60px rgba(40,50,80,0.08);
border-radius: 28px;
Do not make every element a card.
Use large open sections and only glass where it provides hierarchy.

9. MOTION LANGUAGE
Animations are essential.
Motion should feel:
smooth
physical
quiet
precise
continuous
scientific
Avoid:
bouncing
excessive spring animations
flashy transitions
spinning everything
gaming UI
Preferred motion:
slow sonar sweeps
acoustic wave propagation
waveform oscillation
subtle frequency bars
particles following signal paths
cards fading/sliding into place
data appearing progressively
scan-line movement
soft parallax
magnetic hover effects
gentle glass distortion
Use Framer Motion / Motion for React.
Use CSS for lightweight continuous animations.
Use Three.js only where genuinely useful.

10. HOME PAGE
The Home page is the main pitch.
It should tell the story in this order:
Problem
↓
Why vision alone has limits
↓
Acoustic intelligence
↓
How the complete grading system works
↓
Government/procurement grading context
↓
Expected outcomes
↓
Scalability
↓
Prototype CTA

11. HOME — HERO SECTION
Hero headline
Preferred:
HEAR WHAT THE EYE CAN'T SEE.
Alternative supporting line:
Acoustic intelligence for next-generation onion grading.
Supporting copy:
A non-destructive sensing layer designed to complement computer vision by probing the acoustic response of an onion for hidden internal conditions.
Do not claim proven internal-defect accuracy before experimental validation.
Hero metadata:
ACOUSTIC SENSING
NON-DESTRUCTIVE
SIGNAL PROCESSING
AI-ASSISTED GRADING
CTA:
Explore the Technology
Secondary:
Open Prototype

12. HERO VISUAL — SONAR ONION
This is one of the most important visuals.
Do not simply show an onion photograph.
Create an abstract, premium 3D onion/object silhouette at the centre.
Around it:
acoustic waves
concentric rings
radial signal propagation
subtle particles
waveform traces
frequency labels
Concept:
                 )))))))))
            ))))           ))))
         )))                 )))
       ))        ONION         ))
         )))                 )))
            ))))           ))))
                 )))))))))
But rendered as a sophisticated animated visualization.
Interaction:
cursor movement slightly changes the wave field
hover creates a sensing pulse
scroll causes the acoustic field to evolve
The visual should immediately communicate:
sound → structure → information

13. HOME — PROBLEM
Heading:
THE EYE HAS A LIMIT.
Explain:
Current procurement grading is dependent on manual inspection and visual assessment.
This creates:
inconsistency
disputes
lack of evidence
variation between inspection centres
Use three minimal glass panels:
INCONSISTENCY
Different inspectors can reach different conclusions.

DISPUTES
Farmers may not receive a detailed evidence-backed explanation.

NO EVIDENCE TRAIL
Manual grading does not inherently produce a structured audit record.
Then transition into:
What if grading could listen?

14. HOME — WHY ACOUSTICS
Heading:
THE ONION HAS A SIGNATURE.
Copy:
A camera sees the surface. An acoustic system measures a response.
Explain conceptually:
controlled acoustic excitation
onion responds
microphone captures response
signal is digitized
Fourier analysis reveals frequency-domain characteristics
extracted features support hidden-defect screening
Visual:
ACOUSTIC EXCITATION
        ↓
      ONION
        ↓
MICROPHONE RESPONSE
        ↓
     RAW SIGNAL
        ↓
      FFT / DSP
        ↓
ACOUSTIC SIGNATURE
        ↓
HIDDEN-DEFECT SCREEN
This is the core visual story of the entire website.

15. HOME — SIGNAL ANIMATION
Create a large section with a continuously animated waveform.
Left:
TIME DOMAIN
Right:
FREQUENCY DOMAIN
Animate transformation:
Waveform
     ↓
FFT
     ↓
Frequency peaks
Technical labels can include:
Sampling rate
Dominant frequency
Spectral centroid
Peak amplitude
Damping
Signal energy
These should be presented as prototype/illustrative values until the backend supplies real measurements.
Never fabricate experimental measurements.

16. HOME — COMPLETE SYSTEM
Heading:
FROM SIGNAL TO GRADE
Show the complete system as a horizontal or diagonal flow:
                ┌───────────────┐
                │     ONION     │
                └───────┬───────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼
     CAMERA FEED                ACOUSTIC FEED
          │                           │
          ▼                           ▼
   OPENCV / YOLO                 MICROPHONE
          │                           │
          ▼                           ▼
  SIZE + DEFECTS                 FFT / DSP
          │                           │
          │                    ACOUSTIC FEATURES
          │                           │
          └─────────────┬─────────────┘
                        ▼
                RULE / MODEL LAYER
                        │
                        ▼
                  GRADE DECISION
                        │
                        ▼
                DIGITAL REPORT
The visual hierarchy must show:
Acoustic Feed = differentiator
but still show:
Vision + Rule Engine = required MVP

17. HOME — PROCUREMENT / GOVERNMENT STANDARDS
Heading:
FROM STANDARDS TO SIGNAL
The master project uses configurable Grade A / URS rules.
Explain:
The system is designed around a configurable procurement policy rather than a permanently hard-coded grading rule.
Show:
ACTIVE POLICY
      ↓
GRADE A THRESHOLDS
      +
URS ENABLED / DISABLED
      +
DEFECT RULES
      ↓
CONSISTENT APPLICATION
      ↓
EVIDENCE-BACKED REPORT
The website must not invent or permanently claim universal government thresholds.
If exact official standards are displayed, they must be verified against the current applicable source before publication.
The master plan provides suggested editable starting defaults:
Parameter
Grade A
Grade URS
Diameter
45–65 mm
35–70 mm
Visible rot
Not allowed
Not allowed
Severe damage
Not allowed
Not allowed
Sprouting
Policy-dependent
Policy-dependent
These must be labelled as:
Suggested starting defaults — editable policy settings, not universal fixed standards.

18. HOME — GRADING OUTPUT
Create an elegant grade visualization.
Example:
BATCH ANALYSIS

████████████████████████  GRADE A
██████████                URS
████                      REJECTED
██                        MANUAL REVIEW
Show:
total onions
Grade A %
Grade URS %
Rejected %
Manual Review %
Formula representation:
Grade A % = NGradeA / NTotal × 100
Grade URS % = NURS / NTotal × 100
Rejected % = NRejected / NTotal × 100
Manual Review % = NManualReview / NTotal × 100
Until backend data exists, use neutral placeholders such as:
--
or clearly marked demo data.

19. HOME — EXPECTED RESULTS
Heading:
MEASURABLE OUTCOMES
Use charts for:
grading consistency
processing time
evidence completeness
defect detection
acoustic hidden-defect screening
manual-review rate
Do NOT present invented accuracy percentages as experimental results.
Use one of:
Prototype target
Illustrative
Expected
Awaiting validation
When real data exists, replace placeholders with actual measurements.
Recommended future metrics:
accuracy
precision
recall
F1
confusion matrix
false acceptance rate
false rejection rate
acoustic classification confidence
processing time/onion
repeatability
percentage requiring manual review

20. HOME — THE TRANSPARENCY DIFFERENCE
Heading:
EVERY DECISION LEAVES A TRACE.
Show a digital report mockup.
Include:
REPORT ID
BATCH ID
FARMER / SUPPLIER
PROCUREMENT CENTRE
OFFICER
DATE / TIME
ACTIVE POLICY VERSION
URS STATUS

TOTAL DETECTED
GRADE A
GRADE URS
REJECTED
MANUAL REVIEW

DEFECT BREAKDOWN
SIZE DISTRIBUTION
AI CONFIDENCE

HUMAN OVERRIDE
REASON

QR CODE
The report is one of the core MVP deliverables and should receive significant visual emphasis.

21. HOME — SCALABILITY
Heading:
BUILT FOR A SINGLE ONION. DESIGNED FOR A SYSTEM.
Use an animated progression:
PHONE PROTOTYPE
      ↓
PROCUREMENT CENTRE
      ↓
GUIDED BATCH SCANNING
      ↓
DEDICATED SENSOR STATION
      ↓
CONVEYOR INTEGRATION
      ↓
HIGH-THROUGHPUT GRADING
Future industrial architecture may include:
fixed camera
controlled acoustic excitation
piezo/contact microphone
conveyor
automated sorting output
Clearly label this as:
FUTURE INDUSTRIAL DIRECTION
not as current prototype hardware.

22. HOME — CLOSING STATEMENT
Large closing text:
FROM VISUAL INSPECTION TO STRUCTURAL SENSING.
Supporting:
Standardize what can be seen.
Investigate what cannot.
CTA:
ENTER THE PROTOTYPE

23. ABOUT PAGE
The About page should feel like a technical project brief rather than a marketing page.
Sections:
Problem
Solution
Technology
Acoustic differentiator
Feasibility
Viability
Scalability
Sustainability
Reliability / explainability
Future roadmap

24. ABOUT — PROBLEM
Explain the procurement problem:
manual inspection
inconsistent grading
disputes
lack of evidence trail
Show a before/after comparison:
BEFORE

INSPECT
  ↓
JUDGE
  ↓
GRADE
  ↓
DISPUTE?

AFTER

CAPTURE
  ↓
MEASURE
  ↓
ANALYSE
  ↓
APPLY POLICY
  ↓
EXPLAIN
  ↓
REPORT

25. ABOUT — SOLUTION
The system is not a black-box "good/bad" classifier.
It is a procurement decision-support workflow:
Individual onion detection
        +
Calibrated physical measurement
        +
Visible defect detection
        +
Configurable policy
        +
Acoustic hidden-defect screening
        +
Evidence report
        +
Human review
Important:
The officer retains authority for difficult cases.
The website should communicate human-in-the-loop design rather than pretending the model is infallible.

26. ABOUT — FEASIBILITY
Explain why the MVP is technically feasible.
Hardware
Core MVP:
smartphone camera
Acoustic Tier 2:
smartphone speaker
smartphone microphone
No added hardware is required for the phone-based acoustic proof of concept according to the master plan.
Software
Flutter / React Native
YOLO detection/segmentation
OpenCV
FastAPI / Flask / Node.js
Firebase / Supabase / PostgreSQL
PDF/HTML reporting
FFT / signal processing
Random Forest / gradient-boosted model
Data
Build the dataset using:
mixed real onions
healthy onions
damaged onions
sprouted onions
rotten onions
calibration card / ArUco marker
repeated acoustic measurements
ground-truth inspection

27. ABOUT — VIABILITY
Potential users / stakeholders:
procurement officers
procurement centres
farmers
aggregators
mandis
warehouses
exporters
food processors
procurement agencies
The system creates value through:
consistency
faster assessment
evidence
traceability
reduced ambiguity
structured records
possible hidden-defect screening
Do not make unsupported claims about financial savings.

28. ABOUT — SCALABILITY
Three levels:
LEVEL 1 — MOBILE
Phone camera + acoustic sensor.
LEVEL 2 — CENTRE
Dedicated capture station.
LEVEL 3 — INDUSTRIAL
Conveyor + fixed camera + controlled acoustic sensing + automated sorting.
Show the transition as a system architecture animation.

29. ABOUT — SUSTAINABILITY
Potential sustainability narrative:
Non-destructive screening
Acoustic screening is intended to inspect internal characteristics without cutting every onion open.
Reduced unnecessary rejection
Better evidence and calibrated measurements may reduce avoidable classification disagreements.
Digital records
Reports replace fragmented manual records with structured evidence.
Modular hardware
Future sensing hardware can evolve without changing the entire software architecture.
Local-first potential
The architecture can later support offline/on-device inference, which is explicitly listed as a future addition.
Avoid claiming measured environmental savings without data.

30. ABOUT — RELIABILITY
Create a section:
DESIGNED TO SAY "I DON'T KNOW."
This is important.
If:
image is unclear
calibration marker is missing
model confidence is low
acoustic signal is noisy
the system should be able to return:
MANUAL REVIEW
rather than inventing a grade.
This is directly aligned with the master plan's decision logic.

31. ABOUT — ACOUSTIC LIMITATIONS
Do not hide limitations.
Create a premium "engineering constraints" section:
Ambient noise
Procurement centres are noisy.
Potential mitigation:
noise-gated window
baseline subtraction
repeated measurements
Consistent positioning
Phone-to-onion geometry affects measurements.
Potential mitigation:
guided on-screen acquisition
standardized distance/orientation
Small initial dataset
Potential mitigation:
low-data-friendly models
explainable features
controlled acquisition
This section increases credibility.

32. ABOUT — ROADMAP
Timeline:
NOW
MVP VISION PIPELINE
       ↓
ACOUSTIC PROOF OF CONCEPT
       ↓
LARGER DATASET
       ↓
VALIDATED ACOUSTIC MODEL
       ↓
OFFLINE ON-DEVICE INFERENCE
       ↓
DEDICATED SENSOR HARDWARE
       ↓
INDUSTRIAL GRADING
Future items from the master plan can include:
QR batch traceability
GPS
digital scale integration
multilingual UI
procurement dashboard
decay/shelf-life prediction
farmer appeal workflow
Blockchain should be visually de-emphasized as an optional future item, not presented as a core requirement.

33. PROTOTYPE PAGE
The Prototype page should feel fundamentally different.
It should resemble a live scientific instrument.
Page title:
ACOUSTIC LAB
Subheading:
A live interface for sensing, transforming and interpreting the onion's acoustic response.
Top system state:
● SYSTEM READY
MICROPHONE
CAMERA
SIGNAL PROCESSOR
When backend is not connected:
DEMO MODE
Never fake a live sensor connection.

34. PROTOTYPE — MAIN LAYOUT
Desktop:
┌──────────────────────────────────────────────────────────┐
│                    ACOUSTIC LAB                          │
│              ● DEMO MODE / LIVE                         │
├───────────────────────────────┬──────────────────────────┤
│                               │                          │
│       ONION / SENSOR          │     MICROPHONE FEED      │
│       VISUALIZATION           │                          │
│                               │                          │
├───────────────────────────────┼──────────────────────────┤
│                               │                          │
│       TIME DOMAIN             │      FFT / SPECTRUM      │
│                               │                          │
├───────────────────────────────┴──────────────────────────┤
│                  ACOUSTIC SIGNATURE                      │
├───────────────────────────────┬──────────────────────────┤
│ CAMERA / OPENCV               │ CLASSIFICATION           │
│                               │                          │
├───────────────────────────────┴──────────────────────────┤
│ DATASET / HISTORY / REPORT                              │
└──────────────────────────────────────────────────────────┘
On mobile, stack panels vertically.

35. PROTOTYPE — ACOUSTIC EXCITATION
Show:
CHIRP GENERATOR

100 Hz ─────────────── 8 kHz

[ START TEST ]

Status:
WAITING
RECORDING
PROCESSING
COMPLETE
The master plan specifies a logarithmic chirp of approximately 100 Hz–8 kHz for the acoustic proof of concept.
Make this parameter visible.

36. PROTOTYPE — MICROPHONE FEED
Real backend later:
live waveform
amplitude
sample rate
duration
noise floor
clipping indicator
Visual:
MIC INPUT

Amplitude
│       /\      /\_
│  /\__/  \_/\_/   \__
│_/                  \___
└───────────────────────── Time
Animation must stop / freeze when not receiving actual data.

37. PROTOTYPE — FOURIER / FFT
Large central panel:
FOURIER TRANSFORM
Explain briefly:
The recorded time-domain signal is transformed into the frequency domain to expose resonant and spectral characteristics.
Display:
dominant frequency
spectral centroid
amplitude
damping / decay
spectral energy
Use a dynamic spectrum.
Possible interaction:
hover frequency peaks
click peak
show feature value
toggle linear/log scale

38. PROTOTYPE — ACOUSTIC SIGNATURE
Make this the visual centerpiece of the Prototype page.
Show:
ACOUSTIC SIGNATURE

███████
██  ████
██     ███
██        ██
████████████
But implement as a real animated spectral visualization.
Potential derived features:
DOMINANT FREQUENCY
SPECTRAL CENTROID
PEAK AMPLITUDE
DAMPING RATE
SIGNAL ENERGY
If no real backend data exists, show:
WAITING FOR SIGNAL
not invented numbers.

39. PROTOTYPE — CAMERA FEED
Show:
VISION SENSOR
Features:
live camera feed
onion segmentation
bounding boxes
defect labels
calibration marker
estimated diameter
Possible overlay:
ONION #07
DIAMETER: -- mm
DEFECT: --
CONFIDENCE: --
Use OpenCV/YOLO visuals only as supporting evidence.

40. PROTOTYPE — SENSOR FUSION
Create a striking convergence visualization:
CAMERA
  │
  ├── Size
  ├── Damage
  ├── Rot
  └── Sprout
       │
       ▼
   ┌─────────┐
   │  FUSION │
   └─────────┘
       ▲
       │
ACOUSTICS
  │
  ├── Resonance
  ├── Spectral features
  ├── Damping
  └── Hidden-condition signal
       │
       ▼
  DECISION SUPPORT
This is where the project should visibly distinguish itself from a standard OpenCV classifier.

41. PROTOTYPE — RULE ENGINE
Display the actual decision logic conceptually:
VISIBLE ROT?
    YES → REJECTED
    NO
      ↓
CALIBRATION VALID?
    NO → MANUAL REVIEW
    YES
      ↓
QUALITY + SIZE
      ↓
ACTIVE POLICY
      ↓
GRADE A / URS / REJECTED
Acoustic screening can then appear as a parallel hidden-defect check:
VISUAL GRADE
      +
ACOUSTIC SCREEN
      ↓
FINAL CONFIDENCE / REVIEW FLAG
Do not visually imply that acoustic screening overrides official policy rules unless the actual backend design later establishes that behavior.

42. PROTOTYPE — DATASET
Dataset table:
ID | IMAGE | AUDIO | FFT | LABEL | GRADE | CONFIDENCE
Example rows should be demo placeholders unless real dataset records are connected.
Provide filters:
Healthy
Damaged
Rotten
Sprouted
Grade A
URS
Rejected
Manual Review

43. PROTOTYPE — MOCK REPORT
Include a button:
GENERATE REPORT
Then render a report preview containing:
batch information
policy version
annotated image
defect breakdown
Grade A / URS percentages
manual-review items
acoustic screening results if available
QR code
audit trail
This should connect the Prototype page back to the project's actual procurement deliverable.

44. PROTOTYPE — DEMO MODE
Until backend integration is complete, use a clear state:
SIMULATION / DEMO DATA
Do not present fabricated data as measured experimental data.
Provide:
LOAD DEMO SAMPLE
START ACOUSTIC TEST
RUN FFT
RUN VISION ANALYSIS
GENERATE REPORT
Later these buttons become API actions.

45. DATA STATES / UI STATES
Every sensor component must support:
IDLE
WAITING FOR INPUT
RECORDING
ACQUIRING SIGNAL
PROCESSING
ANALYZING
COMPLETE
ANALYSIS COMPLETE
ERROR
SIGNAL QUALITY INSUFFICIENT
MANUAL REVIEW
INSUFFICIENT CONFIDENCE — HUMAN REVIEW REQUIRED
This is essential for a credible engineering UI.

46. SONAR / RADAR VISUAL SYSTEM
Use a recurring visual language throughout the website:
Concentric rings
Represent:
propagation
sensing
range
response
Sweep
A slow radial sweep can represent signal acquisition.
Pulse
A pulse travels outward from the onion when the acoustic test begins.
Return signal
A reflected waveform returns to the central sensor.
Frequency field
Subtle spectral bars appear after acquisition.
The animations should communicate the physics metaphorically without claiming that the onion system literally operates like naval sonar.

47. F-22 / SUBMARINE VISUAL REFERENCES — IMPLEMENTATION
Use subtle section labels such as:
SENSOR FUSION
SIGNAL ACQUISITION
MULTI-MODAL ANALYSIS
TARGET / OBJECT DETECTION
Possible hero microcopy:
ONE OBJECT. MULTIPLE SENSORS. ONE EVIDENCE TRAIL.
Avoid:
military insignia
aircraft images as hero art
submarine photographs as hero art
weapons imagery
fake military HUD overlays
claims of military-grade accuracy
claims of military-derived technology
The inspiration should be systems engineering, not military branding.

48. VISUAL ASSETS
Preferred visuals:
abstract 3D onion/object
acoustic waves
sonar rings
radar sweep
waveform
FFT spectrum
spectral heatmap
segmentation mask
calibration marker
digital report
data table
system architecture
industrial conveyor future concept
Do not use stock agricultural photographs as the dominant visual language.
If onion photography is used, treat the onion as a sensor test object, not as decorative food photography.

49. 3D / WEBGL DIRECTION
Three.js can be used for the hero.
Potential scene:
Central onion
+
transparent acoustic shell
+
concentric waves
+
floating particles
+
soft lighting
+
subtle camera movement
The 3D scene must remain lightweight.
Provide a CSS fallback for:
low-power devices
mobile
reduced-motion users

50. ACCESSIBILITY
Must support:
keyboard navigation
readable contrast
reduced motion
semantic HTML
screen-reader labels
focus states
mobile responsiveness
If prefers-reduced-motion is enabled:
disable sonar sweeps
disable floating particles
reduce waveform movement
retain static visual hierarchy

51. RESPONSIVE DESIGN
Desktop should feel cinematic.
Tablet should remain structured.
Mobile should prioritize:
Hero
↓
Problem
↓
Acoustic concept
↓
System
↓
Standards
↓
Outcomes
↓
Prototype
Do not attempt to preserve desktop multi-column layouts on mobile if they become cramped.

52. PERFORMANCE
The website must remain fast.
Rules:
lazy-load heavy 3D
optimize images
avoid huge video backgrounds
use requestAnimationFrame responsibly
throttle expensive signal visualizations
pause off-screen animations
avoid unnecessary Three.js scenes
use CSS animations for simple effects
support reduced motion
The visual sophistication must not make the website unusable.

53. TECH STACK
Recommended:
Frontend
React
Vite
TypeScript
Tailwind CSS
Animation
Framer Motion / Motion
CSS animations
3D
Three.js
React Three Fiber if appropriate
Charts
Recharts / Chart.js
custom SVG for specialized acoustic visualizations
Icons
Lucide React
Backend integration later
FastAPI
WebSocket for live signal streaming
REST API for batch/report operations
Vision
YOLO
OpenCV
DSP
NumPy
SciPy
ML
Random Forest / gradient boosting initially
Storage
Firebase / Supabase / PostgreSQL
These follow the architecture described in the project master plan; implementation may select one option after team verification.

54. FRONTEND COMPONENT ARCHITECTURE
Suggested component tree:
App
├── Navbar
├── Home
│   ├── HeroSonar
│   ├── ProblemSection
│   ├── AcousticConcept
│   ├── SignalTransformation
│   ├── SystemArchitecture
│   ├── StandardsSection
│   ├── GradeVisualization
│   ├── ExpectedResults
│   ├── TransparencyReport
│   ├── Scalability
│   └── FinalCTA
│
├── About
│   ├── Problem
│   ├── Solution
│   ├── Feasibility
│   ├── Viability
│   ├── Scalability
│   ├── Sustainability
│   ├── Reliability
│   ├── Limitations
│   └── Roadmap
│
└── Prototype
    ├── SystemStatus
    ├── OnionVisualizer
    ├── MicrophoneFeed
    ├── TimeDomainChart
    ├── FFTSpectrum
    ├── AcousticSignature
    ├── CameraFeed
    ├── OpenCVOverlay
    ├── SensorFusion
    ├── RuleEngine
    ├── Dataset
    └── ReportPreview

55. BACKEND CONTRACT PREPARATION
The frontend should be designed so real data can be inserted later.
Example conceptual object:
type AcousticResult = {
  status: "idle" | "recording" | "processing" | "complete" | "error";
  sampleRate?: number;
  durationMs?: number;
  dominantFrequency?: number;
  spectralCentroid?: number;
  peakAmplitude?: number;
  dampingRate?: number;
  confidence?: number;
  hiddenDefectFlag?: boolean;
};
Vision:
type OnionDetection = {
  id: string;
  bbox: [number, number, number, number];
  diameterMm?: number;
  damaged?: boolean;
  rotten?: boolean;
  sprouted?: boolean;
  undersized?: boolean;
  confidence?: number;
};
Grading:
type GradeResult = {
  grade: "GRADE_A" | "URS" | "REJECTED" | "MANUAL_REVIEW";
  reasonCodes: string[];
  confidence?: number;
  policyId: string;
  policyVersion: string;
};
Do not expose fake values when these objects are not populated.

56. SEO / PAGE METADATA
Suggested title:
Onion Acoustic Intelligence — Next-Generation Onion Grading | SIH26031
Suggested description:
A non-destructive, AI-assisted onion procurement grading system combining computer vision, calibrated sizing, configurable grading rules, digital evidence, and acoustic hidden-defect screening.
Keywords should naturally include:
onion grading
acoustic testing
acoustic sensing
onion quality grading
AI onion grading
computer vision
FFT
hidden defect detection
non-destructive testing
procurement grading
Grade A
URS
digital quality report
Do not keyword-stuff.

57. CONTENT ACCURACY RULES
This section is mandatory.
The website must distinguish between:
VERIFIED / CURRENT
Official procurement requirements and standards after source verification.
PROJECT DESIGN
Architecture and workflow specified by the team.
PROTOTYPE
Features actually implemented.
EXPECTED
Targets/hypotheses awaiting validation.
FUTURE
Industrial or post-hackathon directions.
Never turn:
"expected"
into:
"achieved."
Never turn:
"future"
into:
"currently implemented."
Never fabricate accuracy.
Never fabricate acoustic defect-detection performance.
Never fabricate government approval.
Never imply the project is already deployed at procurement centres unless that has actually happened.

58. IMPORTANT TERMINOLOGY
Use:
URS = Under Relaxed Specification
Do not describe URS as:
reject
undersized/rotten/sprouted
a synonym for defective
The active policy determines whether URS is enabled and what thresholds apply.
Use:
Grade A / Grade URS / Rejected / Manual Review
where appropriate.

59. CORE PROJECT HIERARCHY
The entire website should communicate this hierarchy:
                    ONION GRADING
                         │
              ┌──────────┴──────────┐
              │                     │
          REQUIRED MVP          DIFFERENTIATOR
              │                     │
       COMPUTER VISION          ACOUSTICS
              │                     │
       ┌──────┼──────┐          FFT / DSP
       │      │      │              │
      SIZE  DEFECTS  CALIBRATION  HIDDEN
       │      │      │            DEFECT
       └──────┴──────┘              │
              │                     │
              └──────────┬──────────┘
                         ▼
                  DECISION SUPPORT
                         │
                         ▼
                   DIGITAL REPORT
Acoustics should be the visual star, but not misrepresented as replacing the MVP.

60. SIGNATURE VISUAL MOMENT
The website should have one unforgettable animation.
Suggested sequence:
Step 1
A single onion appears.
Step 2
A soft acoustic pulse leaves the sensor.
Step 3
The wave reaches the onion.
Step 4
The onion responds with a subtle deformation/ripple.
Step 5
The response returns to the sensor.
Step 6
The waveform becomes visible.
Step 7
The waveform transforms into an FFT spectrum.
Step 8
A frequency signature appears.
Step 9
The system combines:
VISION
+
ACOUSTICS
+
POLICY
Step 10
Final output:
GRADE A
or
URS
or
REJECTED
or
MANUAL REVIEW
Step 11
A report card appears.
This sequence should be the visual metaphor for the entire project.

61. MICRO-INTERACTIONS
Examples:
Navbar
Glass intensifies slightly on scroll.
CTA
Subtle magnetic hover.
Acoustic section
Mouse movement shifts wave field.
Frequency graph
Hovering a peak reveals its frequency.
Grade card
Clicking a grade reveals its decision criteria.
System architecture
Hovering a component highlights its data flow.
Prototype
Starting the acoustic test changes:
READY
→
ACQUIRING
→
PROCESSING
→
SIGNATURE FOUND
Report
QR code softly pulses only when report is generated.

62. WHAT THE WEBSITE MUST NOT DO
Do not:
make it look like a farming marketplace
make OpenCV the hero
make generic "AI" the hero
use excessive onion photographs
claim acoustic detection is already scientifically validated for the team's onion dataset
invent accuracy metrics
hard-code unverified government standards
claim military technology is being used
imply F-22/submarine hardware is part of the system
make the prototype appear live when it is simulated
make future industrial hardware appear already built
overuse glass cards
overuse neon
use distracting animations
sacrifice usability for aesthetics

63. IMPLEMENTATION PHASES
Phase 1 — Static visual system
Build:
navbar
Home
About
Prototype shell
design tokens
typography
glass components
responsive layout
Phase 2 — Visual storytelling
Add:
sonar hero
acoustic wave animation
system architecture animation
FFT mock visualization
report mockup
scalability animation
Phase 3 — Prototype simulation
Add:
demo microphone feed
simulated waveform
simulated FFT
simulated camera
mock dataset
mock report generation
All simulated data must be visibly labelled.
Phase 4 — Backend integration
Replace simulated streams with:
actual microphone feed
actual camera feed
FFT results
OpenCV/YOLO results
rule engine
acoustic model
database
reports
Phase 5 — Validation
Check:
no fabricated claims
responsive design
accessibility
performance
API failure states
sensor states
report accuracy
standards citations
terminology

64. CLAUDE VERIFICATION CHECKLIST
Before sending the implementation to Google Antigravity, Claude should verify:
Project alignment
[ ] Website matches the master project plan.
[ ] MVP remains clearly represented.
[ ] Acoustic system is presented as the chosen differentiator.
[ ] Acoustic module does not falsely replace the MVP.
[ ] Decay/shelf-life prediction remains secondary/future.
Visual alignment
[ ] Apple glassmorphism.
[ ] Soft pastel palette.
[ ] Sonar/radar visual language.
[ ] Aerospace instrumentation feel.
[ ] Minimalistic.
[ ] Premium.
[ ] No generic agricultural aesthetic.
Content accuracy
[ ] URS terminology is correct.
[ ] Government standards are verified before exact claims.
[ ] Suggested thresholds are labelled as configurable starting defaults.
[ ] No fabricated experimental results.
[ ] Demo data is labelled.
[ ] Future hardware is labelled as future.
UX
[ ] Exactly three primary tabs.
[ ] Mobile responsive.
[ ] Accessibility support.
[ ] Reduced-motion support.
[ ] Loading/error/manual-review states.
[ ] No fake live data.
Technical
[ ] Components are modular.
[ ] Backend integration points are clean.
[ ] WebSocket architecture can be added later.
[ ] Heavy 3D is lazy-loaded.
[ ] Charts can consume real backend data.
[ ] Prototype simulation can be replaced without redesign.

65. GOOGLE ANTIGRAVITY IMPLEMENTATION BRIEF
Build the website from this document as the frontend design contract.
The result must feel like:
Apple-designed scientific instrumentation for acoustic onion intelligence.
Do not interpret "onion website" as permission to use agricultural visual conventions.
The primary visual motif is:
An object being interrogated by sound.
The primary narrative is:
See the surface. Hear the structure. Standardize the decision. Record the evidence.
The acoustic system must be the most memorable part of the website.
The computer-vision system must remain visible because it is the core MVP.
The digital report must remain visible because transparency/auditability is a central project value.

66. FINAL DESIGN NORTH STAR
If an evaluator opens the site for five seconds, they should understand:
This project uses computer vision for onion procurement grading and adds acoustic sensing to investigate what the camera cannot see.
If they stay for thirty seconds, they should understand:
The system measures individual onions, calibrates physical size, applies configurable procurement rules, detects visible defects, performs acoustic hidden-defect screening, and produces an evidence-backed report.
If they explore the Prototype page, they should feel:
"I am looking at a real sensing system."
The final design should not scream "agriculture."
It should whisper:
SONAR. SIGNAL. STRUCTURE. INTELLIGENCE.
And the final visual statement should be:
HEAR WHAT THE EYE CAN'T SEE.

SOURCE NOTE
This specification is derived from the uploaded project master plan:
AI-Based Onion Quality Grading — Master Plan (SIH26031)
The master plan establishes the manual-grading problem, required image-based MVP, calibrated sizing, configurable Grade A/URS rules, evidence-backed reporting, acoustic hidden-defect screening as the chosen differentiator, two-tier architecture, data-collection plan, scope boundaries, and demo flow.
Where this website specification introduces visual direction, interaction design, UI architecture, animation concepts, or implementation recommendations, those are frontend design decisions, not claims that they already exist in the project backend.
