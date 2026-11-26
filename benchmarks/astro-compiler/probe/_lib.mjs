import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

export const folder = process.cwd();
export const require = createRequire(`${folder}/`);

// The compiler the project's `astro` uses, found from the folder of `astro` with `createRequire`, as `daodan/core/premap/astro_templates.mjs`
// does (so the one the project installed, whether the package manager hoists it (npm) or not (pnpm), and on any Node `astro` runs on).
// Astro 5 and 6 depend on `@astrojs/compiler` (2.x, 4.x), Astro 7 on `@astrojs/compiler-rs`.
export const COMPILERS = ['@astrojs/compiler', '@astrojs/compiler-rs'];
export async function loadCompiler() {
  const astroManifestPath = require.resolve('astro/package.json');
  const astroManifest = JSON.parse(fs.readFileSync(astroManifestPath, 'utf8'));
  const name = COMPILERS.find((n) => astroManifest.dependencies?.[n]);
  if (!name) throw new Error(`astro ${astroManifest.version} declares none of ${COMPILERS.join(', ')}`);
  const fromAstro = createRequire(astroManifestPath);
  const manifestPath = fromAstro.resolve(`${name}/package.json`);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const entry = fromAstro.resolve(name);
  const loaded = await import(pathToFileURL(entry).href);
  const compiler = typeof loaded.parse === 'function' ? loaded : loaded.default;
  return { name, compiler, version: manifest.version, entry, manifest, packageDir: path.dirname(manifestPath), astro: astroManifest.version };
}

export function sources(dir = 'src') {
  const out = [];
  const visit = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) visit(full);
      else if (e.name.endsWith('.astro')) out.push(full.split(path.sep).join('/'));
    }
  };
  visit(dir);
  return out.sort();
}

// Independent ground truth: line and column (1-based, as the compiler writes them) of an offset in a JavaScript string, counting
// UTF-16 code units, and the same counting UTF-8 bytes.
export function lineColUnits(text, offset) {
  let line = 1, col = 1;
  for (let i = 0; i < offset && i < text.length; i++) { if (text[i] === '\n') { line++; col = 1; } else col++; }
  return { line, column: col };
}
export function lineColBytes(text, offset) {
  const bytes = Buffer.from(text, 'utf8');
  let line = 1, col = 1;
  for (let i = 0; i < offset && i < bytes.length; i++) { if (bytes[i] === 0x0a) { line++; col = 1; } else col++; }
  return { line, column: col };
}

// Every node of the tree with its parent: children of a node, the attributes of a tag-like node are listed apart.
export function* walk(node, parent = null, depth = 0) {
  yield { node, parent, depth };
  for (const child of node.children ?? []) yield* walk(child, node, depth + 1);
}

export const point = (p) => (p ? `${p.line}:${p.column}@${p.offset}` : '-');
export const span = (position) => (position ? `${point(position.start)}..${point(position.end)}` : 'no position');
export const q = (s) => JSON.stringify(s);
