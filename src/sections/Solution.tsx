export default function Solution() {
  return (
    <section className="section-pad bg-[#091A2A] relative overflow-hidden">
      <div className="absolute inset-0 grid-overlay opacity-30 pointer-events-none" />

      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

          {/* Left — copy */}
          <div>
            <p className="tech-label-cyan mb-4">The system</p>
            <h2 className="text-off-white font-bold leading-[1.05] mb-6" style={{ fontSize: 'clamp(2rem, 4vw, 3.75rem)' }}>
              From visual inspection<br />to digital evidence.
            </h2>
            <p className="text-soft-white/55 text-lg leading-relaxed mb-8">
              The platform combines computer vision, calibrated size measurement and a configurable Grade A / URS rule engine to turn onion inspection into a structured, reviewable process.
            </p>
            <div className="space-y-3">
              {[
                'Individual onion detection via computer vision',
                'Calibrated diameter measurement in millimetres',
                'Configurable Grade A / URS procurement policy',
                'Evidence-backed digital batch report',
                'Human review for uncertain or low-confidence cases',
              ].map(item => (
                <div key={item} className="flex items-start gap-3">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-cyan shrink-0" />
                  <span className="text-soft-white/60 text-sm leading-relaxed">{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right — mock CV detection visual */}
          <div className="relative">
            {/* Outer frame */}
            <div className="tech-panel-bright p-1 relative overflow-hidden">
              {/* Scan line */}
              <div className="scan-line opacity-70" />

              {/* Mock onion tray — styled div representing a tray */}
              <div className="relative bg-[#04101A] aspect-[4/3] overflow-hidden flex items-center justify-center">
                {/* Simulated onion blobs */}
                <div className="absolute inset-0 flex flex-wrap items-center justify-center gap-3 p-6">
                  {[
                    { grade: 'A',  mm: '57mm',  col: '#35D07F', x: 18, y: 22 },
                    { grade: 'A',  mm: '61mm',  col: '#35D07F', x: 52, y: 18 },
                    { grade: 'A',  mm: '53mm',  col: '#35D07F', x: 78, y: 30 },
                    { grade: 'U',  mm: '39mm',  col: '#27C7E8', x: 30, y: 58 },
                    { grade: '?',  mm: '--',    col: '#F2B84B', x: 62, y: 62 },
                    { grade: 'A',  mm: '55mm',  col: '#35D07F', x: 14, y: 75 },
                  ].map((o, i) => (
                    <div key={i} className="absolute" style={{ left: `${o.x}%`, top: `${o.y}%` }}>
                      {/* Onion circle */}
                      <div className="w-14 h-14 rounded-full bg-[#3a2a10]/60 border border-[rgba(180,140,60,0.3)] relative">
                        {/* Detection box */}
                        <div
                          className="absolute -inset-3 border pointer-events-none"
                          style={{ borderColor: o.col + '80' }}
                        />
                        {/* Label badge */}
                        <div
                          className="absolute -top-8 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[9px] font-mono font-bold whitespace-nowrap"
                          style={{ background: o.col + '20', color: o.col, border: `1px solid ${o.col}55` }}
                        >
                          {o.grade === 'U' ? 'URS' : o.grade === '?' ? 'REVIEW' : `GRADE A`} {o.mm}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Corner watermark */}
                <div className="absolute bottom-3 right-3">
                  <p className="tech-label text-[8px] text-muted-blue/40">PROTOTYPE VISUALISATION</p>
                </div>
              </div>
            </div>

            {/* Label below */}
            <p className="tech-label text-[9px] text-center mt-3 text-muted-blue">
              Computer vision detection overlay · illustrative
            </p>
          </div>

        </div>
      </div>
    </section>
  )
}
