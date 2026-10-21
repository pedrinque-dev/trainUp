/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13294B", // azul-marinho da logo (texto, títulos, sidebar)
        brand: { DEFAULT: "#0B8FDB", dark: "#1A73C8", deeper: "#155FAA", soft: "#E6F3FC" },
        accent: { DEFAULT: "#9BD64A", soft: "#EDF8DB" }, // verde-limão: só como preenchimento
        teal: "#5FC28A",
        paper: "#F3F6FA",
        line: "#DDE4EE",
        muted: "#5B6B80",
        ok: "#1F7A45", // verde escuro legível como texto
        danger: "#C23B3B",
        warn: "#9A6700",
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      boxShadow: { card: "0 1px 2px rgba(19,41,75,.05), 0 4px 16px rgba(19,41,75,.04)" },
    },
  },
  plugins: [],
};
