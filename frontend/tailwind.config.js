/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class', // Keeps your dark mode toggle working
  theme: {
    extend: {
      colors: {
        isstech: {
          // Bright Neon Green for primary actions/highlights
          primary: '#49E97F', 
          
          // Deepest Green for the main page background
          dark: '#08271E', 
          
          // Lighter Dark Green for cards/sections
          surface: '#11352A', 
          
          // Light Gray for primary text
          light: '#F2F2F2',
          
          // Pure Black for harsh contrast if needed
          black: '#000000', 
        }
      },
      fontFamily: {
        // "Clean lines and structured typography"
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    }
  },
  plugins: [],
}