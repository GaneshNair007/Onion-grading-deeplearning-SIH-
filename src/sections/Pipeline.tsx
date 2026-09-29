import { useState } from 'react'

const nodes = [
  {
    id: 'CAPTURE',
    label: 'CAPTURE',
    desc: 'The officer photographs onions arranged in a single layer with a calibration reference card in frame.',
  },
  {
    id: 'VISION',
    label: 'VISION',
    desc: 'Computer vision detects every individual onion and identifies visible surface defects.',
  },
  {
    id: 'CALIBRATION',
    label: 'CALIBRATION',
    desc: 'The calibration reference converts image-pixel measurements into estimated real-world diameter in millimetres.',
  },
  {
    id: 'RULE ENGINE',
    label: 'RULE ENGINE',
    desc: 'The active procurement policy is applied consistently — configurable Grade A / URS thresholds, defect rules and sprouting policy.',
  },
  {
    id: 'BATCH ANALYSIS',
    label: 'BATCH ANALYSIS',
    desc: 'The system calculates batch-level grade distribution percentages across all detected onions.',
  },
  {
    id: 'DIGITAL REPORT',
    label: 'DIGITAL REPORT',
    desc: 'An evidence-backed digital report is generated with annotated images, reason codes, policy version and QR code.',
  },
]

export default function Pipeline() {
  const [active, setActive] = useState<string | null>(null)

  return (
    <section id="technology" className="section-pad bg-white relative overflow-hidden">
      <div className="absolute inset-0 grid-overlay opacity-[0.03] pointer-events-none invert" />

      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="tech-label-cyan mb-4 text-black">System architecture</p>
          <h2 className="text-navy font-bold leading-[1.05]" style={{ fontSize: 'clamp(2rem, 4vw, 3.5rem)' }}>
            One capture.<br />Multiple intelligence layers.
          </h2>
        </div>

        {/* Pipeline nodes — horizontal scroll on mobile */}
        <div className="flex flex-col md:flex-row items-stretch gap-0 overflow-x-auto pb-2">
          {nodes.map((node, i) => (
            <div key={node.id} className="flex flex-col md:flex-row items-center flex-1">
              {/* Node */}
              <button
                className={`
                  w-full flex-1 p-5 text-left transition-all duration-200 border
                  ${active === node.id
                    ? 'bg-cyan/10 border-cyan/50 text-black'
                    : 'bg-off-white border-black/10 hover:bg-[#F8FAFC] text-navy-mid/70'}
                `}
                onMouseEnter={() => setActive(node.id)}
                onMouseLeave={() => setActive(null)}
                onClick={() => setActive(active === node.id ? null : node.id)}
              >
                <p className="font-mono text-[9px] text-muted-blue mb-2">{String(i + 1).padStart(2, '0')}</p>
                <p className="tech-label text-[10px] font-bold tracking-widest mb-3 text-current">{node.label}</p>
                <p className={`text-xs leading-relaxed transition-colors duration-200 ${active === node.id ? 'text-navy' : 'text-navy-mid/50'}`}>
                  {node.desc}
                </p>
              </button>

              {/* Arrow connector */}
              {i < nodes.length - 1 && (
                <div className="hidden md:flex items-center justify-center w-8 shrink-0 text-muted-blue/40">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M1 8h12M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        <p className="tech-label text-[9px] text-center mt-6 text-muted-blue/50">
          Explore each stage to view its role.
        </p>
      </div>
    </section>
  )
}
