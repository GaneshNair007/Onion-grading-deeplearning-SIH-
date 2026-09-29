import { motion, useInView } from 'framer-motion'
import { useRef, useState } from 'react'

// Generate mock FFT data with realistic peaks
const generateFFTData = () => {
  const data = []
  for (let i = 0; i < 64; i++) {
    let val = Math.random() * 15
    if (i > 12 && i < 22) val += Math.sin((i - 12) * Math.PI / 10) * 55
    if (i > 35 && i < 42) val += Math.sin((i - 35) * Math.PI / 7) * 35
    if (i > 50 && i < 55) val += Math.sin((i - 50) * Math.PI / 5) * 70
    data.push({
      freq: (i * 0.31).toFixed(1),
      amp: Math.max(4, val),
    })
  }
  return data
}

const data = generateFFTData()

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
}

export default function FFTVisualization() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: false, margin: '-60px' })

  return (
    <section ref={containerRef} className="relative w-full py-32 bg-bg-base overflow-hidden">
      {/* Background decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-pastel-sky/30 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: false, amount: 0.2 }}
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.12 } } }}
          className="text-center mb-20"
        >
          <motion.div variants={fadeUp} className="section-label mb-4">Spectral Analysis</motion.div>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-display font-semibold tracking-tight text-text-primary mb-6">
            From Sound to <span className="">Signal insight</span>
          </motion.h2>
          <motion.p variants={fadeUp} className="text-base text-text-secondary max-w-xl mx-auto leading-relaxed">
            The captured acoustic waveform is mathematically decomposed via Fast Fourier Transform into its constituent frequency components, exposing hidden structural signatures.
          </motion.p>
        </motion.div>

        {/* FFT Graph Card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false, amount: 0.15 }}
          transition={{ duration: 0.8 }}
          className="glass-card p-8 md:p-12"
        >
          {/* Graph Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-8 pb-4 border-b border-glass-border">
            <div>
              <h3 className="font-display text-xl font-semibold text-text-primary mb-1">Spectral signature</h3>
              <span className="text-sm text-text-muted font-sans">Fast Fourier Transform · frequency domain</span>
            </div>
            <div className="flex gap-4 mt-3 sm:mt-0">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-onion" />
                <span className="text-xs text-text-secondary font-sans font-medium">Signal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-pastel-lavender border border-purple-300" />
                <span className="text-xs text-text-secondary font-sans font-medium">Harmonics</span>
              </div>
            </div>
          </div>

          {/* Custom Bar Graph */}
          <div className="relative w-full h-[280px] md:h-[360px]">
            {/* Y-Axis */}
            <div className="absolute left-0 top-0 bottom-6 w-8 flex flex-col justify-between text-[10px] text-text-muted font-mono text-right pr-2">
              <span>100</span><span>75</span><span>50</span><span>25</span><span>0</span>
            </div>

            <div className="absolute left-10 right-0 top-0 bottom-6 border-l border-b border-glass-border flex items-end">
              {/* Grid lines */}
              <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="w-full border-t border-glass-border/30 h-0" />
                ))}
              </div>

              {/* Bars */}
              <div className="relative w-full h-full flex items-end justify-between px-0.5">
                {data.map((d, i) => {
                  const isHighPeak = d.amp > 50
                  return (
                    <div
                      key={i}
                      className="group relative flex-1 flex justify-center h-full items-end cursor-crosshair"
                      onMouseEnter={() => setHoveredIndex(i)}
                      onMouseLeave={() => setHoveredIndex(null)}
                    >
                      <motion.div
                        initial={{ height: 0 }}
                        animate={
                          isInView
                            ? {
                                height: [
                                  `${Math.max(4, d.amp * 0.7)}%`,
                                  `${Math.min(98, d.amp * 1.15)}%`,
                                  `${Math.max(5, d.amp * 0.85)}%`,
                                  `${Math.min(96, d.amp * 1.05)}%`,
                                  `${Math.max(4, d.amp * 0.7)}%`,
                                ],
                              }
                            : { height: 0 }
                        }
                        transition={{
                          duration: 2.2 + (i % 7) * 0.3,
                          repeat: Infinity,
                          ease: 'easeInOut',
                          delay: (i % 10) * 0.08,
                        }}
                        className={`w-[75%] rounded-t-sm transition-all duration-300 ${
                          hoveredIndex === i
                            ? 'bg-onion shadow-[0_0_16px_rgba(212,104,122,0.4)]'
                            : hoveredIndex !== null
                            ? 'bg-onion/15'
                            : isHighPeak
                            ? 'bg-gradient-to-t from-onion to-onion-deep/80'
                            : 'bg-onion/40 hover:bg-onion/60'
                        }`}
                      />

                      {/* Tooltip */}
                      {hoveredIndex === i && (
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 flex flex-col items-center pointer-events-none z-20">
                          <div className="glass-card !rounded-xl px-3 py-2 whitespace-nowrap shadow-blush !border-onion/15">
                            <div className="text-[9px] text-text-muted font-sans font-semibold uppercase tracking-wider mb-0.5">Frequency</div>
                            <div className="text-xs text-onion font-mono font-semibold">{d.freq} kHz</div>
                            <div className="text-[9px] text-text-muted font-sans font-semibold uppercase tracking-wider mt-1.5 mb-0.5">Amplitude</div>
                            <div className="text-xs text-text-primary font-mono font-semibold">{d.amp.toFixed(1)} dB</div>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* X-Axis */}
          <div className="ml-10 mt-2 flex justify-between text-[10px] text-text-muted font-mono">
            <span>0.0 kHz</span><span>5.0 kHz</span><span>10.0 kHz</span><span>15.0 kHz</span><span>20.0 kHz</span>
          </div>

          {/* Insight note */}
          <div className="mt-8 pt-6 border-t border-glass-border flex flex-col sm:flex-row gap-4 sm:gap-8">
            {[
              { label: 'Dominant Frequency', value: '~1.4 kHz', note: 'Characteristic of healthy tissue' },
              { label: 'Spectral Centroid', value: '~4.2 kHz', note: 'Indicates firmness score' },
              { label: 'Damping Coefficient', value: '0.032', note: 'Low = structurally sound' },
            ].map((item) => (
              <div key={item.label} className="flex-1 text-center sm:text-left">
                <div className="text-xs text-text-muted font-sans font-semibold uppercase tracking-wider mb-1">{item.label}</div>
                <div className="font-display text-2xl font-semibold text-text-primary">{item.value}</div>
                <div className="text-xs text-text-secondary mt-1">{item.note}</div>
              </div>
            ))}
          </div>
        </motion.div>


      </div>
    </section>
  )
}
