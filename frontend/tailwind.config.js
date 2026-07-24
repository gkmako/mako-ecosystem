/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mako: {
          dark: '#002b25',
          surface: '#313d2f',
          sidebar: '#334f3a',
          primary: '#336649',
          secondary: '#334f3a',
          message: '#b5e3d8',
          border: '#334f3a',
        },
      },
    },
  },
  plugins: [],
}
