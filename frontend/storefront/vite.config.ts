/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/users": "http://localhost:8000",
      "/api/products": "http://localhost:8001",
      "/api/inventory": "http://localhost:8002",
      "/api/orders": "http://localhost:8003",
      "/api/payments": "http://localhost:8004",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
