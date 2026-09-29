import { useEffect, useRef } from 'react'

export default function FeaturePanels() {
  const panel1Ref = useRef<HTMLDivElement>(null)
  const panel2Ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
          }
        })
      },
      { threshold: 0.2 }
    )

    if (panel1Ref.current) observer.observe(panel1Ref.current)
    if (panel2Ref.current) observer.observe(panel2Ref.current)

    return () => observer.disconnect()
  }, [])

  return (
    <section className="bg-premium-cream px-8 md:px-16 py-24 space-y-24">
      
      {/* Computer vision Panel */}
      <div ref={panel1Ref} className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16 items-center reveal-on-scroll">
        <div className="aspect-[4/3] bg-premium-charcoal/5 overflow-hidden">
           <img 
            src="https://images.unsplash.com/photo-1599351431202-1e0f0137899a?q=80&w=2000&auto=format&fit=crop" 
            alt="Onion close up" 
            className="w-full h-full object-cover mix-blend-multiply opacity-80"
          />
        </div>
        <div className="max-w-md">
          <h3 className="text-sm font-medium tracking-widest uppercase text-premium-copper mb-4">Vision</h3>
          <p className="text-2xl md:text-4xl font-light text-premium-charcoal leading-snug">
            Detects individual bulbs, visible condition, size and surface defects.
          </p>
        </div>
      </div>

      {/* Acoustic Panel */}
      <div ref={panel2Ref} className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16 items-center reveal-on-scroll" style={{ transitionDelay: '0.2s' }}>
        <div className="order-2 md:order-1 max-w-md md:ml-auto">
          <h3 className="text-sm font-medium tracking-widest uppercase text-premium-olive mb-4">Acoustic screening</h3>
          <p className="text-2xl md:text-4xl font-light text-premium-charcoal leading-snug">
            Uses a controlled impulse response to flag possible internal-quality risk for review.
          </p>
        </div>
        <div className="order-1 md:order-2 aspect-[4/3] bg-premium-charcoal/5 overflow-hidden">
           <img 
            src="https://images.unsplash.com/photo-1616781295257-2007c6f0927e?q=80&w=2000&auto=format&fit=crop" 
            alt="Acoustic wave representation" 
            className="w-full h-full object-cover mix-blend-multiply opacity-70 grayscale"
          />
        </div>
      </div>

    </section>
  )
}
