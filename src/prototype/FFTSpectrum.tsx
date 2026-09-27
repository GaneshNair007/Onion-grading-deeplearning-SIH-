import { useEffect, useRef } from 'react'
import TechLabel from '../components/TechLabel'
import { useReducedMotion } from '../hooks/useReducedMotion'

interface FFTSpectrumProps {
  isComplete: boolean
}

export default function FFTSpectrum({ isComplete }: FFTSpectrumProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)
  const reduced = useReducedMotion()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    let t = 0

    function draw() {
      if (!ctx || !canvas) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const barCount = 52
      const barW = (canvas.width / barCount) * 0.55
      const gap = (canvas.width / barCount) * 0.45

      for (let i = 0; i < barCount; i++) {
        const freq = i / barCount
        const peak = Math.exp(-Math.pow((i - 16) / 5, 2)) * 0.88
        const base = Math.max(0, 0.12 - freq * 0.08)
        const anim = isComplete ? 0 : Math.sin(t * 1.5 + i * 0.3) * 0.04
        const h = Math.max(4, (peak + base + anim) * canvas.height * 0.85)
        const x = i * (barW + gap) + gap / 2

        const isHighlight = i >= 13 && i <= 19
        const alpha = 0.1 + (peak + base) * 0.7 + (isHighlight && isComplete ? 0.2 : 0)

        ctx.fillStyle = isHighlight
          ? `rgba(0,200,255,${alpha + 0.1})`
          : `rgba(0,200,255,${alpha})`

        ctx.beginPath()
        ctx.roundRect(x, canvas.height - h, barW, h, 2)
        ctx.fill()

        if (isHighlight && isComplete) {
          ctx.fillStyle = 'rgba(0,200,255,0.95)'
          ctx.beginPath()
          ctx.roundRect(x, canvas.height - h - 3, barW, 2, 1)
          ctx.fill()
        }
      }

      // Axis
      ctx.strokeStyle = 'rgba(0,200,255,0.15)'
      ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(0, canvas.height - 1); ctx.lineTo(canvas.width, canvas.height - 1); ctx.stroke()

      // Labels
      ctx.font = '500 8px "JetBrains Mono", monospace'
      ctx.fillStyle = 'rgba(0,200,255,0.4)'
      const labels = ['100 Hz', '500 Hz', '2 kHz', '5 kHz', '8 kHz']
      labels.forEach((label, i) => {
        const x = (i / (labels.length - 1)) * (canvas.width - 30)
        ctx.fillText(label, x, canvas.height - 6)
      })

      if (isComplete) {
        // Label the resonance peak
        ctx.font = '600 9px "JetBrains Mono", monospace'
        ctx.fillStyle = 'rgba(0,200,255,0.8)'
        ctx.fillText('RESONANCE PEAK', (16 / 52) * canvas.width - 20, 14)
      }

      t += 0.025
    }

    if (!reduced) {
      if (isComplete) {
        draw()
      } else {
        const loop = () => { draw(); rafRef.current = requestAnimationFrame(loop) }
        rafRef.current = requestAnimationFrame(loop)
      }
    } else {
      draw()
    }

    return () => cancelAnimationFrame(rafRef.current)
  }, [isComplete, reduced])

  const features = [
    { label: 'DOMINANT FREQ', value: isComplete ? '~1.4 kHz' : '—', note: isComplete ? 'illustrative' : '' },
    { label: 'SPECTRAL CENTROID', value: '—', note: 'awaiting validation' },
    { label: 'PEAK AMPLITUDE', value: '—', note: 'awaiting validation' },
    { label: 'DAMPING RATE', value: '—', note: 'awaiting validation' },
  ]

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <TechLabel>FOURIER TRANSFORM · FREQUENCY SPECTRUM</TechLabel>
        {isComplete && <TechLabel cyan>SPECTRAL ANALYSIS COMPLETE</TechLabel>}
      </div>
      <div className="relative rounded-sm border overflow-hidden flex-1 mb-4" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
        <canvas
          ref={canvasRef}
          className="w-full h-full min-h-[140px]"
        />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {features.map((f) => (
          <div key={f.label} className="rounded-sm p-3 text-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border-dim)' }}>
            <TechLabel className="block text-[8px] mb-1">{f.label}</TechLabel>
            <span className="mono text-sm font-bold text-white">{f.value}</span>
            {f.note && <TechLabel className="block text-[7px] mt-1 opacity-50">{f.note}</TechLabel>}
          </div>
        ))}
      </div>
    </div>
  )
}
