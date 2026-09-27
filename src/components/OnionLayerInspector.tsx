import { useState } from 'react'
import { motion } from 'framer-motion'
import { Volume2 } from 'lucide-react'
import { soundSynth } from '../utils/audioSynth'

type OnionState = 'solid' | 'rot' | 'hollow'

const onionProfiles: Record<OnionState, {
  title: string
  subtitle: string
  freq: string
  velocity: string
  damping: string
  visionResult: string
  acousticResult: string
  grade: string
  color: string
  bgBorder: string
  badgeColor: string
  description: string
}> = {
  solid: {
    title: 'Grade A Solid Onion (Crisp Layers)',
    subtitle: '100% Structural Integrity, Uniform Water-turgor Tension',
    freq: '210 Hz',
    velocity: '1,480 m/s',
    damping: 'α = 0.05 dB/cm (Low)',
    visionResult: 'PASSED (0% External Defect)',
    acousticResult: 'PASSED (Sharp Acoustic Peak @ 210Hz)',
    grade: 'GRADE A PASSED',
    color: '#10B981',
    bgBorder: 'border-emerald-500/40 bg-emerald-950/20',
    badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    description: 'High acoustic sound velocity propagates evenly across dry outer tunic and tight interior fleshy scales. Produces a crisp, sustained resonant acoustic signature.'
  },
  rot: {
    title: 'Internal Neck Rot (Hidden Core Rot)',
    subtitle: 'Flawless Outer Tunic Skin, Soft Mushy Fleshy Core',
    freq: '95 Hz (Dampened)',
    velocity: '620 m/s (58% Drop)',
    damping: 'α = 0.42 dB/cm (Severe)',
    visionResult: 'FALSE PASS (Skin looks 100% healthy)',
    acousticResult: 'REJECTED (High Damping & Frequency Drop)',
    grade: 'INTERNAL ROT DETECTED',
    color: '#EF4444',
    bgBorder: 'border-red-500/40 bg-red-950/20',
    badgeColor: 'bg-red-500/20 text-red-300 border-red-500/40',
    description: 'Fungal decay (Botrytis aclada) liquefies cell walls in internal rings. Acoustic impulse energy is heavily absorbed by mushy tissue, causing rapid signal damping.'
  },
  hollow: {
    title: 'Hollow Heart / Center Void',
    subtitle: 'Air Cavity Inside Core from Dry Growing Season',
    freq: '155 Hz (Double Peak)',
    velocity: '940 m/s',
    damping: 'α = 0.22 dB/cm (Medium)',
    visionResult: 'PASSED (Sizing compliant)',
    acousticResult: 'URS POLICY APPLIED (Internal Void Flag)',
    grade: 'URS ACCEPTED (LOWER GRADE)',
    color: '#FF9F1C',
    bgBorder: 'border-amber-500/40 bg-amber-950/20',
    badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    description: 'Central air cavity creates an acoustic impedance boundary ($Z_1 \\neq Z_2$). Sound bounces off internal void boundary, creating a split secondary peak.'
  }
}

