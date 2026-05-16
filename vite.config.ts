import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// Backend (portal_server.py) runs on port 8001 by default (orama-system convention).
// Vite dev server proxies /api/* there so the React app uses same-origin paths.
// Override with PORTAL_URL env var if your portal lives elsewhere.
const PORTAL_URL = process.env.PORTAL_URL ?? "http://localhost:8001";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Mirror the `@/*` → `./src/*` mapping declared in tsconfig.json.
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: PORTAL_URL,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom"],
          query: ["@tanstack/react-query"],
        },
      },
    },
  },
});
