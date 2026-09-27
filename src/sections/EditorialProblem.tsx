import { useEffect, useRef } from 'react'

export default function EditorialProblem() {
  const sectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
        }
      },
      { threshold: 0.1 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <section className="py-32 md:py-48 px-8 md:px-16 bg-premium-paper flex justify-center text-premium-charcoal">
      <div 
        ref={sectionRef} 
        className="max-w-4xl text-center reveal-on-scroll"
      >
        <h2 className="text-4xl md:text-6xl font-medium tracking-tight mb-8">
          Quality is not always visible.
        </h2>
        <p className="text-xl md:text-3xl font-light text-premium-charcoal/70 leading-relaxed max-w-3xl mx-auto">
          Surface inspection can miss internal-quality risk. Our prototype combines calibrated visual assessment with controlled acoustic screening to surface what the camera cannot see.
        </p>
      </div>
    </section>
  )
}
