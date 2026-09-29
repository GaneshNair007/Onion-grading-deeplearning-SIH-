import { motion } from 'framer-motion'
import GlassCard from '../components/GlassCard'
import { PieChart, ShieldAlert } from 'lucide-react'

const grades = [
  { label: 'GRADE A', pct: 62, color: '#10B981', bg: 'bg-emerald-500' },
  { label: 'GRADE URS', pct: 21, color: '#00C8FF', bg: 'bg-cyan-dark' },
  { label: 'REJECTED', pct: 11, color: '#EF4444', bg: 'bg-rose-500' },
  { label: 'MANUAL REVIEW', pct: 6, color: '#F59E0B', bg: 'bg-amber-500' },
]

export default function GradeVisualization() {
  return (
    <section className="py-24 px-6 bg-app-bg relative">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Header */}
        <div className="space-y-4 max-w-3xl">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="flex items-center gap-3"
          >
            <span className="w-8 h-0.5 bg-cyan-dark" />
            <span className="font-mono text-xs font-bold tracking-widest text-cyan-dark uppercase">
              BATCH OUTPUT · ANALYTICS
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-heading"
          >
            MEASURABLE <span className="text-cyan-dark">BATCH OUTCOMES.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-lg md:text-xl text-text-sec leading-relaxed font-medium"
          >
            Every scanned tray yields immediate percentage breakdowns across Grade A, Grade URS, Rejected, and Manual Review items.
          </motion.p>
        </div>

        {/* Analytics Grid */}
        <div className="grid lg:grid-cols-12 gap-8 items-stretch">
          
          {/* Main Distribution Bar Card */}
          <GlassCard className="lg:col-span-7 space-y-8 border-white">
            <div className="flex items-center justify-between border-b border-black/5 pb-4">
              <div className="flex items-center gap-3">
                <PieChart className="w-5 h-5 text-cyan-dark" />
                <h3 className="font-mono text-xs font-bold tracking-wider text-graphite uppercase">BATCH DISTRIBUTION</h3>
              </div>
              <span className="tech-micro-badge">PROTOTYPE BATCH</span>
            </div>

            <div className="space-y-6">
              {grades.map((g, i) => (
                <div key={g.label} className="space-y-2">
                  <div className="flex justify-between items-center font-mono text-xs">
                    <span className="font-bold text-graphite">{g.label}</span>
                    <span className="font-extrabold" style={{ color: g.color }}>{g.pct}%</span>
                  </div>
                  <div className="h-3 rounded-full bg-surface-subtle overflow-hidden p-0.5 border border-black/5">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${g.pct}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.0, delay: i * 0.12, ease: [0.16, 1, 0.3, 1] }}
                      className={`h-full rounded-full ${g.bg}`}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 rounded-2xl bg-surface-subtle border border-black/5 font-mono text-[11px] text-text-sec flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-cyan-dark flex-shrink-0" />
              Formula: Grade A % = N_GradeA / N_Total × 100
            </div>
          </GlassCard>

          {/* Quick Stat Tiles */}
          <div className="lg:col-span-5 grid grid-cols-2 gap-4">
            {grades.map((g, i) => (
              <GlassCard key={g.label} delay={i * 0.08} className="p-6 border-white space-y-2 flex flex-col justify-between">
                <span className="font-mono text-[10px] font-bold text-text-muted tracking-widest">{g.label}</span>
                <div className="font-mono text-4xl font-extrabold" style={{ color: g.color }}>
                  {g.pct}%
                </div>
                <span className="font-mono text-[9px] text-text-sec">BATCH DISTRIBUTION</span>
              </GlassCard>
            ))}
          </div>

        </div>

      </div>
    </section>
  )
}

