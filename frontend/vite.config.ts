import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Matches scripts/lib.sh's FRONTEND_PORT default -- so a bare `npm run dev` (no scripts,
  // no --port flag) lands on the same port scripts/start.sh uses by default, and backend
  // config.py's own FRONTEND_PORT fallback stays correct for both paths. A `--port` CLI flag
  // (as scripts/start.sh always passes) overrides this regardless.
  server: {
    port: 8001,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
  },
});
