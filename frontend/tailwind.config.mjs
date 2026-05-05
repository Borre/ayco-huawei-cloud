/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        gs: {
          navy: '#1B2A4A',
          'navy-light': '#2A3F6B',
          blue: '#0066B3',
          'blue-light': '#0080E0',
          gold: '#C5A55A',
          'gold-light': '#D4B86A',
          white: '#FFFFFF',
          'gray-50': '#F8F9FA',
          'gray-100': '#E9ECEF',
          'gray-200': '#DEE2E6',
          'gray-300': '#CED4DA',
          'gray-600': '#6C757D',
          'gray-900': '#212529',
        },
        risk: {
          low: '#22C55E',
          medium: '#F59E0B',
          high: '#EF4444',
          critical: '#7C2D12',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #1B2A4A 0%, #0066B3 100%)',
        'card-gradient': 'linear-gradient(180deg, rgba(27,42,74,0.02) 0%, rgba(0,102,179,0.05) 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'gauge-fill': 'gaugeFill 1.5s ease-out forwards',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'counter': 'counter 2s ease-out forwards',
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
        gaugeFill: {
          '0%': { 'stroke-dashoffset': '283' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [],
};
