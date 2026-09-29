import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function CtaBanner() {
  return (
    <footer className="bg-[#040A10] border-t border-[rgba(255,255,255,0.06)] relative overflow-hidden">
      {/* Dark photo background for CTA */}
      <div className="absolute inset-0 opacity-40">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover object-bottom"
        >
          <source src="/hero_video.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-[#040A10]/80" />
      </div>

      <div className="absolute inset-0 grid-overlay opacity-20 pointer-events-none" />

      {/* CTA Main Content */}
      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10 pt-24 pb-16 border-b border-[rgba(255,255,255,0.06)]">
        <div className="max-w-3xl">
          <h2 className="text-off-white font-bold leading-[1.05] mb-8" style={{ fontSize: 'clamp(2.5rem, 5vw, 4.5rem)' }}>
            A better way<br />to grade.
          </h2>
          
          <div className="flex flex-wrap items-center gap-4 mb-10">
            <span className="tech-label text-cyan text-[10px]">AI</span>
            <span className="text-muted-blue/40">/</span>
            <span className="tech-label text-cyan text-[10px]">COMPUTER VISION</span>
            <span className="text-muted-blue/40">/</span>
            <span className="tech-label text-cyan text-[10px]">SIZE CALIBRATION</span>
            <span className="text-muted-blue/40">/</span>
            <span className="tech-label text-cyan text-[10px]">AUDIT EVIDENCE</span>
          </div>

          <div className="flex flex-wrap gap-4">
            <Link to="/prototype" className="btn-primary">
              Open the web prototype <ArrowRight size={14} />
            </Link>
            <Link to="/contact" className="btn-secondary">
              Request system access
            </Link>
          </div>
        </div>
      </div>

      {/* Footer Links & Legal */}
      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          
          {/* Brand */}
          <div className="flex flex-col">
            <span className="text-off-white font-bold text-lg tracking-tight">ONION // VISION</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6">
            <Link to="/#platform" className="tech-label text-[10px] hover:text-cyan transition-colors">PLATFORM</Link>
            <Link to="/#technology" className="tech-label text-[10px] hover:text-cyan transition-colors">TECHNOLOGY</Link>
            <Link to="/about" className="tech-label text-[10px] hover:text-cyan transition-colors">ABOUT</Link>
            <Link to="/contact" className="tech-label text-[10px] hover:text-cyan transition-colors">CONTACT</Link>
          </div>

          {/* Status */}
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-success dot-online" />
            <span className="tech-label text-[9px]">SYSTEM STATUS</span>
            <span className="tech-label text-[9px] text-success">OPERATIONAL</span>
          </div>

        </div>
      </div>
    </footer>
  )
}
