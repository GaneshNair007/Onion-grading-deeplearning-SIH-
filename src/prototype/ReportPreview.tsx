import { motion, AnimatePresence } from 'framer-motion'
import TechLabel from '../components/TechLabel'
import GlassCard from '../components/GlassCard'

interface ReportPreviewProps {
  show: boolean
  grade: string | null
}

export default function ReportPreview({ show, grade }: ReportPreviewProps) {
  const now = new Date()

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 24 }}
          transition={{ duration: 0.5 }}
        >
          <GlassCard hud className="overflow-hidden p-0">
            {/* Report header */}
            <div className="px-6 py-4 flex items-start justify-between border-b" style={{ background: 'var(--bg-panel)', borderColor: 'var(--border)' }}>
              <div>
                <TechLabel cyan className="block text-xs">DIGITAL INSPECTION REPORT</TechLabel>
                <p className="text-[10px] mono mt-1" style={{ color: 'var(--text-dim)' }}>Prototype visualization · not experimental results</p>
              </div>
              {/* Animated QR placeholder */}
              <motion.div
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-14 h-14 rounded-sm grid grid-cols-3 grid-rows-3 gap-0.5 p-1.5"
                style={{ background: 'rgba(255,255,255,0.05)' }}
              >
                {Array.from({ length: 9 }).map((_, i) => (
                  <div
                    key={i}
                    className="rounded-sm"
                    style={{ background: [0, 2, 6, 8].includes(i) ? 'var(--text-sec)' : i === 4 ? 'var(--cyan)' : 'rgba(255,255,255,0.05)' }}
                  />
                ))}
              </motion.div>
            </div>

            <div className="p-6">
              {/* Fields */}
              <div className="grid grid-cols-2 gap-x-8 gap-y-3 mb-5">
                {[
                  ['REPORT ID', 'RPT-DEMO-001'],
                  ['BATCH ID', 'BCH-DEMO-001'],
                  ['DATE / TIME', now.toLocaleString('en-IN')],
                  ['POLICY VERSION', 'POL-v1.0-DEMO'],
                  ['URS STATUS', 'ENABLED'],
                  ['OFFICER', '— (DEMO)'],
                ].map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between border-b pb-1.5" style={{ borderColor: 'var(--border-dim)' }}>
                    <TechLabel className="text-[8px]">{k}</TechLabel>
                    <span className="mono text-[10px] text-white">{v}</span>
                  </div>
                ))}
              </div>

              {/* Grade result */}
              <div
                className="rounded-sm p-4 text-center mb-4 border relative"
                style={{
                  background: grade === 'GRADE A' ? 'rgba(0,200,255,0.05)'
                    : grade === 'GRADE URS' ? 'rgba(167,139,250,0.05)'
                    : grade === 'REJECTED' ? 'rgba(248,113,113,0.05)'
                    : 'rgba(255,184,0,0.05)',
                  borderColor: grade === 'GRADE A' ? 'rgba(0,200,255,0.2)'
                    : grade === 'GRADE URS' ? 'rgba(167,139,250,0.2)'
                    : grade === 'REJECTED' ? 'rgba(248,113,113,0.2)'
                    : 'rgba(255,184,0,0.2)',
                }}
              >
                <TechLabel className="block mb-1 text-white">GRADE OUTCOME</TechLabel>
                <div
                  className="text-2xl mono font-bold"
                  style={{
                    color: grade === 'GRADE A' ? 'var(--cyan)'
                      : grade === 'GRADE URS' ? '#A78BFA'
                      : grade === 'REJECTED' ? '#F87171'
                      : 'var(--amber)',
                  }}
                >
                  {grade || '—'}
                </div>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                {[
                  { label: 'TOTAL', value: '—' },
                  { label: 'GRADE A', value: '—', color: 'var(--cyan)' },
                  { label: 'URS', value: '—', color: '#A78BFA' },
                  { label: 'REJECTED', value: '—', color: '#F87171' },
                ].map((s) => (
                  <div key={s.label} className="rounded-sm p-2 text-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border-dim)' }}>
                    <TechLabel className="block text-[7px] mb-1">{s.label}</TechLabel>
                    <span className="mono text-sm font-bold" style={{ color: s.color || 'var(--text-sec)' }}>{s.value}</span>
                  </div>
                ))}
              </div>

              {/* Audit fields */}
              <div className="space-y-2">
                {[
                  ['DEFECT BREAKDOWN', '—'],
                  ['AI CONFIDENCE', '—'],
                  ['ACOUSTIC SCREEN', '—'],
                  ['HUMAN OVERRIDE', 'NONE'],
                ].map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1 border-b" style={{ borderColor: 'var(--border-dim)' }}>
                    <TechLabel className="text-[8px]">{k}</TechLabel>
                    <span className="mono text-[10px]" style={{ color: 'var(--text-sec)' }}>{v}</span>
                  </div>
                ))}
              </div>

              <p className="text-[9px] mt-4 text-center" style={{ color: 'var(--text-dim)' }}>
                Prototype values shown · live results will populate through the connected backend.
              </p>
            </div>
          </GlassCard>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
