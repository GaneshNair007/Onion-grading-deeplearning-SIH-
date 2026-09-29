import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'

/* ── Live inspection UI panel (spec §8.1 right side) ── */
const onions = [
  { id: '01', grade: 'GRADE A',   mm: '57.2 mm', color: '#35D07F', delay: 800  },
  { id: '02', grade: 'URS',       mm: '38.7 mm', color: '#27C7E8', delay: 1200 },
  { id: '03', grade: 'GRADE A',   mm: '52.1 mm', color: '#35D07F', delay: 1600 },
  { id: '04', grade: 'REVIEW',    mm: '--',       color: '#F2B84B', delay: 2000 },
  { id: '05', grade: 'GRADE A',   mm: '61.3 mm', color: '#35D07F', delay: 2400 },
]

function InspectionPanel({ loaded }: { loaded: boolean }) {
  const [revealed, setRevealed] = useState<number[]>([])

  useEffect(() => {
    if (!loaded) return
    onions.forEach((o, i) => {
      const t = setTimeout(() => setRevealed(prev => [...prev, i]), o.delay)
      return () => clearTimeout(t)
    })
  }, [loaded])

  return (
    <div className="tech-panel-bright relative overflow-hidden w-full max-w-[380px] mx-auto lg:mx-0">
      {/* Scanning line */}
      {loaded && <div className="scan-line" />}

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-[rgba(255,255,255,0.08)]">
        <div>
          <p className="tech-label-cyan text-[10px]">LIVE INSPECTION</p>
          <p className="tech-label text-[9px] mt-0.5">ONION QUALITY SYSTEM · V1.0</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-success dot-online" />
          <span className="tech-label text-[9px] text-success">ACTIVE</span>
        </div>
      </div>

      {/* Onion rows */}
      <div className="divide-y divide-[rgba(255,255,255,0.06)]">
        {onions.map((o, i) => (
          <div
            key={o.id}
            className={`flex items-center gap-4 px-5 py-3.5 transition-all duration-500 ${revealed.includes(i) ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-3'}`}
          >
            <div className="w-7 h-7 rounded-full border flex items-center justify-center shrink-0" style={{ borderColor: o.color + '55', background: o.color + '18' }}>
              <span className="font-mono text-[9px] font-bold" style={{ color: o.color }}>{o.id}</span>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-xs tracking-wide text-off-white">{o.grade}</p>
              <p className="tech-label text-[9px]">{o.mm}</p>
            </div>
            <div className="w-2 h-2 rounded-full" style={{ background: o.color }} />
          </div>
        ))}
      </div>

      {/* Footer confidence */}
      <div className="px-5 py-3 border-t border-[rgba(255,255,255,0.08)] flex items-center justify-between">
        <span className="tech-label text-[9px]">MODEL CONFIDENCE</span>
        <span className="font-mono text-cyan font-bold text-sm">96.4%</span>
      </div>
    </div>
  )
}

/* ── System status strip (spec §8.2) ── */
const statusItems = [
  { label: 'SYSTEM STATUS',  val: 'ONLINE',  color: '#35D07F' },
  { label: 'VISION ENGINE',  val: 'ACTIVE',  color: '#35D07F' },
  { label: 'CALIBRATION',    val: 'READY',   color: '#27C7E8' },
  { label: 'POLICY',         val: 'ACTIVE',  color: '#27C7E8' },
]

export default function Hero() {
  const [loaded, setLoaded] = useState(false)
  useEffect(() => { const t = setTimeout(() => setLoaded(true), 120); return () => clearTimeout(t) }, [])

  const reveal = (delay: number): React.CSSProperties => ({
    opacity: loaded ? 1 : 0,
    transform: loaded ? 'translateY(0)' : 'translateY(22px)',
    transition: `opacity 0.8s ease ${delay}ms, transform 0.8s cubic-bezier(0.16,1,0.3,1) ${delay}ms`,
  })

  return (
    <section className="relative min-h-screen flex flex-col overflow-hidden">
      {/* Background video + dark overlay */}
      <div className="absolute inset-0">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover object-center"
        >
          <source src="/hero_video.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-r from-navy/95 via-navy/80 to-navy/50" />
        <div className="absolute inset-0 bg-gradient-to-t from-navy/70 via-transparent to-navy/30" />
        {/* Grid overlay */}
        <div className="absolute inset-0 grid-overlay opacity-60" />
      </div>

      {/* Corner badge (spec §8.2) */}
      <div className="absolute top-24 right-6 md:right-10 z-10" style={reveal(1600)}>
        <div className="tech-panel px-3 py-2 text-right">
          <p className="font-mono text-[10px] text-muted-blue">01</p>
          <p className="tech-label-cyan text-[10px]">AI INSPECTION SYSTEM</p>
        </div>
      </div>

      {/* Main content */}
      <div className="relative z-10 flex-1 flex items-center max-w-8xl mx-auto w-full px-6 md:px-10 pt-28 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 w-full items-center">

          {/* Left — 7 cols */}
          <div className="lg:col-span-7">
            <p className="tech-label-cyan mb-5" style={reveal(100)}>
              PRECISION AGRICULTURE · QUALITY INTELLIGENCE
            </p>

            <h1
              className="text-off-white font-bold leading-[1.05] mb-6"
              style={{ fontSize: 'clamp(2.8rem, 5.5vw, 5.5rem)', ...reveal(250) }}
            >
              See every onion.<br />
              <span className="text-cyan">Measure what matters.</span><br />
              decision.
            </h1>

            <p
              className="text-soft-white/60 text-lg leading-relaxed max-w-lg mb-10"
              style={reveal(420)}
            >
              AI-assisted onion quality grading for consistent, explainable procurement. Computer vision, calibrated size measurement and configurable Grade A / URS rules—delivered through a mobile-first workflow.
            </p>

            <div className="flex flex-wrap gap-4 mb-14" style={reveal(580)}>
              <a href="#platform" className="btn-primary">
                Explore the platform <ArrowRight size={14} />
              </a>
              <a href="#how-it-works" className="btn-secondary">
                View how it works <ArrowRight size={14} />
              </a>
            </div>
          </div>

          {/* Right — 5 cols */}
          <div className="lg:col-span-5" style={reveal(700)}>
            <InspectionPanel loaded={loaded} />
          </div>
        </div>
      </div>

      {/* Status strip (spec §8.2) */}
      <div className="relative z-10 border-t border-[rgba(255,255,255,0.07)]" style={reveal(1200)}>
        <div className="max-w-8xl mx-auto px-6 md:px-10 py-3 flex flex-wrap gap-x-8 gap-y-2">
          {statusItems.map(s => (
            <div key={s.label} className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color }} />
              <span className="tech-label text-[9px]">{s.label}</span>
              <span className="font-mono text-[10px] font-semibold" style={{ color: s.color }}>{s.val}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
