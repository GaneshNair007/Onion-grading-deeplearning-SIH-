import { useEffect, useRef, useState } from 'react'

/* Animated counter hook */
function useCounter(target: number, duration = 1200, start = false) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!start) return
    let raf: number
    const startTime = performance.now()
    const tick = (now: number) => {
      const progress = Math.min((now - startTime) / duration, 1)
      setVal(Math.floor(progress * target))
      if (progress < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [start, target, duration])
  return val
}

const detections = [
  { grade: 'A',      mm: '57mm', col: '#35D07F', x: 10, y: 15, w: 90, h: 90 },
  { grade: 'A',      mm: '61mm', col: '#35D07F', x: 55, y: 8,  w: 85, h: 85 },
  { grade: 'A',      mm: '52mm', col: '#35D07F', x: 28, y: 45, w: 80, h: 80 },
  { grade: 'URS',    mm: '39mm', col: '#27C7E8', x: 68, y: 48, w: 72, h: 72 },
  { grade: 'REVIEW', mm: '--',   col: '#F2B84B', x: 42, y: 68, w: 76, h: 76 },
  { grade: 'A',      mm: '59mm', col: '#35D07F', x: 15, y: 70, w: 82, h: 82 },
  { grade: 'X',      mm: '--',   col: '#FF5D5D', x: 78, y: 70, w: 68, h: 68 },
]

const stats = [
  { label: 'TOTAL DETECTED', val: 48,  col: '#F4F7FA' },
  { label: 'GRADE A',        val: 31,  col: '#35D07F' },
  { label: 'URS',            val: 9,   col: '#27C7E8' },
  { label: 'REVIEW',         val: 4,   col: '#F2B84B' },
  { label: 'REJECTED',       val: 4,   col: '#FF5D5D' },
]

export default function InspectionDemo() {
  const ref = useRef<HTMLDivElement>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setInView(true) }, { threshold: 0.3 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])

  const c0 = useCounter(48, 1000, inView)
  const c1 = useCounter(31, 1200, inView)
  const c2 = useCounter(9,  1000, inView)
  const c3 = useCounter(4,  800,  inView)
  const c4 = useCounter(4,  800,  inView)
  const counts = [c0, c1, c2, c3, c4]

  return (
    <section id="intelligence" className="section-pad bg-[#091A2A] relative overflow-hidden">
      <div className="absolute inset-0 grid-overlay opacity-30 pointer-events-none" />

      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <p className="tech-label-cyan mb-4">See the assessment</p>
          <h2 className="text-off-white font-bold leading-[1.05]" style={{ fontSize: 'clamp(2rem, 4vw, 3.5rem)' }}>
            What the system actually sees.
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" ref={ref}>
          {/* Detection visual — 2 cols */}
          <div className="lg:col-span-2 tech-panel-bright relative overflow-hidden" style={{ aspectRatio: '16/9', minHeight: 320 }}>
            {/* Mock onion field */}
            <div className="absolute inset-0 bg-[#1a1000]">
              {/* Fake texture dots */}
              {Array.from({ length: 40 }).map((_, i) => (
                <div key={i} className="absolute w-1 h-1 rounded-full bg-[rgba(180,140,60,0.12)]"
                  style={{ left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%` }} />
              ))}
            </div>

            {/* Scan line */}
            <div className="scan-line" />

            {/* Detection boxes */}
            {detections.map((d, i) => (
              <div
                key={i}
                className="absolute"
                style={{ left: `${d.x}%`, top: `${d.y}%`, width: d.w, height: d.h }}
              >
                {/* Onion blob */}
                <div className="w-full h-full rounded-full bg-[rgba(120,80,20,0.45)] border border-[rgba(160,110,40,0.3)]" />
                {/* Detection border */}
                <div className="absolute inset-0 border" style={{ borderColor: d.col + '70' }} />
                {/* Label */}
                <div
                  className="absolute -top-6 left-0 px-1.5 py-px text-[8px] font-mono font-bold whitespace-nowrap"
                  style={{ background: d.col + '22', color: d.col, border: `1px solid ${d.col}55` }}
                >
                  {d.grade} {d.mm}
                </div>
              </div>
            ))}

            {/* Watermark */}
            <div className="absolute bottom-3 left-3">
              <p className="tech-label text-[8px] text-muted-blue/40">PROTOTYPE VISUALISATION · NOT VALIDATED DATA</p>
            </div>
          </div>

          {/* Stats panel */}
          <div className="tech-panel-bright flex flex-col">
            <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.07)]">
              <p className="tech-label-cyan text-[10px]">BATCH ANALYSIS</p>
              <p className="tech-label text-[9px] mt-0.5">PROTOTYPE DATA</p>
            </div>
            <div className="divide-y divide-[rgba(255,255,255,0.06)] flex-1">
              {stats.map((s, i) => (
                <div key={s.label} className="flex items-center justify-between px-6 py-4">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-sm" style={{ background: s.col }} />
                    <span className="tech-label text-[9px]">{s.label}</span>
                  </div>
                  <span className="font-mono font-bold text-xl" style={{ color: s.col }}>
                    {counts[i]}
                  </span>
                </div>
              ))}
            </div>
            <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.07)]">
              <div className="flex items-center justify-between mb-1">
                <span className="tech-label text-[9px]">MODEL CONFIDENCE</span>
                <span className="font-mono text-cyan font-bold">96.4%</span>
              </div>
              <div className="h-1 bg-[rgba(255,255,255,0.07)] rounded-full overflow-hidden">
                <div className="h-full bg-cyan transition-all duration-1000" style={{ width: inView ? '96.4%' : '0%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
