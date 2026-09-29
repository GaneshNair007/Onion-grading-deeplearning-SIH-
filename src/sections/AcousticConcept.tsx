import { motion } from 'framer-motion'
import { ArrowRight, Cpu } from 'lucide-react'

const steps = [
  { id: '01', label: 'EXCITATION', sub: 'Solenoid transient tap\n100 Hz – 2.5 kHz chirp' },
  { id: '02', label: 'TRANSMISSION', sub: 'Acoustic wave propagates\nthrough tunic & rings' },
  { id: '03', label: 'PIEZO PICKUP', sub: 'Contact microphone\ncaptures raw impulse' },
  { id: '04', label: 'PREAMP DSP', sub: 'High-pass filter & 24-bit\nADC digitization' },
  { id: '05', label: 'FOURIER FFT', sub: 'Discrete Fourier Transform\nspectral breakdown' },
  { id: '06', label: 'FEATURE MATH', sub: 'Resonant frequency peak\n& damping coefficient α' },
  { id: '07', label: 'FUSION CLASSIFY', sub: 'Random Forest model\nflags rot vs solid' },
]

export default function AcousticConcept() {
  return (
    <section id="acoustic" className="py-24 px-4 md:px-8 bg-ind-dark relative">
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
              PHYSICAL ACOUSTIC SCREENING
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="section-heading"
          >
            THE PHYSICS OF <br />
            <span className="text-sonar-cyan">READING STRUCTURAL STRUCTURAL RESONANCE.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="text-base md:text-lg text-text-sec leading-relaxed font-mono"
          >
            Controlled acoustic excitation probes internal structural density. Intact and internally compromised onions exhibit measurably distinct sound velocity (v = √(E/ρ)) and acoustic attenuation (α).
          </motion.p>
        </div>

        {/* Pipeline steps grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
          {steps.map((step, i) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false }}
              transition={{ delay: i * 0.08 }}
              className="relative"
            >
              <div className="hud-panel p-4 space-y-3 h-full border-white/10 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-lg font-bold text-sonar-cyan">{step.id}</span>
                  {i < steps.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-text-muted hidden lg:block" />
                  )}
                </div>
                <div>
                  <h4 className="font-mono text-xs font-bold text-white tracking-wider uppercase">{step.label}</h4>
                  <p className="text-[10px] text-text-sec font-mono leading-tight whitespace-pre-line mt-1">{step.sub}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Physics Formula Bench */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false }}
          className="hud-panel p-8 space-y-6 border-sonar-cyan/30 bg-ind-card"
        >
          <div className="flex items-center gap-3 border-b border-white/10 pb-4">
            <Cpu className="w-5 h-5 text-sonar-cyan" />
            <h4 className="font-mono text-xs font-bold tracking-widest text-sonar-cyan uppercase">BIO-ACOUSTIC MODEL · MATHEMATICAL FOUNDATION</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 font-mono text-xs">
            <div className="space-y-3 bg-ind-dark p-5 rounded-xl border border-white/10">
              <span className="text-sonar-cyan text-[10px] uppercase font-bold block">01 · SOUND VELOCITY & ELASTICITY</span>
              <p className="text-lg font-bold text-white">v = √(E / ρ)</p>
              <p className="text-text-sec text-[11px] leading-relaxed">
                Where E is Young&apos;s Modulus of elasticity of fleshy scales and ρ is tissue density (kg/m³). Fungal rot liquefies cell pectin, reducing E by 60%+ and slowing sound propagation.
              </p>
            </div>

            <div className="space-y-3 bg-ind-dark p-5 rounded-xl border border-white/10">
              <span className="text-amber-400 text-[10px] uppercase font-bold block">02 · ACOUSTIC IMPEDANCE BOUNDARY</span>
              <p className="text-lg font-bold text-white">Z = ρ · v</p>
              <p className="text-text-sec text-[11px] leading-relaxed">
                When sound hits internal rotten liquid pockets or air cavities, impedance mismatch (Z₁ ≠ Z₂) causes acoustic reflections, split double frequency peaks, and heavy signal decay (α).
              </p>
            </div>
          </div>
        </motion.div>

      </div>
    </section>
  )
}

