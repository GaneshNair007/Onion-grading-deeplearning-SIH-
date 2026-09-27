import { useState } from 'react'
import TechLabel from '../components/TechLabel'
import GlassCard from '../components/GlassCard'

type FilterKey = 'ALL' | 'HEALTHY' | 'DAMAGED' | 'ROTTEN' | 'SPROUTED' | 'GRADE_A' | 'URS' | 'REJECTED' | 'MANUAL_REVIEW'

const demoRows = [
  { id: 'ONI-001', audio: '✓', fft: '✓', label: 'HEALTHY', grade: 'GRADE A', conf: '0.94' },
  { id: 'ONI-002', audio: '✓', fft: '✓', label: 'DAMAGED', grade: 'REJECTED', conf: '0.88' },
  { id: 'ONI-003', audio: '✓', fft: '✓', label: 'SPROUTED', grade: 'GRADE URS', conf: '0.76' },
  { id: 'ONI-004', audio: '✓', fft: '✓', label: 'HEALTHY', grade: 'GRADE A', conf: '0.91' },
  { id: 'ONI-005', audio: '✓', fft: '—', label: 'ROTTEN', grade: 'REJECTED', conf: '0.97' },
  { id: 'ONI-006', audio: '—', fft: '—', label: 'HEALTHY', grade: 'MANUAL REVIEW', conf: '0.51' },
]

const gradeColors: Record<string, string> = {
  'GRADE A': '#00C8FF',
  'GRADE URS': '#A78BFA',
  'REJECTED': '#F87171',
  'MANUAL REVIEW': '#FFB800',
}

const filters: FilterKey[] = ['ALL', 'HEALTHY', 'DAMAGED', 'ROTTEN', 'SPROUTED', 'GRADE_A', 'URS', 'REJECTED', 'MANUAL_REVIEW']

export default function Dataset() {
  const [activeFilter, setActiveFilter] = useState<FilterKey>('ALL')

  const filtered = demoRows.filter((row) => {
    if (activeFilter === 'ALL') return true
    if (activeFilter === 'GRADE_A') return row.grade === 'GRADE A'
    if (activeFilter === 'URS') return row.grade === 'GRADE URS'
    if (activeFilter === 'REJECTED') return row.grade === 'REJECTED'
    if (activeFilter === 'MANUAL_REVIEW') return row.grade === 'MANUAL REVIEW'
    return row.label === activeFilter
  })

  return (
    <GlassCard hud className="p-6">
      <div className="flex items-center justify-between mb-4">
        <TechLabel>DATASET / INSPECTION HISTORY</TechLabel>
        <span className="tech-label bg-surface2 px-2 py-1 rounded-sm border text-[9px]" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>PROTOTYPE DATA</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`px-3 py-1 rounded-sm text-[9px] font-semibold tracking-widest uppercase transition-all border ${
              activeFilter === f
                ? 'text-cyan border-cyan'
                : 'text-text-sec border-border hover:bg-white/5'
            }`}
            style={{ 
              background: activeFilter === f ? 'rgba(0,200,255,0.1)' : 'var(--bg-mid)',
              borderColor: activeFilter === f ? 'var(--cyan)' : 'var(--border)'
            }}
          >
            {f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-sm border" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-xs min-w-[480px]">
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
              {['ID', 'AUDIO', 'FFT', 'LABEL', 'GRADE', 'CONFIDENCE'].map((h) => (
                <th key={h} className="text-left px-4 py-3 border-b" style={{ borderColor: 'var(--border-dim)' }}><TechLabel className="text-[8px]">{h}</TechLabel></th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={row.id} className="border-b" style={{ borderColor: 'var(--border-dim)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                <td className="px-4 py-2.5 mono text-white font-medium">{row.id}</td>
                <td className="px-4 py-2.5 mono text-center" style={{ color: row.audio === '✓' ? 'var(--cyan)' : 'var(--text-dim)' }}>{row.audio}</td>
                <td className="px-4 py-2.5 mono text-center" style={{ color: row.fft === '✓' ? 'var(--cyan)' : 'var(--text-dim)' }}>{row.fft}</td>
                <td className="px-4 py-2.5 font-medium text-white">{row.label}</td>
                <td className="px-4 py-2.5 font-bold mono" style={{ color: gradeColors[row.grade] }}>{row.grade}</td>
                <td className="px-4 py-2.5 mono" style={{ color: 'var(--text-sec)' }}>{row.conf}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[10px] mt-4" style={{ color: 'var(--text-sec)' }}>Prototype records shown here are illustrative. Live inspection records will populate from the connected backend.</p>
    </GlassCard>
  )
}
