import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, Volume2, VolumeX } from 'lucide-react'
import { soundSynth } from '../utils/audioSynth'

const links = [
  { label: 'Home',      to: '/' },
  { label: 'About',     to: '/about' },
  { label: 'Inspection Lab', to: '/prototype' },
]

export default function SiteNav() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const [isMuted, setIsMuted] = useState(soundSynth.getIsMuted())
  const location = useLocation()

  const toggleAudio = () => {
    const next = !isMuted
    soundSynth.setMuted(next)
    setIsMuted(next)
  }

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  return (
    <header
      className={`
        fixed top-0 left-0 right-0 z-[100]
        transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]
        ${scrolled
          ? 'bg-transparent py-3'
          : 'bg-transparent py-5'
        }
      `}
    >
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
        {/* Brand */}
        <Link
          to="/"
          className="flex items-center gap-3 select-none group"
        >
          <div className="flex flex-col leading-none">
            <span className="font-display text-xl font-bold text-onion-deep tracking-[0.15em] uppercase transition-all duration-300 group-hover:opacity-80">
              VOSTOK
            </span>
            <span className="text-[9px] text-text-muted font-sans font-medium max-w-[150px] leading-tight mt-1 hidden lg:block opacity-70">
              Vibro-acoustic & Optical Sensing Technology for Onion Knowledge
            </span>
          </div>
        </Link>
        {/* Desktop Navigation */}
        <nav className="hidden md:flex absolute left-1/2 -translate-x-1/2 items-center">
          <div className="flex items-center gap-1 p-1.5 rounded-full bg-white/50 backdrop-blur-2xl border border-glass-border shadow-soft">
            {links.map(({ label, to }) => {
              const active = location.pathname === to
              return (
                <Link
                  key={label}
                  to={to}
                  className="relative px-5 py-2 text-sm font-sans font-medium transition-colors duration-300 rounded-full"
                >
                  {active && (
                    <motion.div
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-full bg-gradient-to-r from-onion-soft to-onion-light/60 border border-onion/10"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className={`relative z-10 transition-colors duration-300 ${
                    active ? 'text-onion-deep' : 'text-text-secondary hover:text-text-primary'
                  }`}>
                    {label}
                  </span>
                </Link>
              )
            })}
          </div>
        </nav>


        {/* Right Action buttons */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleAudio}
            title={isMuted ? 'Unmute Acoustic Audio Synth' : 'Mute Acoustic Audio Synth'}
            className={`px-3 py-1.5 rounded-full text-xs font-sans font-medium flex items-center gap-1.5 transition-all cursor-pointer ${
              isMuted
                ? 'bg-white/50 text-text-muted hover:text-text-primary border border-glass-border'
                : 'bg-onion-soft/90 text-onion-deep border border-onion/30 shadow-soft'
            }`}
          >
            {isMuted ? <VolumeX size={13} /> : <Volume2 size={13} className="text-onion animate-pulse" />}
            <span>{isMuted ? 'Sound Off' : 'Acoustic Sound'}</span>
          </button>

          <a
            href="http://localhost:8000/dashboard/app/scan.html"
            className="px-4 py-2 text-xs font-sans font-semibold rounded-full bg-white/60 backdrop-blur-xl border border-glass-border text-text-secondary hover:text-text-primary hover:border-onion/30 transition-all shadow-soft"
          >
            Scan Kiosk ↗
          </a>
          <a
            href="http://localhost:5000"
            className="px-4 py-2 text-xs font-sans font-semibold rounded-full bg-gradient-to-r from-cyan-600 to-teal-600 text-white shadow-soft hover:opacity-90 transition-all"
          >
            YOLOv8 Lab ↗
          </a>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setOpen(!open)}
          className="md:hidden w-10 h-10 flex items-center justify-center rounded-full bg-white/60 backdrop-blur-xl border border-glass-border text-text-secondary hover:text-text-primary transition-all"
          aria-label="Toggle navigation"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="md:hidden overflow-hidden"
          >
            <div className="glass-nav px-6 py-6 flex flex-col gap-2 border-t border-glass-border">
              {links.map(({ label, to }) => {
                const active = location.pathname === to
                return (
                  <Link
                    key={label}
                    to={to}
                    onClick={() => setOpen(false)}
                    className={`px-4 py-3 rounded-2xl text-sm font-sans font-medium transition-all duration-300 ${
                      active
                        ? 'bg-onion-soft text-onion-deep border border-onion/10'
                        : 'text-text-secondary hover:bg-bg-soft hover:text-text-primary'
                    }`}
                  >
                    {label}
                  </Link>
                )
              })}

              <div className="pt-3 border-t border-glass-border flex flex-col gap-2">
                <button
                  onClick={toggleAudio}
                  className="px-4 py-2.5 rounded-xl text-xs font-sans font-medium flex items-center justify-between bg-white/60 border border-glass-border text-text-primary"
                >
                  <span className="flex items-center gap-2">
                    {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} className="text-onion" />}
                    <span>Acoustic Audio Feedback</span>
                  </span>
                  <span className="font-semibold text-onion">{isMuted ? 'OFF' : 'ON'}</span>
                </button>
                <a
                  href="http://localhost:8000/dashboard/app/scan.html"
                  className="px-4 py-2.5 rounded-xl text-xs font-sans font-medium flex items-center justify-between bg-white/60 border border-glass-border text-text-primary"
                >
                  <span>Scan Kiosk Dashboard</span>
                  <span>↗</span>
                </a>
                <a
                  href="http://localhost:5000"
                  className="px-4 py-2.5 rounded-xl text-xs font-sans font-medium flex items-center justify-between bg-gradient-to-r from-cyan-600 to-teal-600 text-white"
                >
                  <span>YOLOv8 Deep Learning Lab</span>
                  <span>↗</span>
                </a>
              </div>

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
