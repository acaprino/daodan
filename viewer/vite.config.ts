import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig, type Plugin } from 'vite';

// The pages take their styles from Sigrid alone. Any other stylesheet stops the build.
function systemStyles(): Plugin {
  const css = dirname(fileURLToPath(import.meta.resolve('@acaprino/sigrid/styles.css')));
  return {
    name: 'system-styles', enforce: 'pre',
    transform(_source, id) {
      const path = id.split('?')[0];
      if (!path.endsWith('.css')) return;
      const fromSystem = relative(css, path);
      if (isAbsolute(fromSystem) || fromSystem === '..' || fromSystem.startsWith('..' + sep)) {
        this.error(`The pages' styles are @acaprino/sigrid's only: ${path}`);
      }
    },
  };
}

// Include notices from the packages in each emitted page. The ELK worker has a separate build.
function licenseNotices(viewer: boolean): Plugin {
  return {
    name: 'license-notices',
    generateBundle(_options, bundle) {
      const directories = new Set<string>();
      if (viewer) directories.add(resolve('node_modules/elkjs'));
      for (const chunk of Object.values(bundle)) {
        if (chunk.type !== 'chunk') continue;
        for (const id of Object.keys(chunk.modules)) {
          const path = id.replaceAll('\\', '/');
          const offset = path.lastIndexOf('/node_modules/');
          if (offset < 0) continue;
          const parts = path.slice(offset + '/node_modules/'.length).split('/');
          const name = parts[0].startsWith('@') ? parts.slice(0, 2).join('/') : parts[0];
          const directory = resolve(path.slice(0, offset), 'node_modules', name);
          if (existsSync(join(directory, 'package.json'))) directories.add(directory);
        }
      }
      const notices = [...directories].map(directory => {
        const pkg = JSON.parse(readFileSync(join(directory, 'package.json'), 'utf8'));
        const license = readdirSync(directory).find(name => /^licen[cs]e/i.test(name));
        const text = license ? readFileSync(join(directory, license), 'utf8').replaceAll('\r\n', '\n').trim() : pkg.license;
        return `${pkg.name} ${pkg.version} (${pkg.license})\n\n${text}`;
      }).sort();
      this.emitFile({ type: 'asset', fileName: 'LICENSES.txt', source: notices.join('\n\n----------------\n\n') + '\n' });
    },
  };
}

// The pages, by the mode they are built in: the folder a page is in, and where it goes. The map is the one without a mode of its own;
// `start` is the page inside Daodan's window, built by its workflow and not committed.
const PAGES: Record<string, [root: string, outDir: string]> = {
  app: ['app', '../../daodan/assets/app'],
  start: ['start', '../../apps/desktop/start'],
  pipeline: ['pipeline', '../../docs/pipeline'],  // the tree of the pipeline, a page of the documentation
};
const MAP: [string, string] = ['.', '../daodan/assets/viewer'];

export default defineConfig(({ mode }) => ({
  root: (PAGES[mode] ?? MAP)[0],
  publicDir: resolve('public'),
  base: './',
  plugins: [systemStyles(), licenseNotices(!PAGES[mode])],
  build: {
    outDir: (PAGES[mode] ?? MAP)[1],
    emptyOutDir: true, chunkSizeWarningLimit: 2500,
  },
  worker: { format: 'es' },
}));
