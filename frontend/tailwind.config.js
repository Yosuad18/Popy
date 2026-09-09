/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#faf8f5',
        surface: '#ffffff',
        ink: '#1a1a2e',
        muted: '#6b7280',
        accent: {
          DEFAULT: '#10b981',
          hover: '#059669',
        },
        secondary: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
        },
        chip: {
          bg: '#f0fdf4',
        },
        border: '#e5e7eb',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        body: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'bubble': '18px',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(16, 185, 129, 0.15)',
        'glow-sm': '0 0 10px rgba(16, 185, 129, 0.1)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.1)',
      },
      animation: {
        'fade-up': 'fadeUp 0.3s ease-out forwards',
        'bounce-dot': 'bounceDot 1.4s infinite ease-in-out both',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'slide-in': 'slideIn 0.2s ease-out forwards',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(16, 185, 129, 0.1)' },
          '50%': { boxShadow: '0 0 20px rgba(16, 185, 129, 0.25)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-4px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
