# Website Text Content and Specification

## Location: `components\Navbar.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| // | `<span>` | default/inherited size |
| SIH26031 | `<span>` | default/inherited size |
| BIO-ACOUSTIC HARDWARE PLATFORM | `<p>` | default/inherited size |
| HARDWARE READY | `<span>` | default/inherited size |
| TEST BENCH | `<NavLink>` | default/inherited size |
| SIH26031 | `<span>` | default/inherited size |
| OPEN BENCH | `<NavLink>` | default/inherited size |

## Location: `components\OnionLayerInspector.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| TACTILE HARDWARE DEMO | `<span>` | default/inherited size |
| // PHYSICAL ACOUSTICS | `<span>` | default/inherited size |
| ONION CROSS-SECTION ACOUSTIC PROBE | `<h3>` | default/inherited size |
| Click a sample to trigger piezo solenoid impact and compare external vision vs internal acoustic echo. | `<p>` | default/inherited size |
| handleSelect('solid')}             className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${               activeState === 'solid'                 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-lg'                 : 'text-text-muted hover:text-white'             }`}           >             SOLID (GRADE A) | `<button>` | default/inherited size |
| handleSelect('rot')}             className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${               activeState === 'rot'                 ? 'bg-red-500/20 text-red-300 border border-red-500/50 shadow-lg'                 : 'text-text-muted hover:text-white'             }`}           >             HIDDEN ROT | `<button>` | default/inherited size |
| handleSelect('hollow')}             className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${               activeState === 'hollow'                 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-lg'                 : 'text-text-muted hover:text-white'             }`}           >             HOLLOW CORE | `<button>` | default/inherited size |
| PIEZO TRANSDUCER CONTACT POINT | `<span>` | default/inherited size |
| $x=0$ | `<span>` | default/inherited size |
| DECISION ENGINE STATE | `<span>` | default/inherited size |
| RGB COMPUTER VISION: | `<span>` | default/inherited size |
| PIEZO ACOUSTIC DSP: | `<span>` | default/inherited size |
| PEAK FREQUENCY (FFT): | `<span>` | default/inherited size |
| SOUND VELOCITY ($v$) | `<span>` | default/inherited size |
| DAMPING COEFF ($\alpha$) | `<span>` | default/inherited size |

## Location: `components\PremiumNav.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| OAI | `<div>` | default/inherited size |
| Menu | `<button>` | default/inherited size |

## Location: `components\SiteNav.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Onion AI | `<span>` | default/inherited size |
| SIH 2026 | `<span>` | default/inherited size |
| setOpen(false)}                     className={`px-4 py-3 rounded-2xl text-sm font-sans font-medium transition-all duration-300 ${                       active                         ? 'bg-onion-soft text-onion-deep border border-onion/10'                         : 'text-text-secondary hover:bg-bg-soft hover:text-text-primary'                     }`}                   >                     {label} | `<Link>` | default/inherited size |
| Project Code | `<span>` | default/inherited size |

## Location: `pages\About.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Quality Control. | `<span>` | default/inherited size |
| 26 million tonnes | `<strong>` | default/inherited size |
| internal rot | `<strong>` | default/inherited size |
| hollow centres | `<strong>` | default/inherited size |
| early-stage bacterial soft rot | `<strong>` | default/inherited size |
| ₹3,800 crore | `<strong>` | default/inherited size |
| That's what we're building. | `<strong>` | default/inherited size |
| Real Impact | `<span>` | default/inherited size |
| Shift | `<span>` | default/inherited size |
| Traditional Grading | `<h3>` | default/inherited size |
| Surface Only | `<span>` | default/inherited size |
| 0{i + 1} | `<span>` | default/inherited size |
| Our Acoustic Model | `<h3>` | default/inherited size |
| Evidence-Based | `<span>` | default/inherited size |
| Highlights | `<span>` | default/inherited size |
| Gallery | `<span>` | default/inherited size |
| live. | `<span>` | default/inherited size |

## Location: `pages\Prototype.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Bench | `<span>` | default/inherited size |
| System Online | `<span>` | default/inherited size |
| SIH26031 · Demo Mode | `<span>` | default/inherited size |
| CAM_1 (TOP VIEW) | `<span>` | default/inherited size |
| Processing CV Matrix… | `<span>` | default/inherited size |
| Assessment Result | `<p>` | default/inherited size |
| Testing Sequence | `<h3>` | default/inherited size |
| Backend Integration | `<h3>` | default/inherited size |
| This UI is prepared to connect with the Python backend via WebSocket. Once integrated, it will: | `<p>` | default/inherited size |
| Sensor Readout | `<h3>` | default/inherited size |
| Hardware Config | `<h3>` | default/inherited size |

