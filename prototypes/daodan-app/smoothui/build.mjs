import { build } from "esbuild";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

await build({
  entryPoints: ["src/index.tsx"],
  bundle: true,
  minify: true,
  format: "iife",
  target: ["es2020"],
  jsx: "automatic",
  outfile: "smoothui.bundle.js",
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "linked",
});
execFileSync(process.execPath, [resolve("node_modules/@tailwindcss/cli/dist/index.mjs"), "-i", "src/theme.css", "-o", "smoothui.css", "--minify"], { stdio: "inherit" });
