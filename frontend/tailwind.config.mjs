/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        gs: {
          navy: '#0a0e17', // Darker navy for premium dark mode
          'navy-light': '#1a1f2e',
          blue: '#00d4aa', // Vibrant emerald/teal for primary actions
          'blue-light': '#00f2c3',
          gold: '#C5A55A',
          'gold-light': '#D4B86A',
          white: '#FFFFFF',
          'gray-50': '#F8F9FA',
          'gray-100': '#E9ECEF',
          'gray-200': '#DEE2E6',
          'gray-300': '#CED4DA',
          'gray-400': '#9DA4B0',
          'gray-500': '#7C8595',
          'gray-600': '#9DA4B0', // Bumped from #6C757D for WCAG AA contrast on dark bg
          'gray-900': '#212529',
        },
        risk: {
          low: '#00d4aa',
          medium: '#ffd700',
          high: '#ff8c00',
          critical: '#ff4444',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #0a0e17 0%, #1a1f2e 100%)',
        'glass-gradient': 'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      },
    },
  },
  plugins: [],
};
