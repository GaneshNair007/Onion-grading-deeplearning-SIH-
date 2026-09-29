import { motion, useInView } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'
import { CheckCircle2 } from 'lucide-react'

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
}

export default function AIGradingReveal() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: true, margin: '-20%' })

  const [progress, setProgress] = useState(0)
  const [analyzing, setAnalyzing] = useState(true)

  const [firmness, setFirmness] = useState(0)
  const [integrity, setIntegrity] = useState(0)
  const [health, setHealth] = useState(0)

  useEffect(() => {
    if (isInView && analyzing) {
      const interval = setInterval(() => {
        setProgress(p => {
          if (p >= 100) {
            clearInterval(interval)
            setTimeout(() => setAnalyzing(false), 500)
            return 100
          }
          return p + 2
        })
      }, 30)
      return () => clearInterval(interval)
    }
  }, [isInView, analyzing])

  useEffect(() => {
    if (!analyzing) {
      const duration = 1500
      const steps = 60
      const stepTime = duration / steps
      let currentStep = 0

      const timer = setInterval(() => {
        currentStep++
        const ease = 1 - Math.pow(1 - currentStep / steps, 3)
        setFirmness(Math.round(ease * 92))
        setIntegrity(Math.round(ease * 88))
        setHealth(Math.round(ease * 96))

        if (currentStep >= steps) clearInterval(timer)
      }, stepTime)

      return () => clearInterval(timer)
    }
  }, [analyzing])

  return (
    <section ref={containerRef} className="relative w-full py-32 bg-bg-base overflow-hidden">
      {/* Background */}
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-pastel-sage/30 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.12 } } }}
          className="text-center mb-20"
        >
          <motion.div variants={fadeUp} className="section-label mb-4">AI Classification</motion.div>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-display font-semibold tracking-tight text-text-primary mb-6">
            Intelligent <span className="">Grading</span>
          </motion.h2>
          <motion.p variants={fadeUp} className="text-base text-text-secondary max-w-xl mx-auto leading-relaxed">
            The trained model processes the spectral signature in real-time and delivers an objective quality assessment aligned with AGMARK standards.
          </motion.p>
        </motion.div>

        {/* Grading Visualization */}
        <div className="relative w-full max-w-lg mx-auto">
          {analyzing ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <div className="relative w-48 h-48 flex items-center justify-center mb-8">
                <svg className="w-full h-full -rotate-90">
                  <circle cx="96" cy="96" r="88" className="fill-none" stroke="rgba(212, 104, 122, 0.1)" strokeWidth="3" />
                  <motion.circle
                    cx="96" cy="96" r="88"
                    className="fill-none"
                    stroke="#D4687A"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeDasharray="553"
                    strokeDashoffset={553 - (553 * progress) / 100}
                  />
                </svg>
                <div className="absolute font-display text-3xl font-semibold text-text-primary">
                  {progress}%
                </div>
              </div>
              <p className="section-label animate-pulse-soft">Reading spectral signature…</p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="glass-card p-10 md:p-12 flex flex-col items-center"
            >
              <div className="flex items-center gap-2 text-accent-success mb-6">
                <CheckCircle2 size={16} />
                <span className="text-xs font-sans font-semibold uppercase tracking-[0.15em] text-accent-success">Assessment complete</span>
              </div>

              {/* The Grade */}
              <div className="text-center mb-10">
                <div className="text-xs text-text-muted font-sans font-semibold uppercase tracking-[0.2em] mb-3">Quality assessment</div>
                <motion.div
                  initial={{ opacity: 0, y: 20, filter: 'blur(12px)' }}
                  animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                  transition={{ delay: 0.2, duration: 1 }}
                  className="text-8xl font-display font-bold text-text-primary mb-3"
                >
                  A
                </motion.div>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1, duration: 1 }}
                  className="tag tag-sage w-fit mx-auto"
                >
                  <CheckCircle2 size={12} />
                  Premium Quality — Export Ready
                </motion.div>
              </div>

              {/* Stat Bars */}
              <div className="w-full space-y-5 border-t border-glass-border pt-8">
                {[
                  { label: 'Structural Firmness', val: firmness, target: 92 },
                  { label: 'Layer Integrity', val: integrity, target: 88 },
                  { label: 'Internal Health Score', val: health, target: 96 },
                ].map((stat) => (
                  <div key={stat.label} className="flex flex-col gap-2">
                    <div className="flex justify-between items-end">
                      <span className="text-sm text-text-secondary font-sans font-medium">{stat.label}</span>
                      <span className="text-sm text-text-primary font-mono font-semibold">{stat.val}%</span>
                    </div>
                    <div className="w-full h-2 bg-onion-soft rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${stat.val}%` }}
                        transition={{ duration: 0.1 }}
                        className="h-full bg-gradient-to-r from-onion-light to-onion rounded-full"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  )
}
