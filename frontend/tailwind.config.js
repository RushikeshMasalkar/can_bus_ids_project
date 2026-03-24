/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cybersecurity color palette
        cyber: {
          darker: '#0a0a0f',
          dark: '#0d1117',
          bg: '#161b22',
          surface: '#21262d',
          border: '#30363d',
          muted: '#484f58',
        },
        neon: {
          cyan: '#00f5ff',
          blue: '#0ea5e9',
          purple: '#a855f7',
          pink: '#ec4899',
        },
        threat: {
          critical: '#ff0040',
          high: '#ff4444',
          medium: '#ff8800',
          low: '#ffcc00',
          safe: '#00ff88',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        display: ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 2s linear infinite',
        'threat-pulse': 'threat-pulse 0.5s ease-in-out infinite',
        'slide-in': 'slide-in 0.3s ease-out',
        'fade-in': 'fade-in 0.5s ease-out',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 245, 255, 0.5), 0 0 10px rgba(0, 245, 255, 0.3)' },
          '100%': { boxShadow: '0 0 10px rgba(0, 245, 255, 0.8), 0 0 20px rgba(0, 245, 255, 0.5), 0 0 30px rgba(0, 245, 255, 0.3)' },
        },
        scan: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'threat-pulse': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(255, 0, 64, 0.8)' },
          '50%': { opacity: '0.7', boxShadow: '0 0 40px rgba(255, 0, 64, 1)' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'neon-cyan': '0 0 10px rgba(0, 245, 255, 0.5), 0 0 20px rgba(0, 245, 255, 0.3)',
        'neon-red': '0 0 10px rgba(255, 0, 64, 0.5), 0 0 20px rgba(255, 0, 64, 0.3)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
      },
    },
  },
  plugins: [],
}
