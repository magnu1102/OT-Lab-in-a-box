import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api/history": "http://localhost:8001",
      "/api": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
