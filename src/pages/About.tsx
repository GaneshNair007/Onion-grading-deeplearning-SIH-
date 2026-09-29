import { motion } from 'framer-motion'
import { ArrowRight, CheckCircle2, Shield, Rocket, Settings, Zap, Target, Waves, Cpu, BarChart3, Camera, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
}

export default function About() {
  return (
    <main className="pt-28 pb-0 bg-bg-base min-h-screen text-text-primary selection:bg-onion/15">

      {/* ═══════ 1. Hero Header & Stat Strip ═══════ */}
      <section className="py-16 px-6 relative max-w-5xl mx-auto text-center">
        <motion.div initial="hidden" animate="visible" variants={stagger}>


          <motion.h1 variants={fadeUp} className="text-4xl md:text-6xl font-display font-semibold tracking-tight mb-6">
            Redefining Agricultural{' '}
            <span className="">Quality, Made Measurable.</span>
          </motion.h1>

          <motion.p variants={fadeUp} className="text-lg text-text-secondary font-sans leading-relaxed max-w-2xl mx-auto mb-10">
            Our AI-based vision and acoustic grading system is designed to bring objective, non-destructive quality assessment to the Indian onion supply chain — reducing waste, increasing trust, and enabling fair trade at every level.
          </motion.p>

          {/* Stat Strip */}
          <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-3 mb-16">
            {['Per-onion grading', 'mm-accurate sizing', 'Camera + acoustic', 'Instant audit-ready report'].map((stat, i) => (
              <div key={i} className="px-4 py-2 rounded-full bg-white border border-glass-border shadow-soft text-sm font-medium text-text-primary">
                {stat}
              </div>
            ))}
          </motion.div>

          <motion.div variants={fadeUp} className="w-full rounded-4xl overflow-hidden shadow-glass border border-glass-border">
            <img src="/image (2).jpg" alt="System Architecture Overview" className="w-full h-auto object-cover" />
          </motion.div>
        </motion.div>
      </section>

      {/* ═══════ 2. Two Ways to Grade an Onion ═══════ */}
      <section className="py-24 px-6 bg-bg-cream relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-pastel-lavender/30 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="max-w-6xl mx-auto relative z-10">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="text-center mb-16">
            <motion.div variants={fadeUp} className="section-label mb-4">Dual Pipeline</motion.div>
            <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary">
              Two Ways to Grade an Onion
            </motion.h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Vision Grading */}
            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.7 }} className="glass-card p-8 space-y-5 border border-pastel-sky/30 relative">
              <div className="flex items-center justify-between border-b border-glass-border pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-pastel-sky/30 flex items-center justify-center text-accent-info">
                    <Camera size={20} />
                  </div>
                  <h3 className="font-display text-xl font-semibold text-text-primary">Vision Grading</h3>
                </div>
                <span className="tag text-[10px] bg-bg-soft text-text-muted border border-glass-border">Tier 1 · Core</span>
              </div>
              <div className="tag tag-sage w-fit mb-4">Required · Every Batch</div>
              <div className="space-y-4">
                {[
                  'Detect every onion in the tray',
                  'Measure diameter via calibration marker',
                  'Flag visible damage, rot, sprouting',
                  'Apply Grade A / URS rule engine',
                ].map((step, i) => (
                  <div key={i} className="flex items-start gap-4">
                    <span className="w-6 h-6 rounded-full bg-pastel-sky/40 text-accent-info flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{i + 1}</span>
                    <p className="text-sm text-text-secondary leading-relaxed">{step}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Acoustic Grading */}
            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.7, delay: 0.15 }} className="glass-card p-8 space-y-5 border border-onion/10 relative">
              <div className="flex items-center justify-between border-b border-glass-border pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-onion-soft/30 flex items-center justify-center text-onion">
                    <Waves size={20} />
                  </div>
                  <h3 className="font-display text-xl font-semibold text-text-primary">Acoustic Grading</h3>
                </div>
                <span className="tag text-[10px] bg-bg-soft text-text-muted border border-glass-border">Tier 2 · Differentiator</span>
              </div>
              <div className="tag tag-pink w-fit mb-4">Optional · Catches Hidden Defects</div>
              <div className="space-y-4">
                {[
                  'Phone speaker emits chirp (100 Hz–8 kHz)',
                  'Phone mic records the echo',
                  'FFT extracts resonance + damping',
                  'Model flags internal rot invisible to camera',
                ].map((step, i) => (
                  <div key={i} className="flex items-start gap-4">
                    <span className="w-6 h-6 rounded-full bg-onion-soft/40 text-onion flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{i + 1}</span>
                    <p className="text-sm text-text-secondary leading-relaxed">{step}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Merge line into single result */}
          <div className="flex flex-col items-center">
            <div className="w-px h-8 bg-glass-border" />
            <motion.div initial={{ scale: 0.9, opacity: 0 }} whileInView={{ scale: 1, opacity: 1 }} viewport={{ once: true }} className="px-6 py-3 rounded-2xl bg-white border border-glass-border shadow-soft flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-accent-success" />
              <span className="font-semibold text-text-primary">Combined Grade + Confidence Score</span>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══════ 3. Grade A vs Grade URS ═══════ */}
      <section className="py-24 px-6 bg-bg-base relative">
        <div className="max-w-5xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="text-center mb-16">
            <motion.div variants={fadeUp} className="section-label mb-4">Quality Thresholds</motion.div>
            <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary">
              Configurable Specifications
            </motion.h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <motion.div initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="glass-card p-8 shadow-glass">
              <h3 className="font-display text-2xl font-semibold mb-6">Grade A</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2"><span className="font-medium">Diameter</span><span className="text-text-muted">45–65 mm</span></div>
                  <div className="h-2 w-full bg-bg-soft rounded-full overflow-hidden relative">
                    <div className="absolute left-[30%] right-[30%] h-full bg-accent-success rounded-full" />
                  </div>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-glass-border">
                  <span className="text-sm font-medium text-text-secondary">Visible Rot</span>
                  <span className="text-sm font-bold text-accent-warn">✕ Not allowed</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-glass-border">
                  <span className="text-sm font-medium text-text-secondary">Severe Damage</span>
                  <span className="text-sm font-bold text-accent-warn">✕ Not allowed</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-glass-border">
                  <span className="text-sm font-medium text-text-secondary">Sprouting</span>
                  <span className="text-sm font-bold text-accent-warn">✕ Not allowed</span>
                </div>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, x: 20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="glass-card p-8 border border-pastel-peach/40 shadow-glass">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-display text-2xl font-semibold">Grade URS</h3>
              </div>
              <p className="text-xs text-text-muted mb-6 italic">An accepted relaxed-quality tier — not a reject category</p>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2"><span className="font-medium">Diameter</span><span className="text-text-muted">35–70 mm</span></div>
                  <div className="h-2 w-full bg-bg-soft rounded-full overflow-hidden relative">
                    <div className="absolute left-[15%] right-[15%] h-full bg-accent-warn rounded-full" />
                  </div>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-glass-border">
                  <span className="text-sm font-medium text-text-secondary">Visible Rot</span>
                  <span className="text-sm font-bold text-accent-warn">✕ Not allowed</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-glass-border">
                  <span className="text-sm font-medium text-text-secondary">Severe Damage</span>
                  <span className="text-sm font-bold text-accent-warn">✕ Not allowed</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-glass-border">
                  <span className="text-sm font-medium text-text-secondary">Sprouting</span>
                  <span className="text-sm font-bold text-text-muted">Per active policy</span>
                </div>
              </div>
            </motion.div>
          </div>


        </div>
      </section>

      {/* ═══════ 4. Officer Workflow ═══════ */}
      <section className="py-24 px-6 bg-bg-base border-y border-glass-border relative overflow-hidden">
        {/* Subtle background blur blobs to enhance glass effect */}
        <div className="absolute top-1/2 left-1/4 w-[300px] h-[300px] bg-onion-soft/30 rounded-full blur-[100px] -translate-y-1/2 pointer-events-none" />
        <div className="absolute top-1/2 right-1/4 w-[250px] h-[250px] bg-pastel-sky/30 rounded-full blur-[90px] -translate-y-1/2 pointer-events-none" />
        
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-display font-semibold text-text-primary">The Officer's Workflow</h2>
          </div>
          
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-0 relative">
            <div className="hidden md:block absolute top-1/2 left-0 w-full h-px bg-glass-border -z-10" />
            {[
              'Create Batch', 'Select Policy', 'Capture Image', 'AI Analyzes', 
              'Rule Engine', 'Batch % Calc', 'Generate Report', 'Officer Reviews'
            ].map((step, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="flex flex-col items-center group relative glass-card p-4 rounded-2xl md:w-24 border border-white/50 hover:shadow-blush transition-all duration-300">
                <div className="w-8 h-8 rounded-full bg-white/80 backdrop-blur-sm border border-onion/20 text-onion font-bold flex items-center justify-center text-xs mb-3 shadow-soft group-hover:scale-110 group-hover:bg-onion group-hover:text-white transition-all duration-300">
                  {i + 1}
                </div>
                <span className="text-[11px] font-semibold text-text-secondary text-center leading-tight">{step}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════ 5. Computer Vision & Per-Onion Mockup ═══════ */}
      <section className="py-24 px-6 bg-bg-base relative">
        <div className="max-w-6xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="text-center mb-16">
            <motion.div variants={fadeUp} className="section-label mb-4">Core MVP</motion.div>
            <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary">
              Powered by <span className="">Computer Vision</span>
            </motion.h2>
          </motion.div>

          <div className="flex flex-col lg:flex-row gap-8">
            <div className="flex-1 grid md:grid-cols-2 gap-6">
              {[
                { title: 'Detection & Segmentation', desc: 'The YOLO vision model identifies each individual onion in a single tray, placing precise bounding boxes and segmentation masks.' },
                { title: 'Calibrated Size Measurement', desc: 'Using an in-frame calibration reference, the system calculates exact pixel-to-mm ratio, ensuring "undersized" is a real millimeter measurement.' },
                { title: 'Defect Classification', desc: 'The model analyzes the visible surface to flag damage, rot, and sprouting with dedicated confidence scores for every onion.' },
                { title: 'Configurable Rule Engine', desc: 'Runs measurements through a configurable engine tied to active Grade A / Grade URS policies. Identifies why an onion was graded a certain way.' },
                { title: 'Batch Percentages', desc: 'Automatically calculates Grade A, Grade URS, Rejected, and Manual Review percentages for the entire batch based on policy thresholds.' },
                { title: 'Instant Digital Report', desc: 'Generates an evidence-backed digital report with annotated images, per-onion reason codes, policy versions, and a verifiable audit trail.' },
              ].map((item, i) => (
                <motion.div key={item.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="glass-card rounded-2xl p-6 border border-glass-border">
                  <div className="w-8 h-8 rounded-lg bg-onion-soft/60 flex items-center justify-center text-onion mb-4">
                    <span className="font-mono font-bold text-sm">{i + 1}</span>
                  </div>
                  <h3 className="font-display text-lg font-semibold mb-2 text-text-primary">{item.title}</h3>
                  <p className="text-sm text-text-secondary leading-relaxed font-sans">{item.desc}</p>
                </motion.div>
              ))}
            </div>


          </div>
        </div>
      </section>



      {/* ═══════ 7. Reframed "Manual vs AI" ═══════ */}
      <section className="py-24 px-6 bg-bg-base relative overflow-hidden">
        <div className="max-w-5xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <div className="section-label mb-4">Comparison</div>
            <h2 className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary mb-4">
              A Paradigm Shift
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-card p-8 space-y-5">
              <div className="flex items-center justify-between border-b border-glass-border pb-4">
                <h3 className="font-display text-lg font-semibold text-text-muted">Manual Grading (Today)</h3>
                <span className="tag text-[10px] bg-bg-soft text-text-muted border border-glass-border">Status Quo</span>
              </div>
              {[
                'Subjective, inspector-dependent',
                'No measurement, only judgment',
                'No evidence trail',
                'High dispute rate',
              ].map((step, i) => (
                <div key={i} className="p-4 rounded-2xl bg-bg-soft text-text-secondary text-sm font-sans leading-relaxed flex items-start gap-3">
                  <span className="font-mono text-text-muted font-semibold text-xs mt-0.5">0{i + 1}</span>
                  {step}
                </div>
              ))}
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.15 }} className="glass-card p-8 space-y-5 !border-onion/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-br from-onion-soft/20 to-transparent pointer-events-none" />
              <div className="relative z-10">
                <div className="flex items-center justify-between border-b border-onion/10 pb-4">
                  <h3 className="font-display text-lg font-semibold text-onion-deep">AI-Assisted Grading (This System)</h3>
                  <span className="tag tag-pink text-[10px]">Evidence-Led</span>
                </div>
                {[
                  'Calibrated mm measurement, not a guess',
                  'Same policy applied identically at every centre',
                  'Every grade backed by reason codes + images',
                  'Acoustic layer catches what the eye can\'t',
                ].map((step, i) => (
                  <div key={i} className="p-4 rounded-2xl bg-white text-text-primary text-sm font-sans font-medium leading-relaxed flex items-center gap-3 border border-onion/5 shadow-soft">
                    <CheckCircle2 className="w-4 h-4 text-onion flex-shrink-0" />
                    {step}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══════ 8. Built for Operational Impact ═══════ */}
      <section className="py-24 px-6 bg-bg-cream">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary">
              Built for Operational Impact
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              { icon: Settings, title: 'Feasibility & Viability', desc: 'The system uses readily available components — built-in smartphone speakers and microphones, keeping the solution zero-added-hardware. The acoustic test runs locally on the mobile app, making it highly feasible for rapid deployment.', color: 'bg-pastel-sky/40', iconColor: 'text-accent-info' },
              { icon: Shield, title: 'Reliability & Robustness', desc: 'With noise-gated acquisition windows and baseline subtraction, our models isolate structural frequencies even in noisy mandi environments. The system is designed to flag uncertain classifications for human review rather than misclassify.', color: 'bg-pastel-lavender/40', iconColor: 'text-[#6B5BAD]' },
              { icon: FileText, title: 'Instant Verifiability', desc: 'By generating detailed digital reports with actual mm measurements and defect logic, we completely eliminate the ambiguity that causes post-transport disputes, providing an undeniable record.', color: 'bg-pastel-sage/40', iconColor: 'text-accent-success' },
              { icon: Rocket, title: 'Future Roadmap', desc: 'Beyond mobile inference, our roadmap includes integration with industrial conveyor sorting lines. The acoustic models are being expanded to assess firmness, water content, and disease in potatoes, apples, and other produce.', color: 'bg-pastel-peach/40', iconColor: 'text-accent-warn' },
            ].map((item, i) => (
              <motion.div key={item.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className={`${item.color} rounded-4xl p-10 border border-glass-border relative overflow-hidden group hover:shadow-glass transition-all duration-500`}>
                <div className={`w-12 h-12 rounded-2xl bg-white/80 backdrop-blur-sm flex items-center justify-center mb-6 ${item.iconColor} shadow-soft`}>
                  <item.icon size={22} />
                </div>
                <h3 className="font-display text-2xl font-semibold mb-4 text-text-primary">{item.title}</h3>
                <p className="text-text-secondary leading-[1.8] font-sans">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════ 9. Acoustic Technical Highlights ═══════ */}
      <section className="py-24 px-6 bg-bg-base">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <div className="section-label mb-4">Under the Hood</div>
            <h2 className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary">
              Acoustic Highlights
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Zap, title: 'Logarithmic Chirp', desc: 'The phone speaker emits a controlled logarithmic chirp (~100 Hz–8 kHz) to generate a reproducible acoustic impulse without additional hardware.' },
              { icon: Waves, title: 'FFT Spectral Analysis', desc: 'The response waveform is sampled at 44.1 kHz and transformed via a 1024-point FFT to extract dominant frequency, spectral centroid, and damping coefficient.' },
              { icon: Cpu, title: 'Lightweight ML Models', desc: 'A Random Forest or gradient-boosted regressor trained on labeled spectral samples flags likely internal defects in under 200ms per sample.' },
              { icon: Target, title: 'Decay Prediction', desc: 'Reframes acoustic and visual signals as a time-to-event regression, predicting the remaining days before a batch\'s grade is likely to drop.', tag: 'Stretch Goal' },
              { icon: Shield, title: 'Noise Robustness', desc: 'Adaptive noise gating and environmental baseline subtraction ensure reliable operation even in the acoustically chaotic environment of wholesale mandis.' },
              { icon: BarChart3, title: 'Mobile Inference', desc: 'The entire acoustic testing pipeline runs locally on-device as a zero-added-hardware solution, requiring no external mics or speakers.' },
            ].map((item, i) => (
              <motion.div key={item.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }} className="glass-card !rounded-3xl p-8 group hover:shadow-glass transition-all duration-500 relative">
                {item.tag && <div className="absolute top-4 right-4 tag tag-peach text-[10px]">{item.tag}</div>}
                <div className="w-10 h-10 rounded-xl bg-onion-soft/60 flex items-center justify-center text-onion mb-5 group-hover:scale-110 transition-transform">
                  <item.icon size={20} />
                </div>
                <h3 className="font-display text-lg font-semibold text-text-primary mb-2">{item.title}</h3>
                <p className="text-sm text-text-secondary leading-[1.75] font-sans">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>



      {/* ═══════ 11. Footer CTA ═══════ */}
      <section className="py-20 px-6 bg-bg-base text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-onion-soft/40 rounded-full blur-[140px] pointer-events-none" />
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="relative z-10">
          <h2 className="text-3xl font-display font-semibold tracking-tight text-text-primary mb-6">
            Experience it live.
          </h2>
          <Link to="/prototype" className="btn-onion">
            Open the Prototype Lab <ArrowRight size={16} />
          </Link>
        </motion.div>
      </section>
    </main>
  )
}