## Location: `prototype\Dataset.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| DATASET / HISTORY | `<TechLabel>` | default/inherited size |
| DEMO DATA | `<span>` | default/inherited size |
| setActiveFilter(f)}             className={`px-3 py-1 rounded-sm text-[9px] font-semibold tracking-widest uppercase transition-all border ${               activeFilter === f                 ? 'text-cyan border-cyan'                 : 'text-text-sec border-border hover:bg-white/5'             }`}             style={{                background: activeFilter === f ? 'rgba(0,200,255,0.1)' : 'var(--bg-mid)',               borderColor: activeFilter === f ? 'var(--cyan)' : 'var(--border)'             }}           >             {f.replace('_', ' ')} | `<button>` | default/inherited size |
| All rows are demo placeholders. Real records will populate from backend. | `<p>` | default/inherited size |

## Location: `prototype\FFTSpectrum.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| FOURIER TRANSFORM — FFT SPECTRUM | `<TechLabel>` | default/inherited size |
| ANALYSIS COMPLETE | `<TechLabel>` | default/inherited size |
| SIMULATION / DEMO DATA — Illustrative FFT visualization only. | `<p>` | default/inherited size |

## Location: `prototype\MicrophoneFeed.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| MICROPHONE FEED | `<TechLabel>` | default/inherited size |
| RECORDING | `<TechLabel>` | default/inherited size |
| IDLE | `<TechLabel>` | default/inherited size |
| SIMULATION / DEMO DATA | `<p>` | default/inherited size |

## Location: `prototype\ReportPreview.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| DIGITAL QUALITY REPORT | `<TechLabel>` | default/inherited size |
| SIMULATION / DEMO DATA — Not experimental results | `<p>` | default/inherited size |
| GRADE DECISION | `<TechLabel>` | default/inherited size |
| SIMULATION / DEMO DATA — Real values will populate from the backend API when connected. | `<p>` | default/inherited size |

## Location: `prototype\RuleEngine.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| RULE ENGINE | `<TechLabel>` | default/inherited size |
| DECISION REACHED | `<TechLabel>` | default/inherited size |
| GRADE DECISION | `<TechLabel>` | default/inherited size |
| DEMO DATA — Not a real analysis result | `<TechLabel>` | default/inherited size |
| AWAITING INPUT | `<TechLabel>` | default/inherited size |
| ACOUSTIC SCREEN OVERLAY | `<TechLabel>` | default/inherited size |
| Hidden-defect flag: | `<span>` | default/inherited size |
| Acoustic result may trigger Manual Review or alter confidence — does not replace core policy rules. | `<p>` | default/inherited size |

## Location: `prototype\SensorFusion.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| SENSOR FUSION | `<TechLabel>` | default/inherited size |
| CAMERA | `<TechLabel>` | default/inherited size |
| FUSION | `<TechLabel>` | default/inherited size |
| DECISION SUPPORT | `<TechLabel>` | default/inherited size |
| ACOUSTICS | `<TechLabel>` | default/inherited size |
| FUSION COMPLETE — READY FOR RULE ENGINE | `<TechLabel>` | default/inherited size |
| SIMULATION / DEMO DATA | `<p>` | default/inherited size |

## Location: `prototype\SonarVisualizer.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| ONION SENSOR | `<TechLabel>` | default/inherited size |
| ACTIVE | `<TechLabel>` | default/inherited size |
| SIMULATION / DEMO DATA | `<p>` | default/inherited size |

## Location: `sections\AboutPreview.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Project Context | `<p>` | default/inherited size |
| Built for the reality of procurement. | `<h2>` | default/inherited size |
| OAI is developed specifically for agricultural procurement centres, addressing the real-world friction between buyers and suppliers over subjective grading decisions. The system is designed to be mobile-first, operating effectively even in dusty, challenging packhouse environments. | `<p>` | default/inherited size |

