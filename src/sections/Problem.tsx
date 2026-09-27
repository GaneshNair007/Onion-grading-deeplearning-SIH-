const panels = [
  {
    num: '01',
    title: 'INCONSISTENCY',
    body: 'Different inspectors can reach different conclusions on the same batch, depending on experience, fatigue or interpretation of standards.',
  },
  {
    num: '02',
    title: 'NO EVIDENCE TRAIL',
    body: 'Manual grading does not naturally produce a detailed, reviewable record that can be audited or disputed after the fact.',
  },
  {
    num: '03',
    title: 'UNEXPLAINED DECISIONS',
    body: 'Farmers and suppliers may not receive a transparent explanation for why a batch was downgraded or rejected.',
  },
]

export default function Problem() {
  return (
    <section id="platform" className="section-pad bg-off-white relative overflow-hidden">
      <div className="absolute inset-0 grid-overlay opacity-[0.03] pointer-events-none invert" />

      <div className="relative z-10 max-w-8xl mx-auto px-6 md:px-10">
        {/* Heading */}
        <div className="max-w-3xl mb-16">
          <p className="tech-label-cyan mb-4 text-black">The inspection gap</p>
          <h2 className="text-navy font-bold leading-[1.05] mb-6" style={{ fontSize: 'clamp(2rem, 4vw, 3.75rem)' }}>
            Procurement should not<br />depend on opinion.
          </h2>
          <p className="text-navy-mid/70 text-lg leading-relaxed">
            Manual grading can produce inconsistent decisions, limited evidence, and disputes between procurement centres and suppliers.
          </p>
        </div>

        {/* Problem panels */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border border-black/10 bg-white">
          {panels.map((p, i) => (
            <div
              key={p.num}
              className={`p-8 hover:bg-[#F8FAFC] transition-colors duration-300 ${i < panels.length - 1 ? 'border-b md:border-b-0 md:border-r border-black/10' : ''}`}
            >
              <p className="font-mono text-xs text-muted-blue mb-5">{p.num}</p>
              <h3 className="tech-label text-black text-[11px] mb-4">{p.title}</h3>
              <p className="text-navy-mid/70 text-sm leading-relaxed">{p.body}</p>
            </div>
          ))}
        </div>

        {/* Bridge line */}
        <div className="mt-16 pt-12 border-t border-black/10">
          <p className="text-navy-mid/50 text-lg font-light italic">
            “What if every grading decision could be measured, explained and recorded?”
          </p>
        </div>
      </div>
    </section>
  )
}
