// Daodan's script for `nuxt.py`, run in Daodan's container, in the folder of a Nuxt project whose packages are restored, with no
// network and no argument. It calls the `loadNuxt` and `buildNuxt` of the `@nuxt/kit` the project installed (resolved from the
// working folder, not from this script's), the documented API of Nuxt's own tools, and listens to the hook `pages:resolved`:
// Nuxt calls it with the routes it has made of the pages, after the project's `pages:extend` hooks, its modules and its layers
// have had their say, and each route has its `name`, its `path` (relative to its parent for a child) and its `file` (absolute).
// `_prepare` makes `buildNuxt` generate the app and stop before it bundles it, as `nuxt prepare` does. The script prints, as the
// last line of its standard output (a module may print before it), `{"called": bool, "pages": [{name, path, file, children}]}`:
// the same tree, each `file` relative to the working folder (null for a route with no file: a redirect, a route a module adds in
// code), `called` false when Nuxt did not call the hook (the app has no pages folder, or this Nuxt does not know the hook).
// Exit 3: the project has no `@nuxt/kit`. Exit 4: the one it has lacks `loadNuxt` or `buildNuxt`. Exit 5: `loadNuxt` failed (the
// config throws, a module is missing): the cause, its first line, is the standard error. Exit 6: `buildNuxt` failed.
// shortcut: `@nuxt/kit` is resolved from the project's folder, where npm puts it beside `nuxt` (measured: Nuxt 3.21.11 and 4.6.4);
// a manager that does not hoist it (pnpm's strict layout) gives exit 3 and a gap, when one is met resolve it from `nuxt`'s folder.
// shortcut: `loadNuxt` and `buildNuxt` write `.nuxt/` in the copy the container runs in, as `nuxt prepare` does before it.
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

function stop(message, code) {
  process.stderr.write(`daodan-nuxt: ${message}\n`);
  process.exit(code);
}
const first = (error) => String(error?.message ?? error).split('\n')[0].slice(0, 300);

const folder = process.cwd();
const require = createRequire(`${folder}/`);
let kit;
try {
  kit = await import(pathToFileURL(require.resolve('@nuxt/kit')).href);
} catch (error) {
  stop(`@nuxt/kit is not installed for ${folder}: ${first(error)}`, 3);
}
if (typeof kit.loadNuxt !== 'function' || typeof kit.buildNuxt !== 'function') stop('this @nuxt/kit exports no loadNuxt and buildNuxt', 4);

let nuxt;
try {
  nuxt = await kit.loadNuxt({ cwd: folder, overrides: { _prepare: true } });
} catch (error) {
  stop(`loadNuxt failed: ${first(error)}`, 5);
}
let resolved = null;
nuxt.hook('pages:resolved', (pages) => { resolved = pages; });
try {
  await kit.buildNuxt(nuxt);
  await nuxt.close();
} catch (error) {
  stop(`buildNuxt failed: ${first(error)}`, 6);
}
const tree = (pages) => pages.map((page) => ({
  name: page.name ?? null,
  path: page.path,
  file: page.file ? path.relative(folder, page.file) : null,
  children: tree(page.children ?? []),
}));
process.stdout.write(`${JSON.stringify({ called: resolved !== null, pages: tree(resolved ?? []) })}\n`, () => process.exit(0));
