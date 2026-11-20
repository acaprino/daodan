import { build } from "esbuild";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

const options = {
  bundle: true,
  minify: true,
  format: "iife",
  target: ["es2020"],
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "linked",
};
await build({ ...options, entryPoints: ["src/index.tsx"], outfile: "smoothui.bundle.js" });
execFileSync(process.execPath, [resolve("node_modules/@tailwindcss/cli/dist/index.mjs"), "-i", "src/theme.css", "-o", "smoothui.css", "--minify"], { stdio: "inherit" });
