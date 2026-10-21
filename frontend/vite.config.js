import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
  build: {
    rollupOptions: {
      output: {
        // bibliotecas pesadas em chunks próprios: cache melhor e bundle inicial menor
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.js"],
    include: ["src/**/*.test.{js,jsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/lib/**", "src/services/**", "src/components/ui.jsx", "src/components/Toast.jsx", "src/AuthContext.jsx", "src/pages/Login.jsx", "src/App.jsx"],
      exclude: ["src/**/*.test.*"],
    },
  },
});
