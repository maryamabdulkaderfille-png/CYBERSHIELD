/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#05070d",
          900: "#0a0e1a",
          800: "#0f1526",
          700: "#161d33",
          600: "#1f2942",
        },
        brand: {
          blue: "#3b82f6",
          cyan: "#22d3ee",
        },
        safe: "#22c55e",
        warning: "#eab308",
        danger: "#ef4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "grid-glow":
          "radial-gradient(circle at 20% 20%, rgba(59,130,246,0.15), transparent 40%), radial-gradient(circle at 80% 0%, rgba(34,211,238,0.12), transparent 40%)",
      },
      boxShadow: {
        glow: "0 0 30px -5px rgba(59,130,246,0.45)",
        "glow-cyan": "0 0 30px -5px rgba(34,211,238,0.45)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
