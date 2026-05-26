/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"Roboto Mono"', 'monospace'],
        sans: ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        bg:       '#0d0d0d',
        surface:  '#141414',
        border:   '#222222',
        muted:    '#3a3a3a',
        dim:      '#888888',
        text:     '#e8e8e8',
        accent:   '#7aff8a',   /* muted terminal green */
        danger:   '#ff5f5f',
        warn:     '#f0b429',
      },
      animation: {
        'fade-up':   'fadeUp 0.18s ease both',
        'blink':     'blink 1s step-end infinite',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '0.3', transform: 'scale(0.8)' },
          '50%':      { opacity: '1',   transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}