import { motion } from 'framer-motion'

const fadeUp = {
  hidden: { opacity: 0, y: 40, transition: { duration: 0.35, ease: 'easeOut' } },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } },
}

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.15 } },
}

const steps = [
  {
    num: '01',
    title: 'The Solution',
    subtitle: 'Acoustic Intelligence',
    desc: "Our system uses the smartphone's built-in speaker to emit a controlled logarithmic chirp. The resulting acoustic response is captured by the phone's microphone and analyzed in real-time using Fast Fourier Transform (FFT) spectral analysis, revealing the internal structural integrity of each onion without cutting it open.",
    image: '/image-2.png',
    color: 'lavender',
    tag: 'Non-Destructive Testing',
    tagClass: 'tag-lavender',
  },
  {
    num: '02',
    title: 'The Analysis',
    subtitle: 'From Sound to Data',
    desc: 'Each onion produces a unique acoustic fingerprint. Healthy onions exhibit clean, high-frequency resonance patterns. Internally rotting ones produce dampened, irregular waveforms with lower spectral centroids. Our ML pipeline flags likely internal defects and predicts decay trajectories with high confidence.',
    image: '/image-3.png',
    color: 'peach',
    tag: 'Machine Learning',
    tagClass: 'tag-peach',
  },
  {
    num: '03',
    title: 'The Grading',
    subtitle: 'Policy-Compliant Output',
    desc: 'The AI model outputs a digital quality grade (Grade A, Grade URS, Rejected, Manual Review) fully aligned with active configurable procurement policies. Each assessment generates a tamper-proof digital audit report — providing objective, consistent, and verifiable quality documentation for the supply chain.',
    image: '/image-4.png',
    color: 'sage',
    tag: 'Digital Certification',
    tagClass: 'tag-sage',
  },
]

