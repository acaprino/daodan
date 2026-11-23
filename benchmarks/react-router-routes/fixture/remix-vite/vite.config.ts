import { vitePlugin as remix } from "@remix-run/dev";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    remix({
      // vite.config.ts is code: it adds a route the file convention does not name
      routes(defineRoutes) {
        return defineRoutes((route) => {
          route("custom/:id", "custom.tsx", { id: "custom-route" });
        });
      },
    }),
  ],
});
