/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1E40AF',
          foreground: '#FFFFFF',
        },
        secondary: {
          DEFAULT: '#7C3AED',
          foreground: '#FFFFFF',
        },
        success: {
          DEFAULT: '#059669',
          foreground: '#FFFFFF',
        },
        warning: {
          DEFAULT: '#D97706',
          foreground: '#FFFFFF',
        },
        danger: {
          DEFAULT: '#DC2626',
          foreground: '#FFFFFF',
        },
        surface: '#F8FAFC',
        card: '#FFFFFF',
        border: '#E2E8F0',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
