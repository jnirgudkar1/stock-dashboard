/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#1f2937', // dark background
        card: '#2d3748',       // card surface
        primary: '#6366f1',    // button color (indigo-500)
        accent: '#10b981',     // highlight text (emerald-500)
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};