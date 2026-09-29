import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useReducedMotion } from '../hooks/useReducedMotion'
import { Activity, BarChart3, Radio } from 'lucide-react'

const techLabels = [
  { label: 'SAMPLING RATE', value: '44.1 kHz', note: 'STANDARD AUDIO MIC' },
  { label: 'DOMINANT FREQ', value: '1.42 kHz', note: 'PROTOTYPE RES' },
  { label: 'SPECTRAL CENTROID', value: '2.18 kHz', note: 'PROTOTYPE RES' },
  { label: 'PEAK AMPLITUDE', value: '0.84 dB', note: 'ILLUSTRATIVE' },
  { label: 'DAMPING RATE', value: '0.042 s⁻¹', note: 'PROTOTYPE RES' },
  { label: 'SIGNAL ENERGY', value: '84.2 %', note: 'PROTOTYPE RES' },
]

export default function SignalTransformation() {
  const waveRef = useRef<HTMLCanvasElement>(null)
  const fftRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)
  const reduced = useReducedMotion()

  useEffect(() => {
    const wc = waveRef.current
    const fc = fftRef.current
    if (!wc || !fc) return
    const wCtx = wc.getContext('2d')
    const fCtx = fc.getContext('2d')
    if (!wCtx || !fCtx) return

    const W = wc.offsetWidth
    const H = wc.offsetHeight
    wc.width = W; wc.height = H
    fc.width = fc.offsetWidth; fc.height = fc.offsetHeight

    let t = 0

    function drawWave() {
      if (!wCtx || !wc) return
      wCtx.clearRect(0, 0, wc.width, wc.height)
      const cy = wc.height / 2

      wCtx.strokeStyle = 'rgba(0, 200, 255, 0.08)'
      wCtx.lineWidth = 1
      for (let g = 1; g < 4; g++) {
        wCtx.beginPath()
        wCtx.moveTo(0, cy - (cy * g) / 4)
        wCtx.lineTo(wc.width, cy - (cy * g) / 4)
        wCtx.stroke()
        wCtx.beginPath()
        wCtx.moveTo(0, cy + (cy * g) / 4)
        wCtx.lineTo(wc.width, cy + (cy * g) / 4)
        wCtx.stroke()
      }

      const grad = wCtx.createLinearGradient(0, 0, wc.width, 0)
      grad.addColorStop(0, 'rgba(0,200,255,0.2)')
      grad.addColorStop(0.5, '#00C8FF')
      grad.addColorStop(1, 'rgba(124,103,254,0.4)')
      wCtx.strokeStyle = grad
      wCtx.lineWidth = 2
      wCtx.beginPath()

      for (let x = 0; x < wc.width; x++) {
        const progress = x / wc.width
        const freq = 1 + progress * 8
        const amp = 28 * Math.sin(progress * Math.PI)
        const y = cy + amp * Math.sin(progress * freq * Math.PI * 6 + t)
          + 8 * Math.sin(progress * freq * Math.PI * 18 + t * 1.7)
        if (x === 0) wCtx.moveTo(x, y)
        else wCtx.lineTo(x, y)
      }
      wCtx.stroke()

      wCtx.strokeStyle = 'rgba(0,200,255,0.2)'
      wCtx.lineWidth = 1
      wCtx.beginPath()
      wCtx.moveTo(0, cy)
      wCtx.lineTo(wc.width, cy)
      wCtx.stroke()
    }

    function drawFFT() {
      if (!fCtx || !fc) return
      fCtx.clearRect(0, 0, fc.width, fc.height)
      const barCount = 48
      const barW = (fc.width / barCount) * 0.6
      const gap = (fc.width / barCount) * 0.4

      for (let i = 0; i < barCount; i++) {
        const freq = i / barCount
        const peak = Math.exp(-Math.pow((i - 15) / 4, 2)) * 0.9
        const base = Math.max(0, 0.15 - freq * 0.1)
        const noise = reduced ? 0 : (Math.random() * 0.05)
        const h = (peak + base + noise) * fc.height * 0.82

        const alpha = 0.2 + (peak + base) * 0.7
        const isHighlight = i >= 13 && i <= 17

        fCtx.fillStyle = isHighlight
          ? '#00C8FF'
          : `rgba(0,200,255,${alpha})`

        const x = i * (barW + gap) + gap / 2
        fCtx.beginPath()
        fCtx.roundRect(x, fc.height - h, barW, h, 2)
        fCtx.fill()
      }

      fCtx.strokeStyle = 'rgba(0,200,255,0.2)'
      fCtx.lineWidth = 1
      fCtx.beginPath()
      fCtx.moveTo(0, fc.height - 1)
      fCtx.lineTo(fc.width, fc.height - 1)
      fCtx.stroke()
    }

    function loop() {
      drawWave()
      if (!reduced) drawFFT()
      t += 0.04
      rafRef.current = requestAnimationFrame(loop)
    }

    loop()
    return () => cancelAnimationFrame(rafRef.current)
  }, [reduced])

  return (
    <section className="py-24 px-4 md:px-8 bg-ind-dark relative">
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
              DSP SIGNAL TRANSFORMATION
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="section-heading"
          >
            TIME-DOMAIN WAVEFORM <br />
            <span className="text-sonar-cyan">→ FREQUENCY SPECTRUM.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            className="text-base md:text-lg text-text-sec leading-relaxed font-mono"
          >
            The raw piezo contact impulse response recorded in the time domain is transformed via Fast Fourier Transform (FFT) into a 256-bin frequency spectrum.
          </motion.p>
        </div>

        {/* Dual Canvas Panels */}
        <div className="grid lg:grid-cols-2 gap-8">
          
          {/* Time Domain */}
          <div className="hud-panel p-6 space-y-4 border-white/10">
            <div className="flex items-center justify-between font-mono text-xs border-b border-white/10 pb-3">
              <div className="flex items-center gap-2 text-sonar-cyan font-bold">
                <Radio className="w-4 h-4 animate-pulse" /> TIME DOMAIN WAVEFORM
              </div>
              <span className="text-text-sec">CONTROLLED IMPULSE</span>
            </div>
            <div className="relative rounded-xl bg-ind-dark p-2 overflow-hidden border border-white/10 crt-scanlines">
              <canvas ref={waveRef} className="w-full h-36" />
            </div>
            <p className="font-mono text-xs text-text-sec leading-relaxed">
              Raw response captured by the contact piezo transducer following a controlled solenoid impulse.
            </p>
          </div>

          {/* Frequency Domain */}
          <div className="hud-panel p-6 space-y-4 border-white/10">
            <div className="flex items-center justify-between font-mono text-xs border-b border-white/10 pb-3">
              <div className="flex items-center gap-2 text-sonar-cyan font-bold">
                <BarChart3 className="w-4 h-4" /> FREQUENCY DOMAIN (FFT)
              </div>
              <span className="text-emerald-400 font-bold">RESONANT PEAK · 210 Hz</span>
            </div>
            <div className="relative rounded-xl bg-ind-dark p-2 overflow-hidden border border-white/10 crt-scanlines">
              <canvas ref={fftRef} className="w-full h-36" />
            </div>
            <p className="font-mono text-xs text-text-sec leading-relaxed">
              Fourier analysis extracts resonant peaks, damping behaviour and spectral features used for acoustic screening.
            </p>
          </div>

        </div>

        {/* Feature Telemetry Readout Grid */}
        <div className="hud-panel p-8 space-y-6 border-white/10">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-sonar-cyan" />
              <h4 className="font-mono text-xs font-bold tracking-widest text-white uppercase">DERIVED ACOUSTIC FEATURE VECTOR</h4>
            </div>
            <span className="tech-micro-badge">DSP TELEMETRY</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6 font-mono">
            {techLabels.map((item) => (
              <div key={item.label} className="space-y-1 bg-ind-dark p-3 rounded-xl border border-white/10">
                <p className="text-[9px] font-bold tracking-widest text-text-muted uppercase">{item.label}</p>
                <p className="text-lg font-bold text-white">{item.value}</p>
                <p className="text-[9px] font-semibold text-sonar-cyan">{item.note}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  )
}

