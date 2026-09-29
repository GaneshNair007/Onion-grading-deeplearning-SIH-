import { useEffect, useRef } from 'react'

export default function ReportShowcase() {
  const sectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
        }
      },
      { threshold: 0.2 }
    )

    if (sectionRef.current) observer.observe(sectionRef.current)

    return () => observer.disconnect()
  }, [])

  return (
    <section className="bg-premium-paper py-32 px-8 md:px-16 flex flex-col items-center">
      <div ref={sectionRef} className="w-full max-w-5xl reveal-on-scroll">
        <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-premium-charcoal mb-16 text-center">
          The batch, at a glance.
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12 border-t border-premium-charcoal/10 pt-16">
          <div className="flex flex-col items-center text-center">
            <span className="text-5xl md:text-7xl font-light text-premium-charcoal mb-4">68<span className="text-3xl">%</span></span>
            <span className="text-sm tracking-wide font-medium text-premium-charcoal/60 uppercase">Grade A</span>
          </div>
          
          <div className="flex flex-col items-center text-center">
            <span className="text-5xl md:text-7xl font-light text-premium-olive mb-4">21<span className="text-3xl">%</span></span>
            <span className="text-sm tracking-wide font-medium text-premium-charcoal/60 uppercase">Grade URS</span>
          </div>

          <div className="flex flex-col items-center text-center">
            <span className="text-5xl md:text-7xl font-light text-premium-copper mb-4">8<span className="text-3xl">%</span></span>
            <span className="text-sm tracking-wide font-medium text-premium-charcoal/60 uppercase">Manual review</span>
          </div>

          <div className="flex flex-col items-center text-center">
            <span className="text-5xl md:text-7xl font-light text-premium-charcoal/40 mb-4">3<span className="text-3xl">%</span></span>
            <span className="text-sm tracking-wide font-medium text-premium-charcoal/60 uppercase">Rejected</span>
          </div>
        </div>
      </div>
    </section>
  )
}
