import { useEffect, useRef } from 'react'
import TechLabel from '../components/TechLabel'
import { useReducedMotion } from '../hooks/useReducedMotion'

interface MicrophoneFeedProps {
  isRecording: boolean
}

export default function MicrophoneFeed({ isRecording }: MicrophoneFeedProps) {
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
      const cy = canvas.height / 2

      // Grid
      ctx.strokeStyle = 'rgba(0,200,255,0.05)'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(0, cy - 20); ctx.lineTo(canvas.width, cy - 20)
      ctx.moveTo(0, cy + 20); ctx.lineTo(canvas.width, cy + 20)
      ctx.stroke()

      // Axis
      ctx.strokeStyle = 'rgba(0,200,255,0.15)'
      ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(canvas.width, cy); ctx.stroke()

      if (isRecording) {
        const grad = ctx.createLinearGradient(0, 0, canvas.width, 0)
        grad.addColorStop(0, 'rgba(0,200,255,0.2)')
        grad.addColorStop(0.5, 'rgba(0,200,255,0.95)')
        grad.addColorStop(1, 'rgba(0,200,255,0.2)')
        ctx.strokeStyle = grad
        ctx.lineWidth = 1.5
        ctx.beginPath()
        for (let x = 0; x < canvas.width; x++) {
          const phase = (x / canvas.width) * Math.PI * 2
          const env = Math.sin(phase)
          const y = cy + env * (16 + 12 * Math.sin(x * 0.06 + t * 3.5)) + 4 * Math.sin(x * 0.18 + t * 5)
          x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.stroke()
      } else {
        // Flat / noise floor
        ctx.strokeStyle = 'rgba(0,200,255,0.25)'
        ctx.lineWidth = 1
        ctx.beginPath()
        for (let x = 0; x < canvas.width; x++) {
          const noise = (Math.random() - 0.5) * 4
          x === 0 ? ctx.moveTo(x, cy + noise) : ctx.lineTo(x, cy + noise)
        }
        ctx.stroke()
      }

      t += 0.03
      rafRef.current = requestAnimationFrame(draw)
    }

    if (!reduced || isRecording) draw()
    return () => cancelAnimationFrame(rafRef.current)
  }, [isRecording, reduced])

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <TechLabel>ACOUSTIC INPUT</TechLabel>
        <div className="flex items-center gap-2">
          {isRecording ? (
            <><span className="dot-live" /><TechLabel cyan>CAPTURING RESPONSE</TechLabel></>
          ) : (
            <><span className="dot-idle" /><TechLabel>STANDBY</TechLabel></>
          )}
        </div>
      </div>
      <div className="relative rounded-sm border overflow-hidden flex-1 mb-4" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
        <canvas
          ref={canvasRef}
          className="w-full h-full min-h-[140px]"
        />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'SAMPLE RATE', value: '44.1 kHz' },
          { label: 'DURATION', value: isRecording ? '02.4s' : '--' },
          { label: 'NOISE FLOOR', value: isRecording ? '-84 dB' : '--' },
        ].map((item) => (
          <div key={item.label} className="rounded-sm p-3 text-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border-dim)' }}>
            <TechLabel className="block text-[8px] mb-1">{item.label}</TechLabel>
            <span className="mono text-xs font-bold text-white">{item.value}</span>
          </div>
        ))}
      </div>
      <p className="text-[10px] mt-4 text-center" style={{ color: 'var(--text-sec)' }}>PROTOTYPE DATA</p>
    </div>
  )
}
