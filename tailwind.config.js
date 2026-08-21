/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/renderer/index.html',
    './src/renderer/src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        crypto: {
          bg: '#0B0E14',
          card: '#151922',
          cardHover: '#1B212D',
          border: '#232936',
          accent: '#3B82F6',
          green: '#10B981',
          red: '#EF4444',
          muted: '#8E9AA8',
          text: '#F3F4F6'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    }
  },
  plugins: []
}
