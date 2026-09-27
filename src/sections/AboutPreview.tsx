import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function AboutPreview() {
  return (
    <section className="section-pad bg-navy relative overflow-hidden border-t border-[rgba(255,255,255,0.06)]">
      <div className="absolute inset-0 grid-overlay opacity-30 pointer-events-none" />

      <div className="relative z-10 max-w-4xl mx-auto px-6 md:px-10 text-center">
        <p className="tech-label-cyan mb-4">SYSTEM CONTEXT</p>
        <h2 className="text-off-white font-bold leading-[1.05] mb-8" style={{ fontSize: 'clamp(2rem, 3vw, 3rem)' }}>
          Built for the realities of procurement.
        </h2>
        
        <p className="text-soft-white/60 text-lg leading-relaxed mb-10 max-w-2xl mx-auto">
          Designed for agricultural procurement centres, the platform turns subjective inspection into a structured, reviewable workflow. It is mobile-first by design, with the operating realities of busy and challenging packhouse environments in mind.
        </p>

        <Link to="/about" className="btn-secondary">
          Read the project background <ArrowRight size={14} />
        </Link>
      </div>
    </section>
  )
}
