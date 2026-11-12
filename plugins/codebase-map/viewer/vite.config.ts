import { defineConfig } from 'vite';

// The compiled viewer is committed beside the scripts that serve it (`visual.py serve`).
export default defineConfig({
  base: './',
  build: { outDir: '../assets/viewer', emptyOutDir: true, chunkSizeWarningLimit: 2500 },
  worker: { format: 'es' },
});