export default function OnionLayerInspector() {
  const [activeState, setActiveState] = useState<OnionState>('rot')
  const profile = onionProfiles[activeState]

  const handleSelect = (state: OnionState) => {
    setActiveState(state)
    soundSynth.playChirp(state)
  }

  return (
    <div className="hud-panel p-6 md:p-8 space-y-6 relative overflow-hidden border border-ind-border-bright">
      {/* Corner HUD framing */}
      <div className="hud-corner hud-corner-tl" />
      <div className="hud-corner hud-corner-tr" />
      <div className="hud-corner hud-corner-bl" />
      <div className="hud-corner hud-corner-br" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="amber-micro-badge">PHYSICAL INSPECTION DEMO</span>
            <span className="font-mono text-xs text-sonar-cyan tracking-widest uppercase">// INTERNAL ACOUSTIC SCREENING</span>
          </div>
          <h3 className="text-xl md:text-2xl font-mono font-extrabold text-white mt-1">
            ONION STRUCTURAL ACOUSTIC PROBE
          </h3>
          <p className="text-xs text-text-sec font-mono mt-1">
            Select a specimen to simulate a controlled impulse and compare surface vision with the internal acoustic response.
          </p>
        </div>

        {/* State Selector Buttons */}
        <div className="flex items-center gap-2 bg-ind-dark p-1.5 rounded-xl border border-white/10">
          <button
            onClick={() => handleSelect('solid')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeState === 'solid'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-lg'
                : 'text-text-muted hover:text-white'
            }`}
          >
            SOLID (GRADE A)
          </button>
          <button
            onClick={() => handleSelect('rot')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeState === 'rot'
                ? 'bg-red-500/20 text-red-300 border border-red-500/50 shadow-lg'
                : 'text-text-muted hover:text-white'
            }`}
          >
            HIDDEN ROT
          </button>
          <button
            onClick={() => handleSelect('hollow')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeState === 'hollow'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-lg'
                : 'text-text-muted hover:text-white'
            }`}
          >
            HOLLOW CORE
          </button>
        </div>
      </div>

      {/* Main Grid: Interactive Graphic + Telemetry Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* SVG / Canvas Cross-Section Diagram */}
        <div className="lg:col-span-6 bg-ind-dark p-6 rounded-2xl border border-white/10 relative flex flex-col items-center justify-center min-h-[300px]">
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-sonar-cyan animate-pulse" />
            <span className="font-mono text-[10px] text-sonar-cyan font-bold">PIEZO CONTACT POINT</span>
          </div>

          <button
            onClick={() => soundSynth.playChirp(activeState)}
            className="absolute bottom-3 right-3 flex items-center gap-1.5 px-3 py-1 rounded-lg bg-sonar-cyan/10 border border-sonar-cyan/40 text-sonar-cyan font-mono text-[10px] font-bold hover:bg-sonar-cyan/20 transition-all"
          >
            <Volume2 size={12} /> TAP SOLENOID
          </button>

          {/* Interactive Graphic Representation */}
          <div className="relative w-56 h-56 flex items-center justify-center my-4">
            {/* Concentric Rings (Onion Layers) */}
            <motion.div
              animate={{ scale: [1, 1.02, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="absolute inset-0 rounded-full border-4 border-amber-700/60 bg-amber-950/30 flex items-center justify-center"
            >
              {/* Layer 2 */}
              <div className="w-44 h-44 rounded-full border-2 border-amber-600/40 bg-amber-900/20 flex items-center justify-center">
                {/* Layer 3 */}
                <div className="w-32 h-32 rounded-full border-2 border-amber-500/30 bg-amber-800/20 flex items-center justify-center">
                  {/* Layer 4 / Core */}
                  <div 
                    className={`w-20 h-20 rounded-full flex items-center justify-center border transition-all duration-500 ${
                      activeState === 'rot'
                        ? 'bg-red-950/80 border-red-500 animate-pulse shadow-lg shadow-red-500/30'
                        : activeState === 'hollow'
                        ? 'bg-amber-950/60 border-amber-500 border-dashed'
                        : 'bg-emerald-950/60 border-emerald-400'
                    }`}
                  >
                    <span className="font-mono text-[10px] font-bold text-center px-1" style={{ color: profile.color }}>
                      {activeState === 'rot' ? 'MUSH ROT' : activeState === 'hollow' ? 'AIR VOID' : 'SOLID CORE'}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Acoustic Wave Vector */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              <line x1="10" y1="112" x2="216" y2="112" stroke={profile.color} strokeWidth="2" strokeDasharray="4 4" />
              <circle cx="10" cy="112" r="6" fill="#00E5FF" />
            </svg>
          </div>

          <p className="font-mono text-[11px] text-text-sec text-center max-w-sm mt-2">
            Acoustic impulse wave enters outer tunic at <span className="text-white">$x=0$</span> and bounces off core density boundaries.
          </p>
        </div>

        {/* Telemetry Breakdown */}
        <div className="lg:col-span-6 space-y-4 font-mono text-xs">
          {/* Status Badge */}
          <div className={`p-4 rounded-xl border ${profile.bgBorder} flex items-center justify-between`}>
            <div>
              <span className="text-[10px] text-text-sec uppercase tracking-widest font-bold">DECISION ENGINE</span>
              <h4 className="text-base font-extrabold text-white mt-0.5">{profile.title}</h4>
            </div>
            <span className={`px-3 py-1 rounded-md text-[10px] font-extrabold border ${profile.badgeColor}`}>
              {profile.grade}
            </span>
          </div>

          {/* Vision vs Acoustic Comparison Table */}
          <div className="bg-ind-dark p-4 rounded-xl border border-white/10 space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-text-sec text-[11px]">OPTICAL ASSESSMENT:</span>
              <span className="font-bold text-slate-200">{profile.visionResult}</span>
            </div>
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-text-sec text-[11px]">ACOUSTIC RESPONSE:</span>
              <span className="font-bold text-white" style={{ color: profile.color }}>{profile.acousticResult}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-sec text-[11px]">RESONANT PEAK (FFT):</span>
              <span className="font-bold text-sonar-cyan">{profile.freq}</span>
            </div>
          </div>

          {/* Physical Constants */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-ind-dark p-3 rounded-xl border border-white/10">
              <span className="text-[10px] text-text-sec block">SOUND VELOCITY ($v$)</span>
              <span className="text-sm font-bold text-white mt-0.5 block">{profile.velocity}</span>
            </div>
            <div className="bg-ind-dark p-3 rounded-xl border border-white/10">
              <span className="text-[10px] text-text-sec block">DAMPING COEFF ($\alpha$)</span>
              <span className="text-sm font-bold text-amber-400 mt-0.5 block">{profile.damping}</span>
            </div>
          </div>

          <p className="text-[11px] text-text-sec leading-relaxed bg-ind-dark/50 p-3 rounded-xl border border-white/5">
            {profile.description}
          </p>
        </div>
      </div>
    </div>
  )
}
