import { useEffect, useRef } from 'react'
import { ArrowDown } from 'lucide-react'

/* ── Live animated waveform + FFT bars ── */
function SignalDisplay() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    let raf: number
    let t = 0

    const draw = () => {
      const W = canvas.width = canvas.offsetWidth
      const H = canvas.height = canvas.offsetHeight
      ctx.clearRect(0, 0, W, H)
      t += 0.03

      const halfH = H / 2

      // ── Time-domain waveform (left half)
      ctx.beginPath()
      for (let x = 0; x < W * 0.48; x++) {
        const norm = x / (W * 0.48)
        const env  = Math.exp(-norm * 2.5) * Math.sin(norm * Math.PI)
        const y    = halfH + Math.sin(norm * 80 - t) * env * halfH * 0.7
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      }
      ctx.strokeStyle = 'rgba(0,200,224,0.7)'
      ctx.lineWidth   = 1.8
      ctx.stroke()

      // ── Centre divider
      ctx.beginPath()
      ctx.moveTo(W * 0.5, 8)
      ctx.lineTo(W * 0.5, H - 8)
      ctx.strokeStyle = 'rgba(27,29,36,0.08)'
      ctx.lineWidth   = 1
      ctx.setLineDash([4, 4])
      ctx.stroke()
      ctx.setLineDash([])

      // ── FFT frequency bars (right half)
      const barCount = 22
      const barW     = ((W * 0.46) / barCount) - 2
      for (let i = 0; i < barCount; i++) {
        const freq  = i / barCount
        const amp   = Math.exp(-((freq - 0.25) ** 2) / 0.04)
              + 0.3 * Math.exp(-((freq - 0.5) ** 2) / 0.02)
              + 0.18 * Math.sin(t * 0.5 + i * 0.4)
        const bH    = Math.max(4, amp * (H * 0.7))
        const bX    = W * 0.52 + i * ((W * 0.46) / barCount)
        const alpha = 0.35 + 0.45 * (amp / 1.5)

        ctx.fillStyle = `rgba(0,200,224,${Math.min(alpha, 0.85)})`
        ctx.fillRect(bX, H - bH - 4, barW, bH)
      }

      // Labels
      ctx.font = '9px "JetBrains Mono", monospace'
      ctx.fillStyle = 'rgba(98,104,117,0.6)'
      ctx.fillText('TIME DOMAIN', 8, 14)
      ctx.fillText('FREQUENCY DOMAIN', W * 0.52, 14)

      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <div className="glass rounded-2xl overflow-hidden" style={{ height: 180 }}>
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  )
}

/* ── Vertical signal flow — spec §14 ── */
const flow = [
  { label: 'ACOUSTIC EXCITATION', sub: 'Phone speaker chirp  100 Hz → 8 kHz' },
  { label: 'ONION RESPONSE',      sub: 'Structural resonance captured' },
  { label: 'MICROPHONE CAPTURE',  sub: 'Raw time-domain signal recorded' },
  { label: 'FFT / DSP',           sub: 'Fourier transform → frequency domain' },
  { label: 'ACOUSTIC SIGNATURE',  sub: 'Peak freq · decay rate · centroid' },
  { label: 'HIDDEN-DEFECT SCREEN',sub: 'Model flags → Manual Review or pass' },
]

export default function FeatureDetail() {
  return (
    <section id="how-it-works" className="section-pad bg-soft-cyan">
      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center max-w-xl mx-auto mb-16">
          <p className="tech-label text-cyan-acc mb-4">How the system works</p>
          <h2 className="text-graphite font-bold leading-tight" style={{ fontSize: 'clamp(2rem, 4vw, 3.5rem)' }}>
            Every onion has a measurable response.
          </h2>
          <p className="text-text-sec text-lg leading-relaxed mt-5">
            The camera measures the surface. A controlled acoustic response adds a second view of structural condition.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">

          {/* Left: signal flow */}
          <div className="space-y-0">
            {flow.map(({ label, sub }, i) => (
              <div key={label}>
                <div className="glass-sm px-5 py-4 flex items-center gap-4">
                  <div className="w-6 h-6 rounded-full bg-cyan-acc/15 flex items-center justify-center shrink-0">
                    <span className="text-cyan-acc text-[10px] font-bold">{i + 1}</span>
                  </div>
                  <div>
                    <p className="tech-label text-[10px] text-graphite">{label}</p>
                    <p className="text-text-sec text-xs mt-0.5">{sub}</p>
                  </div>
                </div>
                {i < flow.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ArrowDown size={14} className="text-cyan-acc/40" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Right: animated waveform display */}
          <div className="space-y-5">
            <SignalDisplay />

            {/* Spec data labels */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { k: 'Sampling rate',    v: '44.1 kHz' },
                { k: 'Dominant freq',    v: '~210 Hz (solid)' },
                { k: 'Spectral centroid',v: 'Prototype target' },
                { k: 'Damping',          v: 'Awaiting validation' },
              ].map(({ k, v }) => (
                <div key={k} className="glass-sm p-4">
                  <p className="tech-label text-[9px] mb-1">{k}</p>
                  <p className="font-mono text-sm font-semibold text-graphite">{v}</p>
                </div>
              ))}
            </div>

            <p className="text-text-sec text-xs text-center leading-relaxed px-4">
              Values marked “Prototype target” or “Awaiting validation” remain illustrative until experimental data is collected.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
