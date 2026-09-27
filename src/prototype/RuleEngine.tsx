import { motion, AnimatePresence } from 'framer-motion'
import TechLabel from '../components/TechLabel'

interface RuleEngineProps {
  grade: string | null
  isComplete: boolean
}

const ruleSteps = [
  { label: 'VISIBLE ROT?', pass: 'NO', fail: '→ REJECTED' },
  { label: 'CALIBRATION VALID?', pass: 'YES', fail: '→ MANUAL REVIEW' },
  { label: 'IMAGE QUALITY OK?', pass: 'YES', fail: '→ MANUAL REVIEW' },
  { label: 'QUALITY + SIZE', pass: 'ASSESS', fail: '' },
  { label: 'ACTIVE POLICY', pass: 'APPLY', fail: '' },
]

const gradeColors: Record<string, string> = {
  'GRADE A': '#00C8FF',
  'GRADE URS': '#A78BFA',
  'REJECTED': '#F87171',
  'MANUAL REVIEW': '#FFB800',
}

export default function RuleEngine({ grade, isComplete }: RuleEngineProps) {
  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <TechLabel>GRADING RULE ENGINE</TechLabel>
        {isComplete && <TechLabel cyan>DECISION GENERATED</TechLabel>}
      </div>

      {/* Rule steps */}
      <div className="space-y-2 mb-4 flex-1">
        {ruleSteps.map((step, i) => (
          <motion.div
            key={step.label}
            initial={{ opacity: 0.4 }}
            animate={{ opacity: isComplete ? 1 : 0.4 + i * 0.1 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center justify-between rounded-sm px-4 py-2.5 border"
            style={{ background: 'var(--bg)', borderColor: 'var(--border-dim)' }}
          >
            <TechLabel className="text-[9px] text-white">{step.label}</TechLabel>
            <div className="flex gap-2">
              {step.fail && (
                <span className="mono text-[9px]" style={{ color: 'rgba(248,113,113,0.7)' }}>{step.fail}</span>
              )}
              <span className="mono text-[9px] font-bold text-white">{step.pass}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Grade output */}
      <AnimatePresence>
        {isComplete && grade && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="rounded-sm p-5 text-center border relative"
            style={{
              background: `${gradeColors[grade]}10`,
              borderColor: `${gradeColors[grade]}30`,
            }}
          >
            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l" style={{ borderColor: gradeColors[grade] }} />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r" style={{ borderColor: gradeColors[grade] }} />
            <TechLabel className="block mb-2 text-white">GRADE OUTCOME</TechLabel>
            <div className="text-2xl font-bold mono" style={{ color: gradeColors[grade] }}>{grade}</div>
            <TechLabel className="block mt-2 text-[8px] opacity-50 text-white">Prototype decision · not a validated analysis result</TechLabel>
          </motion.div>
        )}
        {!isComplete && (
          <div className="rounded-sm p-4 text-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border-dim)' }}>
            <TechLabel className="opacity-40">AWAITING INSPECTION INPUT</TechLabel>
          </div>
        )}
      </AnimatePresence>

      {/* Acoustic overlay */}
      <div className="mt-4 rounded-sm p-3 border" style={{ background: 'var(--bg-mid)', borderColor: 'var(--border)' }}>
        <TechLabel className="block mb-1 text-[8px] text-white">ACOUSTIC SCREENING OVERLAY</TechLabel>
        <div className="flex items-center justify-between">
          <span className="text-xs text-white">Internal-risk flag:</span>
          <span className="mono text-xs text-white">{isComplete ? '—' : '—'}</span>
        </div>
        <p className="text-[9px] mt-2" style={{ color: 'var(--text-dim)' }}>
          Acoustic screening may increase review priority or adjust confidence. Core grading policy remains authoritative.
        </p>
      </div>
    </div>
  )
}
