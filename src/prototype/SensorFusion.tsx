import { motion } from 'framer-motion'
import TechLabel from '../components/TechLabel'

interface SensorFusionProps {
  isComplete: boolean
}

export default function SensorFusion({ isComplete }: SensorFusionProps) {
  return (
    <div className="p-6 h-full flex flex-col">
      <TechLabel className="block mb-6">SENSOR FUSION</TechLabel>

      <div className="grid grid-cols-3 gap-4 items-center flex-1">
        {/* Camera */}
        <div className="space-y-2">
          <div className="rounded-sm p-3 text-center border" style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'var(--border-dim)' }}>
            <TechLabel className="block mb-1 text-white">OPTICAL</TechLabel>
          </div>
          {['Size', 'Damage', 'Rot', 'Sprout'].map((item) => (
            <div key={item} className="rounded-sm px-3 py-1.5 text-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border-dim)' }}>
              <TechLabel className="text-[9px]">{item}</TechLabel>
            </div>
          ))}
        </div>

        {/* Fusion center */}
        <motion.div
          animate={isComplete ? {
            boxShadow: ['0 0 0 0 rgba(0,200,255,0)', '0 0 30px 4px rgba(0,200,255,0.3)', '0 0 0 0 rgba(0,200,255,0)'],
          } : {}}
          transition={{ duration: 2, repeat: Infinity }}
          className="rounded-sm p-4 text-center border relative"
          style={{
            background: 'var(--bg-panel)',
            borderColor: isComplete ? 'var(--cyan)' : 'var(--border)',
          }}
        >
          {isComplete && (
            <>
              <div className="absolute top-0 left-0 hud-corner hud-corner-tl" />
              <div className="absolute bottom-0 right-0 hud-corner hud-corner-br" />
            </>
          )}
          <TechLabel cyan className="block text-[8px] mb-1">FUSION</TechLabel>
          <div className="text-white text-xs font-bold">
            {isComplete ? 'MERGED' : 'WAITING'}
          </div>
          <div className="mx-auto mt-3 h-6 w-px" style={{ background: 'linear-gradient(to bottom, var(--cyan-dim), transparent)' }} />
          <div className="mt-2">
            <TechLabel className="text-[7px]" style={{ color: 'var(--text-sec)' }}>DECISION SUPPORT</TechLabel>
          </div>
        </motion.div>

        {/* Acoustic */}
        <div className="space-y-2">
          <div
            className="rounded-sm p-3 text-center border"
            style={{ background: 'rgba(0,200,255,0.05)', borderColor: 'var(--cyan)' }}
          >
            <TechLabel cyan className="block mb-1">ACOUSTIC</TechLabel>
          </div>
          {['Resonance', 'Spectral', 'Damping', 'Hidden-cond.'].map((item) => (
            <div key={item} className="rounded-sm px-3 py-1.5 text-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
              <TechLabel cyan className="text-[9px]">{item}</TechLabel>
            </div>
          ))}
        </div>
      </div>

      {isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 rounded-sm p-3 text-center"
          style={{ background: 'rgba(0,200,255,0.1)', border: '1px solid var(--border)' }}
        >
          <TechLabel cyan>FUSION COMPLETE · READY FOR GRADING ENGINE</TechLabel>
        </motion.div>
      )}
      <p className="text-[10px] mt-4 text-center" style={{ color: 'var(--text-sec)' }}>PROTOTYPE DATA</p>
    </div>
  )
}
