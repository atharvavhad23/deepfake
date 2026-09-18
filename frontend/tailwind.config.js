/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0b1220',
        panel: '#101a2f',
        accent: '#38bdf8',
        accent2: '#60a5fa',
        success: '#34d399',
        danger: '#f87171',
      },
      boxShadow: {
        glow: '0 24px 80px rgba(56, 189, 248, 0.18)',
      },
      backgroundImage: {
        'forensics-grid':
          'radial-gradient(circle at top left, rgba(56,189,248,0.16), transparent 28%), radial-gradient(circle at 80% 20%, rgba(96,165,250,0.12), transparent 26%), linear-gradient(180deg, #07111f 0%, #050b15 100%)',
      },
    },
  },
  plugins: [],
};
