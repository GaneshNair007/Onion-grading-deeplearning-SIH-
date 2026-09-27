import { useEffect, useRef } from 'react'

export default function HardwareShowcase() {
  const textRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
        }
      },
      { threshold: 0.5 }
    )

    if (textRef.current) {
      observer.observe(textRef.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <section className="relative h-screen w-full bg-premium-charcoal flex items-center justify-center overflow-hidden">
      {/* Hardware Photography Placeholder */}
      <div className="absolute inset-0">
        <img 
          src="https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2940&auto=format&fit=crop" 
          alt="Hardware Prototype" 
          className="w-full h-full object-cover opacity-30 mix-blend-luminosity"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-premium-charcoal/80 via-transparent to-premium-charcoal/80" />
      </div>

      <div ref={textRef} className="relative z-10 text-center max-w-3xl px-8 reveal-on-scroll">
        <h2 className="text-3xl md:text-5xl font-light text-premium-cream leading-tight">
          A compact inspection station designed for real procurement environments. Each element has a defined role in the inspection workflow.
        </h2>
      </div>
    </section>
  )
}
