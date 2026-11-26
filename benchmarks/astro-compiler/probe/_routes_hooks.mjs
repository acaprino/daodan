// Run by `04_routes.mjs` in a copy of the project: `node _routes_hooks.mjs <root> sync|build`. The integration given inline records each hook.
const root = process.argv[2];
const mode = process.argv[3];
const { sync, build } = await import('astro');
const seen = [];
const brief = (routes) => (routes ?? []).map((r) => ({
  route: r.route ?? r.pattern, pattern: r.pattern, entrypoint: String(r.entrypoint ?? r.component ?? ''), type: r.type, prerender: r.isPrerendered ?? r.prerender,
  origin: r.origin, params: r.params, keys: Object.keys(r).join(','),
}));
const integration = { name: 'daodan-probe', hooks: {
  'astro:config:done': () => { seen.push({ hook: 'astro:config:done' }); },
  'astro:routes:resolved': ({ routes }) => { seen.push({ hook: 'astro:routes:resolved', routes: brief(routes) }); },
  'astro:build:done': ({ routes, pages }) => { seen.push({ hook: 'astro:build:done', routes: brief(routes), pages: (pages ?? []).map((p) => p.pathname) }); },
} };
const started = Date.now();
const lines = [];
try {
  const options = { root, integrations: [integration], logLevel: 'error' };
  if (mode === 'sync') await sync(options); else await build(options);
  lines.push(`${mode}: ok in ${(Date.now() - started) / 1000} s through the API; hooks that fired: ${seen.map((s) => s.hook).join(', ')}`);
} catch (error) {
  lines.push(`${mode}: FAILED in ${(Date.now() - started) / 1000} s: ${String(error?.message ?? error).split('\n').slice(0, 3).join(' | ').slice(0, 400)}; hooks that fired: ${seen.map((s) => s.hook).join(', ')}`);
}
for (const s of seen) {
  if (!s.routes) continue;
  lines.push(`${s.hook}: ${s.routes.length} routes`);
  for (const r of s.routes) lines.push(`  ${r.route} | ${r.entrypoint.replace(root, '<root>')} | ${r.type} | prerender ${r.prerender} | ${r.origin} | params ${JSON.stringify(r.params)}`);
  if (s.routes[0]) lines.push(`  fields of a route: ${s.routes[0].keys}`);
  if (s.pages) lines.push(`  pages: ${s.pages.join(', ')}`);
}
console.log(lines.join('\n'));