## Location: `sections\AcousticConcept.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| PHYSICAL ACOUSTIC PIPELINE | `<span>` | default/inherited size |
| BULB RESONANCE. | `<span>` | default/inherited size |
| BIO-ACOUSTIC WAVE EQUATION & MATHEMATICAL FOUNDATION | `<h4>` | default/inherited size |
| 1. SOUND VELOCITY & ELASTICITY | `<span>` | default/inherited size |
| v = √(E / ρ) | `<p>` | default/inherited size |
| Where E is Young&apos;s Modulus of elasticity of fleshy scales and ρ is tissue density (kg/m³). Fungal rot liquefies cell pectin, reducing E by 60%+ and slowing sound propagation. | `<p>` | default/inherited size |
| 2. ACOUSTIC IMPEDANCE BOUNDARY | `<span>` | default/inherited size |
| Z = ρ · v | `<p>` | default/inherited size |
| When sound hits internal rotten liquid pockets or air cavities, impedance mismatch (Z₁ ≠ Z₂) causes acoustic reflections, split double frequency peaks, and heavy signal decay (α). | `<p>` | default/inherited size |

## Location: `sections\AcousticSection.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| ))} | `<div>` | default/inherited size |
| ACOUSTIC PROBING ACTIVE | `<span>` | default/inherited size |
| IMPULSE_01 | `<span>` | default/inherited size |
| RESP_0.02s | `<span>` | default/inherited size |
| INTERNAL ROT DETECTED | `<span>` | default/inherited size |
| ENHANCED MODULE | `<span>` | default/inherited size |
| CURRENTLY IN R&D | `<span>` | default/inherited size |
| While computer vision handles size and surface defects, our advanced acoustic module sends a physical impulse through the onion to analyze its structural integrity. | `<p>` | default/inherited size |
| By analyzing the acoustic response, the system can flag potential internal issues—such as neck rot or hollow centres—before they reach the supermarket shelf. | `<p>` | default/inherited size |
| Learn about acoustic grading | `<a>` | default/inherited size |

## Location: `sections\AIGradingReveal.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Grading | `<span>` | default/inherited size |
| Analyzing spectral signature… | `<p>` | default/inherited size |
| Analysis Complete | `<span>` | default/inherited size |
| Quality Assessment | `<div>` | default/inherited size |

## Location: `sections\BatchReport.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Batch Intelligence | `<p>` | default/inherited size |
| Every inspection run produces a structured grade distribution and a full evidence report — designed to support buyer conversations and procurement audits. | `<p>` | default/inherited size |
| DEMO DATA — illustrative values | `<p>` | default/inherited size |
| EVERY DECISION LEAVES A TRACE. | `<p>` | default/inherited size |
| Batch inspection report | `<p>` | default/inherited size |
| COMPLETE | `<span>` | default/inherited size |
| OAI-PROTO-01 · DEMO DATA | `<p>` | default/inherited size |
| View sample report | `<button>` | default/inherited size |

## Location: `sections\Capabilities.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Capabilities | `<p>` | default/inherited size |
| A clearer inspection workflow. | `<h2>` | default/inherited size |
| Computer vision handles what's visible. Acoustic intelligence probes what isn't. | `<p>` | default/inherited size |

## Location: `sections\CinematicHero.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Surface. | `<span>` | default/inherited size |
| Scroll | `<span>` | default/inherited size |

## Location: `sections\CoreStorySequence.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Layers | `<span>` | default/inherited size |

## Location: `sections\CtaBanner.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| AI | `<span>` | default/inherited size |
| COMPUTER VISION | `<span>` | default/inherited size |
| CALIBRATION | `<span>` | default/inherited size |
| EVIDENCE | `<span>` | default/inherited size |
| Request full access | `<Link>` | default/inherited size |
| ONION//VISION | `<span>` | default/inherited size |
| PROJECT SIH26031 | `<span>` | default/inherited size |
| PLATFORM | `<Link>` | default/inherited size |
| TECHNOLOGY | `<Link>` | default/inherited size |
| ABOUT | `<Link>` | default/inherited size |
| CONTACT | `<Link>` | default/inherited size |
| SYSTEM STATUS | `<span>` | default/inherited size |
| ONLINE | `<span>` | default/inherited size |

## Location: `sections\EditorialProblem.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Quality is not always visible. | `<h2>` | default/inherited size |
| Surface checks alone can miss internal-quality risk. Our prototype combines visual inspection with a controlled acoustic screening signal. | `<p>` | default/inherited size |