export default function CoreStorySequence() {
  return (
    <section className="relative bg-bg-cream py-32 overflow-hidden">
      {/* Background decorative blurs */}
      <div className="absolute top-20 right-0 w-[500px] h-[500px] bg-onion-soft/40 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-20 left-0 w-[400px] h-[400px] bg-pastel-lavender/30 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-6">
        {/* Section Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: false, amount: 0.15 }}
          variants={staggerContainer}
          className="text-center mb-24"
        >
          <motion.div variants={fadeUp} className="section-label mb-4">How It Works</motion.div>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-6xl font-display font-semibold tracking-tight text-text-primary mb-6">
            Peeling Back the{' '}
            <span className="">Inspection layers</span>
          </motion.h2>
          <motion.p variants={fadeUp} className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            A three-stage non-destructive inspection pipeline that transforms raw acoustic data into actionable quality intelligence.
          </motion.p>
        </motion.div>

        {/* Story Steps */}
        <div className="space-y-32">
          {steps.map((step, idx) => (
            <motion.div
              key={step.num}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: false, amount: 0.15 }}
              variants={staggerContainer}
              className={`grid md:grid-cols-2 gap-12 md:gap-16 items-center ${
                idx % 2 === 1 ? 'md:direction-rtl' : ''
              }`}
            >
              {/* Image Side */}
              <motion.div
                variants={fadeUp}
                className={`relative group ${idx % 2 === 1 ? 'md:order-2' : ''}`}
              >
                {/* Peel effect wrapper */}
                <div className="relative">
                  {/* Background peel layer (decorative) */}
                  <motion.div
                    animate={{ rotate: [2, 3.5, 2], scale: [1, 1.01, 1] }}
                    transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute inset-4 rounded-3xl bg-onion-soft/50 pointer-events-none"
                  />
                  <motion.div
                    animate={{ rotate: [-1, -2.5, -1], scale: [1, 1.01, 1] }}
                    transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
                    className="absolute inset-2 rounded-3xl bg-onion-light/30 pointer-events-none"
                  />
                  
                  {/* Main Image */}
                  <div className="relative rounded-3xl overflow-hidden border border-glass-border shadow-glass">
                    <img
                      src={step.image}
                      alt={step.title}
                      className="w-full h-auto object-cover transition-transform duration-700 group-hover:scale-[1.03]"
                    />
                    {/* Image overlay gradient */}
                    <div className="absolute inset-0 bg-gradient-to-t from-bg-base/20 to-transparent pointer-events-none" />

                    {/* Step 01: Looping acoustic chirp sonar pulse animation */}
                    {step.num === '01' && (
                      <div className="absolute top-[28%] left-[28%] pointer-events-none">
                        <motion.div
                          animate={{ scale: [1, 2.8, 3.8], opacity: [0.8, 0.3, 0] }}
                          transition={{ duration: 2.4, repeat: Infinity, ease: 'easeOut' }}
                          className="absolute -inset-4 rounded-full border-2 border-onion/60"
                        />
                        <motion.div
                          animate={{ scale: [1, 2.2, 3.2], opacity: [0.9, 0.4, 0] }}
                          transition={{ duration: 2.4, repeat: Infinity, ease: 'easeOut', delay: 0.8 }}
                          className="absolute -inset-4 rounded-full border border-onion-light/80"
                        />
                        <motion.div
                          animate={{ scale: [0.9, 1.25, 0.9], opacity: [0.8, 1, 0.8] }}
                          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                          className="w-4 h-4 rounded-full bg-onion shadow-[0_0_14px_rgba(184,80,66,0.9)]"
                        />
                      </div>
                    )}

                    {/* Step 02: Looping FFT live frequency equalizer */}
                    {step.num === '02' && (
                      <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-md rounded-2xl p-3 border border-white/20 flex items-center justify-between pointer-events-none">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                          <span className="text-[11px] font-mono font-medium text-white/90">FFT Resonance 2.4 kHz</span>
                        </div>
                        <div className="flex items-end gap-1 h-5">
                          {[40, 75, 100, 60, 85, 30, 95, 50].map((h, i) => (
                            <motion.div
                              key={i}
                              animate={{ height: [`${h * 0.3}%`, `${h}%`, `${h * 0.4}%`] }}
                              transition={{ duration: 1.2 + (i % 3) * 0.3, repeat: Infinity, ease: 'easeInOut' }}
                              className="w-1 bg-gradient-to-t from-peach to-amber-300 rounded-full"
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Step 03: Looping Audit Verified certification stamp */}
                    {step.num === '03' && (
                      <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-md rounded-2xl px-4 py-2 border border-emerald-500/30 shadow-glass flex items-center gap-2.5 pointer-events-none">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                          className="w-3.5 h-3.5 rounded-full border-2 border-emerald-600 border-t-transparent"
                        />
                        <span className="text-[11px] font-mono font-semibold text-emerald-800 tracking-wide">
                          GRADE A • AUDIT VERIFIED
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Step number floating badge */}
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut', delay: idx * 0.4 }}
                  className="absolute -top-4 -left-4 w-14 h-14 rounded-2xl bg-white shadow-blush flex items-center justify-center border border-onion/10 z-10"
                >
                  <span className="font-display text-xl font-semibold text-onion">{step.num}</span>
                </motion.div>
              </motion.div>

              {/* Text Side */}
              <motion.div
                variants={fadeUp}
                className={`flex flex-col ${idx % 2 === 1 ? 'md:order-1' : ''}`}
              >
                <div className={`tag ${step.tagClass} w-fit mb-6 flex items-center gap-2`}>
                  <motion.span
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-1.5 h-1.5 rounded-full bg-current"
                  />
                  {step.tag}
                </div>

                <h3 className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary mb-3">
                  {step.subtitle}
                </h3>

                <p className="text-base text-text-secondary leading-[1.8] font-sans">
                  {step.desc}
                </p>

                {/* Decorative line with looping pulse */}
                <div className="mt-8 flex items-center gap-3">
                  <div className="h-px flex-1 bg-gradient-to-r from-onion/20 to-transparent" />
                  <motion.div
                    animate={{ scale: [1, 1.6, 1], opacity: [0.6, 1, 0.6] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-2 h-2 rounded-full bg-onion-light"
                  />
                </div>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
