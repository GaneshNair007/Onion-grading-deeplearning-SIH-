import { motion } from 'framer-motion'

const fadeUp = {
  hidden: { opacity: 0, y: 50 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
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
          viewport={{ once: true, margin: '-80px' }}
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
              viewport={{ once: true, margin: '-100px' }}
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
                  <div className="absolute inset-4 rounded-3xl bg-onion-soft/50 transform rotate-2 group-hover:rotate-3 transition-transform duration-700" />
                  <div className="absolute inset-2 rounded-3xl bg-onion-light/30 transform -rotate-1 group-hover:-rotate-2 transition-transform duration-700" />
                  
                  {/* Main Image */}
                  <div className="relative rounded-3xl overflow-hidden border border-glass-border shadow-glass">
                    <img
                      src={step.image}
                      alt={step.title}
                      className="w-full h-auto object-cover transition-transform duration-700 group-hover:scale-[1.03]"
                    />
                    {/* Image overlay gradient */}
                    <div className="absolute inset-0 bg-gradient-to-t from-bg-base/20 to-transparent pointer-events-none" />
                  </div>
                </div>

                {/* Step number floating badge */}
                <div className="absolute -top-4 -left-4 w-14 h-14 rounded-2xl bg-white shadow-blush flex items-center justify-center border border-onion/10 z-10">
                  <span className="font-display text-xl font-semibold text-onion">{step.num}</span>
                </div>
              </motion.div>

              {/* Text Side */}
              <motion.div
                variants={fadeUp}
                className={`flex flex-col ${idx % 2 === 1 ? 'md:order-1' : ''}`}
              >
                <div className={`tag ${step.tagClass} w-fit mb-6`}>
                  {step.tag}
                </div>

                <h3 className="text-3xl md:text-4xl font-display font-semibold tracking-tight text-text-primary mb-3">
                  {step.subtitle}
                </h3>

                <p className="text-base text-text-secondary leading-[1.8] font-sans">
                  {step.desc}
                </p>

                {/* Decorative line */}
                <div className="mt-8 flex items-center gap-3">
                  <div className="h-px flex-1 bg-gradient-to-r from-onion/20 to-transparent" />
                  <div className="w-2 h-2 rounded-full bg-onion-light" />
                </div>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
