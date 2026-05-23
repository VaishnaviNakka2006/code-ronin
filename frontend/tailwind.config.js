/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        neon: {
          cyan: '#00f3ff',
          magenta: '#ff00e5',
          purple: '#b000ff',
          dark: '#0a0a0f',
          gray: '#1a1a2e',
        }
      },
      fontFamily: {
        mono: ['Fira Code', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      animation: {
        'glitch': 'glitch 0.3s ease-in-out infinite',
        'pulse-neon': 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'scan': 'scan 8s linear infinite',
      },
      keyframes: {
        glitch: {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
        },
        scan: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '0 100%' },
        }
      }
    },
  },
  plugins: [],
}