export default function PremiumHero() {
  return (
    <section className="relative h-screen w-full bg-premium-black overflow-hidden flex items-end pb-24 px-8 md:px-16">
      {/* Background Image Placeholder */}
      <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-[#1a1a1a] to-[#0a0a0a]">
        <img 
          src="https://images.unsplash.com/photo-1620574387735-3624d75b2dbc?q=80&w=2938&auto=format&fit=crop" 
          alt="Close up of onion skin" 
          className="w-full h-full object-cover opacity-40 mix-blend-luminosity"
        />
        {/* Subtle gradient for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-premium-black via-premium-black/40 to-transparent" />
      </div>

      <div className="relative z-10 max-w-4xl text-premium-cream">
        <p className="text-sm font-medium tracking-wide uppercase mb-6 opacity-80 animate-fade-in">Onion quality assessment</p>
        <h1 className="text-5xl md:text-8xl font-medium tracking-tight mb-8 leading-none opacity-0 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          A clearer view of<br />onion quality.
        </h1>
        <p className="text-lg md:text-2xl text-premium-cream/80 max-w-2xl font-light leading-relaxed mb-10 opacity-0 animate-slide-up" style={{ animationDelay: '0.4s' }}>
          Calibrated visual inspection with acoustic screening for more transparent procurement decisions.
        </p>
        <div className="opacity-0 animate-slide-up" style={{ animationDelay: '0.6s' }}>
          <button className="px-8 py-4 bg-premium-cream text-premium-charcoal text-sm font-medium hover:bg-white transition-colors duration-300">
            Explore the system
          </button>
        </div>
      </div>
    </section>
  )
}
