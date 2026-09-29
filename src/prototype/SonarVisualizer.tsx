import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import TechLabel from '../components/TechLabel'
import { useReducedMotion } from '../hooks/useReducedMotion'

export default function SonarVisualizer() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)
  const reduced = useReducedMotion()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    let t = 0
    let sweep = 0

    function draw() {
      if (!ctx || !canvas) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const cx = canvas.width / 2
      const cy = canvas.height / 2

      // Rings
      for (let i = 1; i <= 5; i++) {
        ctx.beginPath()
        ctx.arc(cx, cy, i * 32, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(0,200,255,${0.1 - i * 0.015})`
        ctx.lineWidth = 1
        ctx.stroke()
      }

      // Cross hairs
      ctx.strokeStyle = 'rgba(0,200,255,0.08)'
      ctx.lineWidth = 0.5
      ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, canvas.height); ctx.stroke()
      ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(canvas.width, cy); ctx.stroke()

      // Sweep
      if (!reduced) {
        sweep += 0.025
        const g = ctx.createLinearGradient(cx, cy, cx + Math.cos(sweep) * 160, cy + Math.sin(sweep) * 160)
        g.addColorStop(0, 'rgba(0,200,255,0.25)')
        g.addColorStop(1, 'rgba(0,200,255,0)')

        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, 160, sweep - 0.7, sweep)
        ctx.closePath()
        ctx.fillStyle = g
        ctx.fill()
      }

      // Central onion orb
      const oR = 28
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, oR)
      grad.addColorStop(0, 'rgba(180,220,255,0.9)')
      grad.addColorStop(0.7, 'rgba(120,180,240,0.6)')
      grad.addColorStop(1, 'rgba(0,200,255,0.1)')
      ctx.beginPath()
      ctx.ellipse(cx, cy, oR, oR * 1.12, 0, 0, Math.PI * 2)
      ctx.fillStyle = grad
      ctx.fill()
      ctx.strokeStyle = 'rgba(0,200,255,0.5)'
      ctx.lineWidth = 1.5
      ctx.stroke()

      t += 0.02
      rafRef.current = requestAnimationFrame(draw)
    }

    if (!reduced) {
      draw()
    } else {
      draw()
    }

    return () => {
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [reduced])

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <TechLabel>ACOUSTIC SENSOR</TechLabel>
        <div className="flex items-center gap-2">
          <span className="dot-live" />
          <TechLabel cyan>ACTIVE</TechLabel>
        </div>
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="relative flex-1 rounded-sm border overflow-hidden"
        style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}
      >
        <canvas
          ref={canvasRef}
          className="w-full h-full min-h-[200px]"
        />
      </motion.div>
      <p className="text-[10px] mt-3 text-center" style={{ color: 'var(--text-sec)' }}>PROTOTYPE DATA</p>
    </div>
  )
}
