/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: "#0D0D12",
        champagne: "#C9A84C",
        ivory: "#FAF8F5",
        slateCustom: "#2A2A35",
        emeraldCustom: "#0F766E", // Emerald green for signals/wins
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        drama: ["Playfair Display", "serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}

