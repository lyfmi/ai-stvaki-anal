/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        appBg: "#0A0A0A",
        surface: "#111111",
        surfaceElevated: "#161616",
        borderSubtle: "#1F1F1F",
        accent: "#00FF9D",
        accentMuted: "#00FF9D33",
        textPrimary: "#F5F5F5",
        textMuted: "#737373",
        danger: "#FF453A",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        container: "1.25rem",
        containerLg: "1.75rem",
      },
      fontSize: {
        xxs: "0.625rem",
      },
    },
  },
  plugins: [],
};
