const techItems = [
  'COMPUTER VISION',
  'SIZE CALIBRATION',
  'RULE ENGINE',
  'AI DETECTION',
  'DIGITAL EVIDENCE',
  'AUDIT TRAIL',
]

export default function TechStrip() {
  return (
    <section className="bg-[#0A1E30] border-y border-[rgba(255,255,255,0.07)]">
      <div className="max-w-8xl mx-auto px-6 md:px-10 py-5">
        <div className="flex flex-wrap items-center justify-center md:justify-between gap-y-3">
          {techItems.map((item, i) => (
            <div key={item} className="flex items-center gap-0">
              <span className="tech-label text-[10px] text-soft-white/50 hover:text-cyan transition-colors duration-200 cursor-default px-4">
                {item}
              </span>
              {i < techItems.length - 1 && (
                <span className="hidden md:block h-4 w-px bg-[rgba(255,255,255,0.10)]" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