## Location: `sections\FeatureDetail.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| How it works | `<p>` | default/inherited size |
| The onion has a signature. | `<h2>` | default/inherited size |
| A camera sees the surface. An acoustic signal measures what's inside. | `<p>` | default/inherited size |
| Values marked "Prototype target" and "Awaiting validation" are illustrative until experimental data is available. | `<p>` | default/inherited size |

## Location: `sections\FeaturePanels.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Vision | `<h3>` | default/inherited size |
| Detects surface condition, size and visible defects. | `<p>` | default/inherited size |
| Acoustic screening | `<h3>` | default/inherited size |
| Uses a controlled tap to flag possible hidden-quality risk for review. | `<p>` | default/inherited size |

## Location: `sections\FFTVisualization.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Insight | `<span>` | default/inherited size |
| Spectral Signature | `<h3>` | default/inherited size |
| Fast Fourier Transform (FFT) — Frequency Domain | `<span>` | default/inherited size |
| Signal | `<span>` | default/inherited size |
| Harmonics | `<span>` | default/inherited size |
| 100 | `<span>` | default/inherited size |
| 75 | `<span>` | default/inherited size |
| 50 | `<span>` | default/inherited size |
| 25 | `<span>` | default/inherited size |
| ))} | `<div>` | default/inherited size |
| Frequency | `<div>` | default/inherited size |
| Amplitude | `<div>` | default/inherited size |
| 0.0 kHz | `<span>` | default/inherited size |
| 5.0 kHz | `<span>` | default/inherited size |
| 10.0 kHz | `<span>` | default/inherited size |
| 15.0 kHz | `<span>` | default/inherited size |
| 20.0 kHz | `<span>` | default/inherited size |
| Illustrative simulation — actual spectral data will be generated by the prototype hardware. | `<p>` | default/inherited size |

## Location: `sections\FinalCTA.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Request a demonstration | `<button>` | default/inherited size |

## Location: `sections\FooterCTA.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Get Involved | `<div>` | default/inherited size |
| further? | `<span>` | default/inherited size |
| Dive into the working prototype, learn about our technical approach, or connect with the team behind the project. | `<p>` | default/inherited size |
| Onion AI | `<span>` | default/inherited size |
| — SIH26031 | `<span>` | default/inherited size |
| Smart India Hackathon 2026 · Non-Destructive Acoustic Quality Grading | `<p>` | default/inherited size |

## Location: `sections\GradeVisualization.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| BATCH OUTPUT ANALYTICS | `<span>` | default/inherited size |
| OUTCOMES. | `<span>` | default/inherited size |
| BATCH DISTRIBUTION SUMMARY | `<h3>` | default/inherited size |
| SIMULATED DEMO BATCH | `<span>` | default/inherited size |
| BATCH DISTRIBUTION | `<span>` | default/inherited size |

## Location: `sections\HardwareShowcase.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| A compact station designed for real-world procurement environments. Every element serves a distinct inspection purpose. | `<h2>` | default/inherited size |

## Location: `sections\Hero.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| LIVE INSPECTION | `<p>` | default/inherited size |
| ONION QUALITY SYSTEM v1.0 | `<p>` | default/inherited size |
| ACTIVE | `<span>` | default/inherited size |
| AI CONFIDENCE | `<span>` | default/inherited size |
| 96.4% | `<span>` | default/inherited size |
| 01 | `<p>` | default/inherited size |
| AI INSPECTION SYSTEM | `<p>` | default/inherited size |
| PRECISION AGRICULTURE · AI QUALITY INTELLIGENCE | `<p>` | default/inherited size |
| Measure every | `<span>` | default/inherited size |
| AI-powered onion quality grading for transparent and consistent procurement. Computer vision, calibrated size measurement and configurable rule engines — all in one mobile-first platform. | `<p>` | default/inherited size |

## Location: `sections\HeroSonar.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| LIVE OSCILLOSCOPE TRACE | `<span>` | default/inherited size |
| SOLID (210Hz) vs ROT (95Hz) | `<span>` | default/inherited size |
| SIH26031 HARDWARE SPECIFICATION | `<span>` | default/inherited size |
| PIEZO TRANSDUCER & RGB VISION | `<span>` | default/inherited size |
| RESONANCE | `<span>` | default/inherited size |
| Nondestructive internal defect detection for onions using solenoid impulse chirps, contact piezos, and calibrated computer vision. Detecting internal neck rot without cutting. | `<p>` | default/inherited size |
| ACOUSTIC BAND | `<span>` | default/inherited size |
| 100Hz – 2.5kHz | `<span>` | default/inherited size |
| INTERNAL ROT ACCURACY | `<span>` | default/inherited size |
| 94.2% DFT | `<span>` | default/inherited size |
| THROUGHPUT | `<span>` | default/inherited size |
| 1.2 SEC / ONION | `<span>` | default/inherited size |
| TRANSDUCER SIGNAL: | `<span>` | default/inherited size |
| PIEZO-CONTACT ACTIVE | `<span>` | default/inherited size |
| SOLENOID IMPULSE TESTED: | `<span>` | default/inherited size |
| AGMARK / URS ENGINE: | `<span>` | default/inherited size |
| POLICY MAPPED | `<span>` | default/inherited size |

