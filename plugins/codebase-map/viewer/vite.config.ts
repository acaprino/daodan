import { execSync } from 'node:child_process';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { defineConfig } from 'vite';

// The notices of every runtime package the build can bundle, read from their own license files.
function licenseNotices() {
  return {
    name: 'license-notices',
    generateBundle() {
      const listed = execSync('npm ls --omit=dev --all --parseable', { encoding: 'utf8' }).split(/\r?\n/).filter(Boolean).slice(1);
      const notices = [...new Set(listed)].sort().flatMap(directory => {
        const manifest = JSON.parse(readFileSync(join(directory, 'package.json'), 'utf8'));
        const file = readdirSync(directory).find(name => /^licen[cs]e/i.test(name));
        const text = file ? readFileSync(join(directory, file), 'utf8').trim() : `License: ${manifest.license ?? 'not declared'}`;
        return [`${manifest.name} ${manifest.version} (${manifest.license ?? 'not declared'})\n\n${text}`];
      });
      this.emitFile({ type: 'asset', fileName: 'LICENSES.txt', source: notices.join('\n\n----------------\n\n') + '\n' });
    },
  };
}

// The compiled viewer is committed beside the scripts that serve it (`visual.py serve`).
export default defineConfig({
  base: './',
  plugins: [licenseNotices()],
  build: { outDir: '../assets/viewer', emptyOutDir: true, chunkSizeWarningLimit: 2500 },
  worker: { format: 'es' },
});
