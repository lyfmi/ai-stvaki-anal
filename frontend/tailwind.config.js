/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // 1win dark palette — https://1win.design/palette
        // Brand Blue (Hue 212), Deep Blue surfaces, Outline Black bg, White text
        appBg: "#000000",
        surface: "#0C1424",
        surfaceElevated: "#111D33",
        borderSubtle: "#1A2D4F",
        accent: "#0075FF",
        accentHover: "#3391FF",
        accentMuted: "#0075FF33",
        brandDeep: "#062654",
        textPrimary: "#FFFFFF",
        textMuted: "#7B8FA8",
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
      boxShadow: {
        accent: "0 0 12px #0075FF33",
      },
    },
  },
  plugins: [],
};
