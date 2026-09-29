import { motion } from 'framer-motion'
import { Beaker, Waves, Cpu, BarChart3, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
}

const labs = [
  {
    icon: Beaker,
    title: 'Acoustic Test Bench',
    desc: 'Live multimodal inspection bench — test acoustic resonance, FFT spectral analysis, and sensor fusion in real-time.',
    tag: 'Active Lab',
    tagClass: 'tag-pink',
    link: '/prototype',
    external: false,
  },
  {
    icon: Waves,
    title: 'Waveform Sandbox',
    desc: 'Experiment with live Web Audio solenoid impact chirps, live mic capture, and 52-bin frequency spectrum analysis.',
    tag: 'Live Audio & FFT',
    tagClass: 'tag-lavender',
    link: '/prototype',
    external: false,
  },
  {
    icon: Cpu,
    title: 'Vision Inference Playground',
    desc: 'Deep learning instance segmentation — YOLOv8s-seg defect classification, ArUco metric sizing, and instant audit PDF generation.',
    tag: 'YOLOv8 Lab (Port 5000)',
    tagClass: 'tag-peach',
    link: 'http://localhost:5000',
    external: true,
  },
  {
    icon: BarChart3,
    title: 'Batch Analytics Dashboard',
    desc: 'ONION-Q centre procurement kiosk — multi-camera capture, batch analytics, and government grade distribution compliance.',
    tag: 'ONION-Q Kiosk (Port 8000)',
    tagClass: 'tag-sage',
    link: 'http://localhost:8000/dashboard/app/index.html',
    external: true,
  },
]

export default function LMSDashboard() {
  return (
    <section className="relative w-full py-32 bg-bg-cream overflow-hidden">
      {/* Background */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-onion-soft/30 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-pastel-sky/30 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-6 relative z-10">
        {/* Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.12 } } }}
          className="mb-20"
        >
          <motion.div variants={fadeUp} className="section-label mb-4">Experimental</motion.div>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-display font-semibold tracking-tight text-text-primary mb-6">
            The <span className="">System lab</span>
          </motion.h2>
          <motion.p variants={fadeUp} className="text-lg text-text-secondary max-w-xl leading-relaxed">
            Hands-on tools to explore, test, and validate the acoustic intelligence pipeline. Some experiments are live — others are on the roadmap.
          </motion.p>
        </motion.div>

        {/* Lab Cards Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {labs.map((lab, i) => (
            <motion.div
              key={lab.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] }}
            >
              {lab.link ? (
                lab.external ? (
                  <a href={lab.link} target="_blank" rel="noopener noreferrer" className="block h-full">
                    <LabCard lab={lab} interactive />
                  </a>
                ) : (
                  <Link to={lab.link} className="block h-full">
                    <LabCard lab={lab} interactive />
                  </Link>
                )
              ) : (
                <LabCard lab={lab} />
              )}
            </motion.div>
          ))}
        </div>


      </div>
    </section>
  )
}

function LabCard({ lab, interactive = false }: { lab: typeof labs[0]; interactive?: boolean }) {
  const Icon = lab.icon
  return (
    <div className={`glass-card p-8 h-full flex flex-col group relative overflow-hidden transition-all duration-500 ${
      interactive
        ? 'cursor-pointer hover:shadow-blush hover:border-onion/15'
        : 'opacity-70 hover:opacity-90'
    }`}>
      {/* Shimmer on hover */}
      {interactive && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-onion-soft/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out pointer-events-none" />
      )}

      <div className="flex items-start justify-between mb-6 relative z-10">
        <div className="w-12 h-12 rounded-2xl bg-onion-soft/60 flex items-center justify-center text-onion">
          <Icon size={22} />
        </div>
        <div className={`tag ${lab.tagClass} text-[11px]`}>
          {lab.tag}
        </div>
      </div>

      <h3 className="font-display text-xl font-semibold text-text-primary mb-3 relative z-10">
        {lab.title}
      </h3>
      <p className="text-sm text-text-secondary leading-relaxed font-sans flex-1 relative z-10">
        {lab.desc}
      </p>

      {interactive && (
        <div className="mt-6 flex items-center gap-2 text-onion font-sans font-medium text-sm relative z-10 group-hover:gap-3 transition-all duration-300">
          Open Lab <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
        </div>
      )}
    </div>
  )
}
