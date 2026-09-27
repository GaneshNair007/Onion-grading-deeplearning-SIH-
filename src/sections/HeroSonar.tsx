import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { useReducedMotion } from '../hooks/useReducedMotion'
import { ArrowRight, Volume2 } from 'lucide-react'
import { soundSynth } from '../utils/audioSynth'
import OnionLayerInspector from '../components/OnionLayerInspector'

/* ── HARDWARE ACOUSTIC WAVE CANVAS ── */
function HardwareAcousticCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const prefersReducedMotion = useReducedMotion()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationId: number
    let phase = 0

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const w = canvas.width
      const h = canvas.height
      const centerY = h / 2

      // Draw Oscilloscope Grid Lines
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.08)'
      ctx.lineWidth = 1

      for (let x = 0; x < w; x += 40) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, h)
        ctx.stroke()
      }
      for (let y = 0; y < h; y += 30) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(w, y)
        ctx.stroke()
      }

      // Draw Center Baseline
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.25)'
      ctx.beginPath()
      ctx.moveTo(0, centerY)
      ctx.lineTo(w, centerY)
      ctx.stroke()

      // Primary Acoustic Chirp Wave (Solid Resonant 210Hz)
      ctx.beginPath()
      ctx.strokeStyle = '#00E5FF'
      ctx.lineWidth = 2.5
      ctx.shadowColor = '#00E5FF'
      ctx.shadowBlur = 10

      for (let x = 0; x < w; x++) {
        const normX = x / w
        // Damping envelope
        const envelope = Math.exp(-normX * 2) * Math.sin(normX * Math.PI)
        const freq = 210
        const y = centerY + Math.sin(normX * freq * 0.1 - phase) * envelope * (h * 0.35)
        if (x === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.stroke()

      // Reset shadow
      ctx.shadowBlur = 0

      // Secondary Dampened Rot Wave (95Hz Damped)
      ctx.beginPath()
      ctx.strokeStyle = '#FF9F1C'
      ctx.lineWidth = 1.8

      for (let x = 0; x < w; x++) {
        const normX = x / w
        const envelope = Math.exp(-normX * 6) // Heavy decay
        const y = centerY + Math.sin(normX * 95 * 0.1 - phase * 0.5) * envelope * (h * 0.25)
        if (x === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.stroke()

      if (!prefersReducedMotion) {
        phase += 0.08
        animationId = requestAnimationFrame(render)
      }
    }

    render()

    return () => {
      cancelAnimationFrame(animationId)
    }
  }, [prefersReducedMotion])

  return (
    <div className="relative w-full h-44 bg-ind-dark rounded-2xl border border-white/10 overflow-hidden crt-scanlines">
      <canvas ref={canvasRef} width={600} height={176} className="w-full h-full block" />
      <div className="absolute top-3 left-4 flex items-center gap-3">
        <span className="tech-micro-badge">LIVE RESPONSE TRACE</span>
        <span className="font-mono text-[10px] text-sonar-cyan">SOLID RESPONSE · 210 Hz / ROT RESPONSE · 95 Hz</span>
      </div>
    </div>
  )
}

export default function HeroSonar() {
  const [pulseCount, setPulseCount] = useState(0)

  const handleImpactTest = () => {
    soundSynth.playChirp('solid')
    setPulseCount(p => p + 1)
  }

  return (
    <section className="relative min-h-screen pt-32 pb-20 px-4 md:px-8 sonar-grid-bg flex flex-col justify-between overflow-hidden">
      {/* Ambient Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-sonar-cyan/10 blur-[140px] pointer-events-none rounded-full" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-amber-500/10 blur-[140px] pointer-events-none rounded-full" />

      <div className="max-w-7xl mx-auto w-full space-y-16 relative z-10">
        {/* Top Hardware Banner Badge */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-ind-card border border-ind-border-bright shadow-lg shadow-black/50"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-sonar-cyan animate-pulse" />
          <span className="font-mono text-xs font-bold text-white tracking-widest uppercase">
             HARDWARE SPECIFICATION
          </span>
          <span className="h-3 w-px bg-white/20" />
          <span className="font-mono text-xs text-sonar-cyan tracking-wider">
            PIEZO RESPONSE + RGB VISION
          </span>
        </motion.div>

        {/* Hero Title & Subheading */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="lg:col-span-7 space-y-6"
          >
            <h1 className="hero-heading">
              ACOUSTIC <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-sonar-cyan via-teal-300 to-amber-400">
                STRUCTURAL RESONANCE
              </span> <br />
              SENSING.
            </h1>

            <p className="text-base md:text-lg text-text-sec font-mono leading-relaxed max-w-2xl">
              Non-destructive internal screening using controlled impulse response, contact acoustics and calibrated computer vision. Designed to surface potential internal defects without cutting the bulb.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={handleImpactTest}
                className="btn-primary-sci shadow-amber-glow"
              >
                <Volume2 size={16} /> TRIGGER SOLENOID TAP
              </button>

              <Link to="/prototype" className="btn-secondary-sci">
                OPEN HARDWARE BENCH <ArrowRight size={16} />
              </Link>
            </div>

            {/* Quick Spec Readouts */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-white/10 font-mono text-xs">
              <div>
                <span className="text-text-muted block text-[10px]">ACOUSTIC BAND</span>
                <span className="font-bold text-white text-sm">100Hz – 2.5kHz</span>
              </div>
              <div>
                <span className="text-text-muted block text-[10px]">INTERNAL-DEFECT SCREENING</span>
                <span className="font-bold text-sonar-cyan text-sm">PROTOTYPE · DFT</span>
              </div>
              <div>
                <span className="text-text-muted block text-[10px]">INSPECTION RATE</span>
                <span className="font-bold text-amber-400 text-sm">1.2 s / UNIT</span>
              </div>
            </div>
          </motion.div>

          {/* Right Live Wave Telemetry Box */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="lg:col-span-5 space-y-4"
          >
            <HardwareAcousticCanvas />

            <div className="hud-panel p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="text-text-sec">TRANSDUCER SIGNAL:</span>
                <span className="text-emerald-400 font-bold">PIEZO CONTACT · ACTIVE</span>
              </div>
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="text-text-sec">CONTROLLED IMPULSE:</span>
                <span className="text-sonar-cyan font-bold">{pulseCount} PINGS EXECUTED</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-sec">GRADE A / URS ENGINE:</span>
                <span className="text-amber-400 font-bold">POLICY MAPPED</span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Embedded Interactive Onion Cross-Section Inspector */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="pt-8"
        >
          <OnionLayerInspector />
        </motion.div>
      </div>
    </section>
  )
}
