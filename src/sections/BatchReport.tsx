const grades = [
  { label: 'Grade A',       pct: 64.6, col: '#35D07F' },
  { label: 'Grade URS',     pct: 18.7, col: '#27C7E8' },
  { label: 'Manual Review', pct:  8.3, col: '#F2B84B' },
  { label: 'Rejected',      pct:  8.3, col: '#FF5D5D' },
]

const reportFields = [
  { k: 'REPORT ID',          v: 'OAI-RPT-0047'   },
  { k: 'BATCH ID',           v: 'NASHIK-047'      },
  { k: 'FARMER / SUPPLIER',  v: 'Demo Supplier'   },
  { k: 'PROCUREMENT CENTRE', v: 'Centre 04'       },
  { k: 'OFFICER',            v: 'Demo Officer'    },
  { k: 'DATE / TIME',        v: '23 Sep 2026'     },
  { k: 'POLICY VERSION',     v: 'v2.1'            },
  { k: 'URS STATUS',         v: 'ENABLED'         },
]

export default function BatchReport() {
  return (
    <section className="section-pad bg-navy relative overflow-hidden">
      <div className="absolute inset-0 grid-overlay opacity-35 pointer-events-none" />

      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">

          {/* Left — copy */}
          <div>
            <p className="tech-label-cyan mb-4">Batch intelligence</p>
            <h2 className="text-off-white font-bold leading-[1.05] mb-6" style={{ fontSize: 'clamp(2rem, 4vw, 3.5rem)' }}>
              From individual onions<br />to batch-level decisions.
            </h2>
            <p className="text-soft-white/55 text-lg leading-relaxed mb-10">
              Every inspection produces a structured grade distribution and an evidence-backed report—giving buyers, suppliers, and procurement teams a shared record of the decision.
            </p>

            {/* Grade bars */}
            <div className="space-y-4">
              {grades.map(g => (
                <div key={g.label}>
                  <div className="flex justify-between mb-1.5">
                    <span className="tech-label text-[10px]">{g.label}</span>
                    <span className="font-mono text-xs font-bold" style={{ color: g.col }}>{g.pct}%</span>
                  </div>
                  <div className="h-1.5 bg-[rgba(255,255,255,0.06)] rounded-none overflow-hidden">
                    <div
                      className="h-full transition-all duration-1000"
                      style={{ width: `${g.pct}%`, background: g.col }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <p className="tech-label text-[9px] mt-4 text-muted-blue/60">PROTOTYPE DATA · ILLUSTRATIVE VALUES</p>
          </div>

          {/* Right — report card */}
          <div className="tech-panel-bright overflow-hidden">
            {/* Header bar */}
            <div className="bg-[#0B2540] px-6 py-4 flex items-center justify-between border-b border-[rgba(255,255,255,0.07)]">
              <div>
                <p className="text-off-white font-semibold text-sm tracking-wide">EVERY DECISION LEAVES AUDIT EVIDENCE.</p>
                <p className="tech-label text-[9px] mt-0.5">Batch inspection report</p>
              </div>
              <span className="tech-label text-[9px] text-success border border-success/30 px-2 py-1">COMPLETE</span>
            </div>

            {/* Report fields */}
            <div className="grid grid-cols-2 divide-x divide-y divide-[rgba(255,255,255,0.06)]">
              {reportFields.map(({ k, v }) => (
                <div key={k} className="px-5 py-3">
                  <p className="tech-label text-[8px] mb-0.5">{k}</p>
                  <p className="font-mono text-xs text-off-white font-medium">{v}</p>
                </div>
              ))}
            </div>

            {/* Grade summary */}
            <div className="border-t border-[rgba(255,255,255,0.07)] divide-y divide-[rgba(255,255,255,0.06)]">
              {grades.map(g => (
                <div key={g.label} className="flex items-center gap-3 px-6 py-3">
                  <div className="w-2 h-2 rounded-sm shrink-0" style={{ background: g.col }} />
                  <span className="tech-label text-[9px] flex-1">{g.label}</span>
                  <span className="font-mono text-sm font-bold" style={{ color: g.col }}>{g.pct}%</span>
                </div>
              ))}
            </div>

            {/* Footer CTA */}
            <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.07)] flex items-center justify-between">
              <p className="tech-label text-[8px] text-muted-blue/50">OAI-PROTO-01 · PROTOTYPE DATA</p>
              <button className="btn-secondary text-[10px] py-1.5 px-4">View sample report</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
