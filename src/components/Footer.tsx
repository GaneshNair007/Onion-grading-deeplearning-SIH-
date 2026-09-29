export default function Footer() {
  return (
    <footer className="w-full bg-bg-base relative z-10 pt-12 pb-8 border-t border-glass-border">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex flex-col items-center justify-center gap-3 text-center">
          <span className="font-display text-lg font-bold text-onion-deep tracking-[0.15em] uppercase">
            VOSTOK
          </span>
          <span className="text-sm text-text-secondary">
            Vibro-Acoustic & Optical Sensing Technology for Onion Knowledge
          </span>
          <p className="text-xs text-text-muted font-sans mt-2">
            &copy; 2026 VOSTOK
          </p>
        </div>
      </div>
    </footer>
  )
}
