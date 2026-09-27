/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        /* ── Core Backgrounds ── */
        'bg-base':    '#FEFCFB',        // warm white
        'bg-cream':   '#FBF7F4',        // cream off-white
        'bg-blush':   '#FFF5F5',        // lightest blush
        'bg-soft':    '#F8F4F2',        // warm gray

        /* ── Glass ── */
        'glass-panel':     'rgba(255, 252, 251, 0.65)',
        'glass-border':    'rgba(180, 140, 130, 0.12)',
        'glass-highlight': 'rgba(255, 255, 255, 0.9)',

        /* ── Text ── */
        'text-primary':   '#2D1F1A',    // warm dark brown
        'text-secondary': '#7A6860',    // warm medium
        'text-muted':     '#B0A098',    // warm light

        /* ── Onion Pink Accents ── */
        'onion':          '#D4687A',    // primary onion pink
        'onion-light':    '#F2CED4',    // pastel pink
        'onion-soft':     '#FAE8EB',    // very soft pink
        'onion-deep':     '#B8475D',    // deeper onion

        /* ── Supporting pastels ── */
        'pastel-lavender': '#E8DFFE',
        'pastel-sage':     '#D8EDDA',
        'pastel-peach':    '#FFE5D9',
        'pastel-sky':      '#DDE8F8',

        /* ── Functional ── */
        'accent-success': '#5BA67A',
        'accent-warn':    '#D4915E',
        'accent-info':    '#7B93BD',
      },
      boxShadow: {
        'glass':       '0 8px 40px -12px rgba(180, 140, 130, 0.12)',
        'glass-hover': '0 16px 60px -16px rgba(180, 140, 130, 0.18)',
        'blush':       '0 12px 40px -8px rgba(212, 104, 122, 0.15)',
        'soft':        '0 2px 16px -4px rgba(0,0,0,0.04)',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      keyframes: {
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-12px)' },
        },
        'shimmer': {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'ripple': {
          '0%':   { transform: 'scale(0)', opacity: '0.6' },
          '100%': { transform: 'scale(4)', opacity: '0' },
        },
        'peel': {
          '0%':   { transform: 'rotateX(0deg) translateZ(0px)', opacity: '1' },
          '100%': { transform: 'rotateX(-90deg) translateZ(40px)', opacity: '0' },
        },
        'splash-drop': {
          '0%':   { transform: 'translateY(-80px) scale(0.8)', opacity: '0' },
          '40%':  { transform: 'translateY(0px) scale(1)', opacity: '1' },
          '60%':  { transform: 'translateY(-8px) scale(1.02)', opacity: '1' },
          '80%':  { transform: 'translateY(2px) scale(0.99)', opacity: '1' },
          '100%': { transform: 'translateY(0px) scale(1)', opacity: '1' },
        },
      },
      animation: {
        'float':       'float 6s ease-in-out infinite',
        'shimmer':     'shimmer 3s ease-in-out infinite',
        'ripple':      'ripple 2s ease-out forwards',
        'peel':        'peel 0.8s ease-in-out forwards',
        'splash-drop': 'splash-drop 1s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
      },
    },
  },
  plugins: [],
}
