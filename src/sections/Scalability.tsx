import { motion } from 'framer-motion'
import GlassCard from '../components/GlassCard'
import { ArrowDown, Cpu, Factory, Smartphone } from 'lucide-react'

const progression = [
  {
    phase: 'LEVEL 1 — MOBILE PROTOTYPE',
    icon: Smartphone,
    desc: 'Smartphone camera + built-in speaker + mic. Zero added hardware cost for initial deployment.',
    status: 'CURRENT PROTOTYPE MVP',
    active: true,
  },
  {
    phase: 'LEVEL 2 — PROCUREMENT CENTRE STATION',
    icon: Cpu,
    desc: 'Dedicated procurement-centre capture station with guided tray imaging and acoustic chirp calibration.',
    status: 'NEAR-TERM EXPANSION',
    active: false,
  },
  {
    phase: 'LEVEL 3 — INDUSTRIAL CONVEYOR LINE',
    icon: Factory,
    desc: 'Conveyor belt integration with fixed high-speed cameras, piezo contact microphones, and automated mechanical sorting.',
    status: 'FUTURE INDUSTRIAL DIRECTION',
    active: false,
  },
]

export default function Scalability() {
  return (
    <section className="py-24 px-6 bg-app-bg relative">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Header */}
        <div className="space-y-4 max-w-3xl">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: false }}
            className="flex items-center gap-3"
          >
            <span className="w-8 h-0.5 bg-cyan-dark" />
            <span className="font-mono text-xs font-bold tracking-widest text-cyan-dark uppercase">
              SCALABILITY ROADMAP
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="section-heading"
          >
            BUILT FOR A SINGLE ONION. <br />
            <span className="text-cyan-dark">DESIGNED TO SCALE.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="text-lg md:text-xl text-text-sec leading-relaxed font-medium"
          >
            The software architecture starts on a zero-hardware phone prototype and scales seamlessly into high-throughput industrial conveyor sorting lines.
          </motion.p>
        </div>

        {/* Scalability Progression Cards */}
        <div className="max-w-4xl mx-auto space-y-6">
          {progression.map((item, i) => {
            const Icon = item.icon
            return (
              <div key={item.phase} className="space-y-6">
                <GlassCard delay={i * 0.1} className={`p-8 border-white ${item.active ? 'shadow-xl shadow-cyan-glow/10 border-cyan-dark/30' : ''}`}>
                  <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${item.active ? 'bg-cyan-dark text-white' : 'bg-surface-subtle text-graphite'}`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="tech-micro-badge">{item.status}</span>
                        <h3 className="font-mono text-base font-extrabold text-graphite uppercase tracking-wider mt-1">{item.phase}</h3>
                        <p className="text-xs text-text-sec font-medium mt-1">{item.desc}</p>
                      </div>
                    </div>
                  </div>
                </GlassCard>

                {i < progression.length - 1 && (
                  <div className="flex justify-center text-cyan-dark/40">
                    <ArrowDown className="w-6 h-6 animate-bounce" />
                  </div>
                )}
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}