## Location: `sections\IndustrialHero.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| SN-9428-A | `<span>` | default/inherited size |
| STAGE 1: ACQUISITION | `<div>` | default/inherited size |
| SOLENOID TAP | `<div>` | default/inherited size |
| )} | `<div>` | default/inherited size |
| PIEZO (0-2.5kHz) | `<div>` | default/inherited size |
| RGB VISION | `<div>` | default/inherited size |
| WAVEFORM LOG | `<div>` | default/inherited size |
| DECISION MATRIX | `<div>` | default/inherited size |
| GRADE A | `<span>` | default/inherited size |
| [ PASS ] | `<span>` | default/inherited size |
| GRADE URS | `<span>` | default/inherited size |
| [ REVIEW ] | `<span>` | default/inherited size |
| REJECTED | `<span>` | default/inherited size |
| [ FAIL ] | `<span>` | default/inherited size |
| SEQ: {scanPhase + 1}/4 | `<span>` | default/inherited size |
| SEC-01 // EQUIPMENT SPECIFICATION | `<span>` | default/inherited size |
| BEYOND THE SKIN. | `<span>` | default/inherited size |
| Controlled acoustic response and RGB vision for evidence-led onion procurement screening. | `<p>` | default/inherited size |
| Acoustic Range | `<span>` | default/inherited size |
| 100Hz – 2.5kHz | `<span>` | default/inherited size |
| System Status | `<span>` | default/inherited size |
| Inspection Rate | `<span>` | default/inherited size |
| 1.2s / UNIT | `<span>` | default/inherited size |
| 02 | `<span>` | default/inherited size |

## Location: `sections\InspectionDemo.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| See the Intelligence | `<p>` | default/inherited size |
| What the AI actually sees. | `<h2>` | default/inherited size |
| ))} | `<div>` | default/inherited size |
| DEMO VISUALISATION · NOT REAL DATA | `<p>` | default/inherited size |
| BATCH ANALYSIS | `<p>` | default/inherited size |
| DEMO DATA | `<p>` | default/inherited size |
| AI CONFIDENCE | `<span>` | default/inherited size |
| 96.4% | `<span>` | default/inherited size |

## Location: `sections\InternalStructureExplorer.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Surface | `<span>` | default/inherited size |
| RADIUS | `<div>` | default/inherited size |
| ~42 mm | `<div>` | default/inherited size |

## Location: `sections\LMSDashboard.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Lab | `<span>` | default/inherited size |
| All experimental tools use simulated data until hardware integration is complete. | `<p>` | default/inherited size |

## Location: `sections\Pipeline.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Platform Architecture | `<p>` | default/inherited size |
| Hover or tap each stage to view details | `<p>` | default/inherited size |

## Location: `sections\PremiumHero.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Onion quality assessment | `<p>` | default/inherited size |
| Vision-led inspection with acoustic screening for smarter procurement decisions. | `<p>` | default/inherited size |
| Explore the system | `<button>` | default/inherited size |

## Location: `sections\Problem.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| The Problem | `<p>` | default/inherited size |
| Manual grading can produce inconsistent decisions, limited evidence, and disputes between procurement centres and suppliers. | `<p>` | default/inherited size |
| "What if every grading decision could be measured, explained and recorded?" | `<p>` | default/inherited size |

## Location: `sections\ProblemSection.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| PROCUREMENT INSPECTION REALITY (SIH26031) | `<span>` | default/inherited size |
| FAILS ON INTERNAL ROT. | `<span>` | default/inherited size |
| MVP BASELINE | `<span>` | default/inherited size |
| RGB Vision & Sizing Camera | `<h3>` | default/inherited size |
| 30% BLIND SPOT | `<span>` | default/inherited size |
| Risk: | `<strong>` | default/inherited size |
| KEY DIFFERENTIATOR | `<span>` | default/inherited size |
| Piezo Impulse Acoustic Sensor | `<h3>` | default/inherited size |
| NONDESTRUCTIVE | `<span>` | default/inherited size |
| Outcome: | `<strong>` | default/inherited size |

