import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, Activity, Volume2, VolumeX } from 'lucide-react'
import { soundSynth } from '../utils/audioSynth'

const links = [
  { to: '/', label: 'HOME', end: true },
  { to: '/about', label: 'ABOUT', end: false },
  { to: '/prototype', label: 'ACOUSTIC LAB', end: false },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [isMuted, setIsMuted] = useState(soundSynth.getIsMuted())
  const [, setTick] = useState(0)
  const location = useLocation()

  useEffect(() => { setMenuOpen(false) }, [location])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const toggleAudio = () => {
    const nextState = !isMuted
    soundSynth.setMuted(nextState)
    setIsMuted(nextState)
  }

  const now = new Date()
  const timeStr = now.toTimeString().slice(0, 8)

  return (
    <>
      <header className="fixed top-4 left-0 right-0 z-50 px-4 md:px-8">
        <div 
          className={`max-w-7xl mx-auto rounded-2xl transition-all duration-300 px-6 py-3 flex items-center justify-between ${
            scrolled 
              ? 'bg-ind-card/95 backdrop-blur-xl border border-ind-border-bright shadow-2xl shadow-black/80' 
              : 'bg-ind-card/80 backdrop-blur-lg border border-ind-border shadow-xl shadow-black/50'
          }`}
        >
          {/* Brand */}
          <NavLink to="/" className="flex items-center gap-3 group select-none">
            <div className="w-9 h-9 rounded-lg bg-ind-panel border border-sonar-cyan/40 flex items-center justify-center text-sonar-cyan relative shadow-sm group-hover:scale-105 transition-transform">
              <Activity className="w-5 h-5 text-sonar-cyan animate-pulse" />
              <div className="absolute inset-0 rounded-lg border border-sonar-cyan/30 animate-ping opacity-30" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-extrabold text-sm tracking-widest text-white uppercase">
                  ONION <span className="text-sonar-cyan">//</span> ACOUSTIC
                </span>
                <span className="tech-micro-badge hidden sm:inline-block"></span>
              </div>
              <p className="text-[10px] text-text-sec font-mono tracking-widest uppercase hidden sm:block">
                BIO-ACOUSTIC INSPECTION PLATFORM
              </p>
            </div>
          </NavLink>

          {/* Desktop Links */}
          <nav className="hidden md:flex items-center gap-1 bg-ind-panel/90 p-1.5 rounded-xl border border-white/10">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `relative px-5 py-1.5 text-xs font-mono font-bold tracking-widest uppercase transition-all rounded-lg ${
                    isActive
                      ? 'text-sonar-cyan bg-ind-dark border border-sonar-cyan/40 shadow-inner'
                      : 'text-text-sec hover:text-white'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {link.label}
                    {isActive && (
                      <motion.div
                        layoutId="nav-pill"
                        className="absolute inset-0 rounded-lg bg-ind-dark border border-sonar-cyan/40 -z-10"
                        transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                      />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Right Controls & Audio Synth Mute */}
          <div className="hidden md:flex items-center gap-4">
            {/* Sound Synth Toggle */}
            <button
              onClick={toggleAudio}
              title={isMuted ? 'Unmute Acoustic Audio Synth' : 'Mute Acoustic Audio Synth'}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
                isMuted
                  ? 'bg-ind-panel/60 border-white/10 text-text-muted hover:text-white'
                  : 'bg-sonar-cyan/10 border-sonar-cyan/40 text-sonar-cyan hover:bg-sonar-cyan/20'
              }`}
            >
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} className="animate-pulse" />}
              <span className="text-[10px] font-bold tracking-wider">{isMuted ? 'AUDIO OFF' : 'AUDIO SYNTH ON'}</span>
            </button>

            <div className="h-4 w-px bg-white/10" />

            <div className="font-mono text-xs text-sonar-cyan/90 tracking-widest font-bold bg-ind-dark px-2.5 py-1 rounded-md border border-white/10">
              {timeStr}
            </div>

            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-emerald-950/60 border border-emerald-500/40">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-mono text-[10px] font-bold text-emerald-300 tracking-wider">INSPECTION READY</span>
            </div>

            <NavLink
              to="/prototype"
              className="btn-primary-sci text-[11px] py-2 px-5"
            >
              SYSTEM LAB
            </NavLink>
          </div>

          {/* Mobile Toggle */}
          <button
            className="md:hidden p-2 text-white hover:text-sonar-cyan transition-colors"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle Navigation"
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="fixed top-20 left-4 right-4 z-40 md:hidden bg-ind-card border border-ind-border-bright rounded-2xl p-6 shadow-2xl space-y-4"
          >
            <div className="space-y-1">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.end}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-4 py-3 rounded-xl text-xs font-mono font-bold tracking-widest uppercase transition-all ${
                      isActive ? 'bg-ind-dark text-sonar-cyan border border-sonar-cyan/40' : 'text-text-sec hover:bg-ind-panel'
                    }`
                  }
                >
                  {link.label}
                  <span className="font-mono text-[10px] opacity-60"></span>
                </NavLink>
              ))}
            </div>
            
            <div className="pt-3 border-t border-white/10 flex items-center justify-between">
              <button
                onClick={toggleAudio}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono bg-ind-panel text-sonar-cyan border-sonar-cyan/40"
              >
                {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
                <span className="text-[10px]">{isMuted ? 'AUDIO OFF' : 'AUDIO SYNTH ON'}</span>
              </button>
              <NavLink to="/prototype" className="btn-primary-sci text-[10px] py-2 px-4">
                OPEN SYSTEM LAB
              </NavLink>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

