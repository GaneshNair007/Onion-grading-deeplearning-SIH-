export default function AcousticSection() {
  return (
    <section className="section-pad bg-[#040C14] relative overflow-hidden border-t border-[rgba(255,255,255,0.06)]">
      <div className="absolute inset-0 grid-overlay opacity-20 pointer-events-none" />

      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

          {/* Left — Visual representation of acoustic signal */}
          <div className="order-2 lg:order-1 tech-panel p-6 relative overflow-hidden" style={{ minHeight: 280 }}>
            <div className="absolute inset-0 flex items-center justify-center opacity-30">
              {/* Fake acoustic waveform lines */}
              <div className="w-full flex items-center justify-center gap-1">
                {Array.from({ length: 48 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-cyan rounded-full"
                    style={{
                      height: `${Math.max(10, Math.sin(i * 0.4) * 60 + Math.random() * 40)}%`,
                      opacity: Math.random() * 0.5 + 0.3
                    }}
                  />
                ))}
              </div>
            </div>

            {/* overlay badge */}
            <div className="absolute top-4 left-4 bg-[rgba(6,17,31,0.8)] px-3 py-2 border border-[rgba(39,199,232,0.3)] backdrop-blur">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan dot-online" />
                <span className="tech-label-cyan text-[9px]">ACOUSTIC SCREENING ACTIVE</span>
              </div>
            </div>

            {/* signal nodes */}
            <div className="absolute bottom-4 left-4 right-4 flex justify-between">
              <span className="tech-label text-[8px]">IMPULSE · 01</span>
              <span className="tech-label text-[8px]">RESPONSE · 0.02 s</span>
              <span className="tech-label text-[8px] text-cyan">INTERNAL DEFECT FLAGGED</span>
            </div>
          </div>

          {/* Right — Copy */}
          <div className="order-1 lg:order-2">
            <div className="flex items-center gap-3 mb-6">
              <span className="tech-label-cyan px-2 py-1 bg-cyan/10 border border-cyan/30">ENHANCED SCREENING</span>
              <span className="tech-label text-[9px] text-muted-blue">R&D · VALIDATION IN PROGRESS</span>
            </div>
            
            <h2 className="text-off-white font-bold leading-[1.05] mb-6" style={{ fontSize: 'clamp(2rem, 4vw, 3.5rem)' }}>
              The camera sees the surface.<br />We go further.
            </h2>
            
            <p className="text-soft-white/55 text-lg leading-relaxed mb-6">
              Computer vision measures what is visible. The acoustic module adds a controlled impulse-response layer to screen for structural anomalies that may not be visible at the surface.
            </p>
            
            <p className="text-soft-white/55 text-lg leading-relaxed mb-8">
              The response can flag potential internal conditions such as neck rot or hollow centres for further review before procurement decisions are finalized.
            </p>

            <a href="#acoustic" className="btn-secondary">
              Explore acoustic screening
            </a>
          </div>

        </div>
      </div>
    </section>
  )
}
