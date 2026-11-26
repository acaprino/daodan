// Does an official Astro tool list the routes of a project without starting the app? The routes are the files of `src/pages`; what is
// measured: the CLI's commands, what `astro sync` writes, and whether the integration hook `astro:routes:resolved` (and, at the end of a
// build, `astro:build:done`) fires and gives each route with its entry file, under `sync` and under `build`, through the programmatic API
// (`import { sync, build } from 'astro'`) with an integration given inline. Each run is in a copy of the project (the packages linked).
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const ENV = { ...process.env, npm_config_offline: 'true', ASTRO_TELEMETRY_DISABLED: '1', CI: '1', NO_COLOR: '1' };

function copy(name, edit) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `astro-${name}-`));
  fs.cpSync(root, dir, { recursive: true, filter: (src) => !/node_modules|[\\/]probe([\\/]|$)/.test(src) });
  fs.symlinkSync(path.join(root, 'node_modules'), path.join(dir, 'node_modules'));
  if (edit) edit(dir);
  return dir;
}
function listing(dir) {
  const out = [];
  const visit = (d) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.name === 'node_modules') continue; const f = path.join(d, e.name); if (e.isDirectory()) visit(f); else out.push(path.relative(dir, f).split(path.sep).join('/')); } };
  visit(dir);
  return out.sort();
}
function run(argv, cwd, seconds = 300) {
  const started = Date.now();
  const r = spawnSync(argv[0], argv.slice(1), { cwd, env: ENV, encoding: 'utf8', timeout: seconds * 1000 });
  return { ...r, seconds: (Date.now() - started) / 1000 };
}
const show = (r) => `exit ${r.status}${r.signal ? ' signal ' + r.signal : ''} in ${r.seconds}s\n--- stdout\n${(r.stdout ?? '').slice(0, 12000)}\n--- stderr\n${(r.stderr ?? '').slice(0, 1200)}`;

console.log('node', process.version);
console.log('\n##### astro --help');
console.log(show(run(['npx', '--no-install', 'astro', '--help'], root, 120)));

console.log('\n##### astro sync (CLI), in a copy: the files it writes, and whether any names a route');
{
  const dir = copy('sync');
  const before = new Set(listing(dir));
  const r = run(['npx', '--no-install', 'astro', 'sync'], dir);
  console.log(show(r));
  const added = listing(dir).filter((f) => !before.has(f));
  console.log('files added by sync:', JSON.stringify(added));
  for (const f of added) {
    const text = fs.readFileSync(path.join(dir, f), 'utf8');
    const hits = ['/about', '[slug]', 'api/items', 'pages/'].filter((needle) => text.includes(needle));
    console.log(`  ${f} (${text.length} chars) names: ${hits.join(', ') || 'no page, no route'}`);
  }
}

// the integration given inline (`_routes_hooks.mjs`): every hook the question needs, each records what it was given
const HOOKS = fs.readFileSync(new URL('./_routes_hooks.mjs', import.meta.url), 'utf8');
for (const mode of ['sync', 'build']) {
  console.log(`\n##### programmatic ${mode}() with an integration given inline, in a copy`);
  const dir = copy(mode, (d) => { if (mode === 'build') fs.writeFileSync(path.join(d, 'src/pages/api/items.ts'), fs.readFileSync(path.join(d, 'src/pages/api/items.ts'), 'utf8').replace('export const prerender = false;\n', '')); });
  fs.writeFileSync(path.join(dir, 'probe-run.mjs'), HOOKS);
  const r = run(['node', 'probe-run.mjs', dir, mode], dir, 600);
  console.log(show(r));
  console.log('files added in the copy:', JSON.stringify(listing(dir).filter((f) => /^(dist|\.astro)\//.test(f)).slice(0, 25)));
}