## Location: `sections\ReportShowcase.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| Grading at a glance. | `<h2>` | default/inherited size |
| Grade A | `<span>` | default/inherited size |
| Grade URS | `<span>` | default/inherited size |
| Manual Review | `<span>` | default/inherited size |
| Rejected | `<span>` | default/inherited size |

## Location: `sections\Scalability.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| SCALABILITY ROADMAP | `<span>` | default/inherited size |
| DESIGNED FOR A SYSTEM. | `<span>` | default/inherited size |

## Location: `sections\SignalTransformation.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| DSP SIGNAL TRANSFORMATION | `<span>` | default/inherited size |
| → FOURIER SPECTRUM. | `<span>` | default/inherited size |
| SOLENOID IMPULSE | `<span>` | default/inherited size |
| Raw pressure transient captured by contact piezo transducer preamplifier following 1.2 N solenoid tap. | `<p>` | default/inherited size |
| PEAK RESONANCE: 210 Hz | `<span>` | default/inherited size |
| Discrete Fourier Transform extracts fundamental resonant peaks, damping envelopes, and spectral centroids. | `<p>` | default/inherited size |
| DERIVED ACOUSTIC FEATURE VECTOR | `<h4>` | default/inherited size |
| DSP TELEMETRY | `<span>` | default/inherited size |

## Location: `sections\Solution.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| The Solution | `<p>` | default/inherited size |
| Our platform combines computer vision, calibrated size measurement and a configurable grading rule engine to standardise onion procurement decisions into a structured, reviewable process. | `<p>` | default/inherited size |
| DEMO VISUALISATION | `<p>` | default/inherited size |
| Computer vision detection overlay — illustrative | `<p>` | default/inherited size |

## Location: `sections\StandardsSection.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| PROCUREMENT POLICY MATRIX (SIH26031) | `<span>` | default/inherited size |
| POLICY ENGINE. | `<span>` | default/inherited size |
| AGMARK / URS POLICY ENGINE | `<span>` | default/inherited size |
| STARTING POLICY DEFAULTS | `<h3>` | default/inherited size |
| PARAMETER | `<th>` | default/inherited size |
| GRADE A THRESHOLD | `<th>` | default/inherited size |
| GRADE URS THRESHOLD | `<th>` | default/inherited size |
| * Note: Policy thresholds are editable per procurement hub and permanently logged in report metadata. | `<div>` | default/inherited size |
| DEFINITION | `<span>` | default/inherited size |
| UNDER RELAXED SPECIFICATION (URS) | `<h4>` | default/inherited size |
| URS (Under Relaxed Specification) | `<strong>` | default/inherited size |
| • Grade A = Target export/premium grade | `<p>` | default/inherited size |
| • Grade URS = Accepted for immediate processing | `<p>` | default/inherited size |
| • Rejected = Fails both Grade A & URS policy | `<p>` | default/inherited size |

## Location: `sections\SystemArchitecture.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| HARDWARE & SENSOR FUSION PIPELINE | `<span>` | default/inherited size |
| FUSION ENGINE. | `<span>` | default/inherited size |
| REQUIRED MVP | `<span>` | default/inherited size |
| RGB OPTICAL HARDWARE | `<h3>` | default/inherited size |
| KEY DIFFERENTIATOR | `<span>` | default/inherited size |
| SOLENOID ACOUSTIC BENCH | `<h3>` | default/inherited size |
| EDGE CONTROLLER | `<span>` | default/inherited size |
| RASPBERRY PI / URS POLICY | `<h3>` | default/inherited size |

## Location: `sections\TransparencyReport.tsx`

| Text Content | Tag | Sizing/Font Specification |
|---|---|---|
| AUDITABLE EVIDENCE TRAIL | `<span>` | default/inherited size |
| LEAVES A TRACE. | `<span>` | default/inherited size |
| INSTANT DELIVERABLE | `<span>` | default/inherited size |
| DIGITAL QUALITY AUDIT REPORT | `<h3>` | default/inherited size |
| SIH26031 CORE MVP | `<span>` | default/inherited size |

