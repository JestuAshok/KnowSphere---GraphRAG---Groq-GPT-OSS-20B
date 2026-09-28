/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand palette — matching reference image
        sidebar: {
          bg: '#0F0E2A',
          hover: '#1a1850',
          active: '#7C3AED',
          text: '#A0A0C8',
          'text-active': '#FFFFFF',
        },
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#7C3AED',  // primary purple
          700: '#6D28D9',
          800: '#5B21B6',
          900: '#4C1D95',
          950: '#2E1065',
        },
        page: '#F5F4FF',  // lavender-tinted white
        card: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #0F0E2A 0%, #1a0533 40%, #2d1b69 100%)',
        'card-gradient': 'linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)',
        'brand-gradient': 'linear-gradient(90deg, #7C3AED, #4F46E5)',
      },
      boxShadow: {
        card: '0 4px 24px rgba(124, 58, 237, 0.08)',
        'card-hover': '0 8px 32px rgba(124, 58, 237, 0.16)',
        glow: '0 0 20px rgba(124, 58, 237, 0.3)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'float-delayed': 'float 6s ease-in-out 2s infinite',
        'float-slow': 'float 8s ease-in-out 1s infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'fade-up': 'fade-up 0.4s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 10px rgba(124, 58, 237, 0.3)' },
          '50%': { boxShadow: '0 0 25px rgba(124, 58, 237, 0.6)' },
        },
        'slide-in-right': {
          from: { transform: 'translateX(100%)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-up': {
          from: { transform: 'translateY(20px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
