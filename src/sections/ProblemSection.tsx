import { motion } from 'framer-motion'
import { Eye, Radio } from 'lucide-react'

export default function ProblemSection() {
  return (
    <section id="problem" className="py-24 px-4 md:px-8 relative bg-ind-dark">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Header */}
        <div className="space-y-4 max-w-3xl">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: false }}
            className="flex items-center gap-3 font-mono text-xs"
          >
            <span className="w-8 h-0.5 bg-sonar-cyan" />
            <span className="font-bold tracking-widest text-sonar-cyan uppercase">
              PROCUREMENT INSPECTION REALITY ()
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="section-heading"
          >
            EXTERNAL VISION ALONE <br />
            <span className="text-amber-400">BLIND TO INTERNAL CONDITION.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="text-base md:text-lg text-text-sec leading-relaxed font-mono"
          >
            Manual inspectors and basic RGB camera systems can only measure surface defects, tunic color, and diameter. They are completely blind to hidden neck rot, internal hollow heart, and center spongy decay.
          </motion.p>
        </div>

        {/* Dual Hardware Bench Comparison */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Bench 1: Computer Vision Only */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="hud-panel p-8 space-y-6 border-white/10"
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-ind-panel border border-white/10 flex items-center justify-center text-text-muted">
                  <Eye size={20} />
                </div>
                <div>
                  <span className="font-mono text-[10px] text-text-sec uppercase font-bold block">MVP BASELINE</span>
                  <h3 className="font-mono text-lg font-bold text-white">RGB vision + size calibration</h3>
                </div>
              </div>
              <span className="amber-micro-badge">SURFACE-ONLY LIMIT</span>
            </div>

            <ul className="space-y-3 font-mono text-xs text-text-sec">
              <li className="flex items-center gap-3 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Measures outer diameter ($mm$) & skin color
              </li>
              <li className="flex items-center gap-3 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Flags visible surface rot & sprouting
              </li>
              <li className="flex items-center gap-3 text-red-400">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> BLIND to internal neck rot under dry tunic
              </li>
              <li className="flex items-center gap-3 text-red-400">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Cannot measure interior tissue turgor or hollowness
              </li>
            </ul>

            <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 font-mono text-xs text-red-300">
              <strong>Risk:</strong> Rot-infected onions pass external grading, entering mandi cold storage where rot spreads to adjacent healthy lots.
            </div>
          </motion.div>

          {/* Bench 2: Acoustic Impulse Integration */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ delay: 0.15 }}
            className="hud-panel p-8 space-y-6 border-sonar-cyan/40 bg-ind-card"
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-sonar-cyan/10 border border-sonar-cyan/40 flex items-center justify-center text-sonar-cyan">
                  <Radio size={20} />
                </div>
                <div>
                  <span className="font-mono text-[10px] text-sonar-cyan uppercase font-bold block">KEY DIFFERENTIATOR</span>
                  <h3 className="font-mono text-lg font-bold text-white">Acoustic impulse screening</h3>
                </div>
              </div>
              <span className="tech-micro-badge">NON-DESTRUCTIVE</span>
            </div>

            <ul className="space-y-3 font-mono text-xs text-text-sec">
              <li className="flex items-center gap-3 text-sonar-cyan">
                <span className="w-1.5 h-1.5 rounded-full bg-sonar-cyan" /> Solenoid transient impact triggers acoustic chirp
              </li>
              <li className="flex items-center gap-3 text-sonar-cyan">
                <span className="w-1.5 h-1.5 rounded-full bg-sonar-cyan" /> Piezo contact mic records structural impulse response
              </li>
              <li className="flex items-center gap-3 text-sonar-cyan">
                <span className="w-1.5 h-1.5 rounded-full bg-sonar-cyan" /> Real-time FFT spectrum identifies dampening & rot peaks
              </li>
              <li className="flex items-center gap-3 text-sonar-cyan">
                <span className="w-1.5 h-1.5 rounded-full bg-sonar-cyan" /> 100% Nondestructive — onion remains 100% intact
              </li>
            </ul>

            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 font-mono text-xs text-emerald-300">
              <strong>Outcome:</strong> Complete dual-modal inspection. Computer vision grades surface features while acoustics audit interior structural integrity.
            </div>
          </motion.div>
        </div>

      </div>
    </section>
  )
}

