// FILE: frontend/tailwind.config.js - BUGS FIXED: 2
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        primary: {
          DEFAULT: '#1A6FD4',
          hover: '#1560BC',
          light: '#EBF4FF',
          muted: '#5B8FD9',
        },
        primaryHover: '#1560BC',
        primaryLight: '#EBF4FF',
        primaryMuted: '#5B8FD9',
        bg: {
          base: 'var(--color-bg-base)',
          card: 'var(--color-bg-card)',
          sidebar: 'var(--color-bg-sidebar)',
          hover: 'var(--color-bg-hover)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          strong: 'var(--color-border-strong)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          inverse: 'var(--color-text-inverse)',
        },
        success: {
          DEFAULT: 'var(--color-success)',
          bg: 'var(--color-success-bg)',
        },
        danger: {
          DEFAULT: 'var(--color-danger)',
          bg: 'var(--color-danger-bg)',
        },
        warning: {
          DEFAULT: 'var(--color-warning)',
          bg: 'var(--color-warning-bg)',
        },

        // Compatibility aliases used by existing pages/components.
        surface: 'var(--color-bg-base)',
        'surface-container-lowest': 'var(--color-bg-card)',
        'surface-container-low': 'var(--color-bg-hover)',
        'surface-container-high': '#eaf0fb',
        'surface-container-highest': '#dfe7f5',
        'surface-variant': 'var(--color-bg-hover)',
        'outline-variant': 'var(--color-border)',
        outline: 'var(--color-border-strong)',
        'on-surface': 'var(--color-text-primary)',
        'on-surface-variant': 'var(--color-text-secondary)',
        secondary: 'var(--color-primary-muted)',
        tertiary: 'var(--color-success)',
        'tertiary-fixed': '#d8f5e8',
        'tertiary-fixed-dim': 'var(--color-success)',
        'secondary-fixed': '#d9e8ff',
        'secondary-fixed-dim': '#9fc4f4',
        'secondary-container': '#d9e8ff',
        'error-container': 'var(--color-danger-bg)',
        error: 'var(--color-danger)',
        'on-error': 'var(--color-text-inverse)',
        'on-error-container': '#7f1d2d',
        'on-primary': 'var(--color-text-inverse)',
        'on-secondary': 'var(--color-text-inverse)',
        'on-tertiary': 'var(--color-text-inverse)',
        'on-tertiary-container': 'var(--color-success)',
      },
      boxShadow: {
        xs: 'var(--shadow-xs)',
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        card: 'var(--shadow-card)',
      },
      borderRadius: {
        card: '10px',
        badge: '999px',
        btn: '8px',
      },
    },
  },
  plugins: [],
};
