'use strict';
// Explores the running app (plan task 11.3; spec of the project's interfaces, 7.4). Runs INSIDE the container, no
// network: `node explore.cjs <out dir> <name> <cwd> <port|-> <limit seconds> <command> [seeds json]` starts the app
// (`app.cjs`), opens headless Chromium on it, and for each page reads the controls from Playwright's own accessibility
// tree (`page.ariaSnapshotJSON({mode: 'ai'})`: role, name, ref), presses each once (`page.getByRef`) and records which
// functions of the project ran between the two takes of V8's precise coverage (the counters reset on each take),
// less what a still page runs by itself. Writes <out dir>/explore-<name>.json.
// The page is loaded again before each press, so one press does not change what the next one meets.
const fs = require('node:fs');
const { SourceMap } = require('node:module');
const { chromium } = require(process.env.DAODAN_PLAYWRIGHT || 'playwright-core');
const app = require('./app.cjs');

const LIMITS = { pages: 25, presses: 300, seconds: 600, settle: 400, click: 3000 };
const PRESS = new Set(['button', 'link', 'tab', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'switch', 'checkbox', 'radio']);
const VALUE = new Set(['textbox', 'combobox', 'searchbox', 'spinbutton', 'slider']); // they ask for a value: not pressed
const LIBRARY = /\/node_modules\/|\/@vite\/|\/@react-refresh|\/@id\//; // a dependency's or the dev server's own script
const DECLARED = ['pages behind a login are not reached without a test credential',
  'controls that ask for a value are not filled', 'each control is pressed once, from a freshly loaded page',
  'a function that also runs by itself while the page is still is not attributed to a press'];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

const where = (url, origin) => { // an app page's identity: origin, path and query, no hash
  try { const found = new URL(url, origin); return found.origin === origin ? found.origin + found.pathname + found.search : null; }
  catch (error) { return null; }
};

function controlsOf(tree) {
  const found = [], seen = new Map();
  (function walk(nodes) {
    for (const node of Array.isArray(nodes) ? nodes : []) {
      if (!node || typeof node !== 'object') continue;
      if (PRESS.has(node.role) || VALUE.has(node.role)) {
        const key = `${node.role}\0${node.name || ''}`, occurrence = seen.get(key) || 0;
        seen.set(key, occurrence + 1);
        found.push({ role: node.role, name: node.name || '', url: node.url || null, ref: node.ref, occurrence });
      }
      walk(node.children);
    }
  })(tree);
  return found;
}

const offsetToLine = (text, offset) => { // V8 gives an offset into the script; the source map wants line and column
  const before = text.slice(0, offset), line = before.split('\n').length - 1;
  return [line, offset - (before.lastIndexOf('\n') + 1)];
};

// The scripts' texts and their source maps, once per script (an inline map, or the file the comment names).
function scriptReader(context, origin) {
  const cache = new Map();
  return async url => {
    if (!cache.has(url)) {
      let text = '', map = null;
      try {
        text = await (await context.request.get(url)).text();
        const comment = /\/\/# sourceMappingURL=(\S+)\s*$/m.exec(text);
        if (comment) {
          const inline = /^data:application\/json[^,]*;base64,(.+)$/.exec(comment[1]);
          const payload = inline ? Buffer.from(inline[1], 'base64').toString('utf8')
            : await (await context.request.get(new URL(comment[1], url).href)).text();
          map = new SourceMap(JSON.parse(payload));
        }
      } catch (error) { /* a script without its text or map is unmapped */ }
      cache.set(url, { text, map });
    }
    return cache.get(url);
  };
}

// The functions with a count in one take of precise coverage, as `{url, source, line, name, count}`; `source` null
// where no map says the file.
async function ran(cdp, read, origin, unmapped) {
  const { result } = await cdp.send('Profiler.takePreciseCoverage');
  const found = new Map();
  for (const script of result) {
    if (!script.url || !script.url.startsWith(origin) || LIBRARY.test(script.url)) continue;
    const { text, map } = await read(script.url);
    for (const fn of script.functions) {
      const range = fn.ranges[0];
      if (!range || range.count === 0) continue;
      let source = null, line = null;
      if (map) {
        const [row, column] = offsetToLine(text, range.startOffset);
        let entry = {};
        for (let c = column; c < column + 60 && entry.originalLine === undefined; c++) entry = map.findEntry(row, c) || {};
        // a map names its sources relative to the script (`useTheme.ts`, `/work/app/src/a.ts`): the path the page served
        if (entry.originalLine !== undefined) { source = new URL(entry.originalSource, script.url).pathname; line = entry.originalLine + 1; }
      }
      if (source && LIBRARY.test(`/${source}`)) continue;
      if (!source) unmapped.add(script.url);
      found.set(`${script.url}@${range.startOffset}`, { url: new URL(script.url).pathname, source, line,
        name: fn.functionName || '(anonymous)', count: range.count });
    }
  }
  return found;
}

async function explore(ready, out, name, seeds) {
  const started = Date.now(), origin = new URL(ready.address).origin, hit = new Set();
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const context = await browser.newContext();
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Profiler.enable');
  const read = scriptReader(context, origin), unmapped = new Set();
  const state = { requests: [], dialogs: [], popups: [], errors: [] };
  page.on('request', request => { if (['fetch', 'xhr'].includes(request.resourceType())) state.requests.push({ method: request.method(), url: request.url() }); });
  page.on('dialog', dialog => { state.dialogs.push(dialog.type()); dialog.dismiss().catch(() => {}); });
  page.on('pageerror', error => state.errors.push(String(error.message).slice(0, 200)));
  context.on('page', popup => { if (popup !== page) { state.popups.push(popup.url()); popup.close().catch(() => {}); } });

  const load = async url => {
    await page.goto(url, { waitUntil: 'load', timeout: 15000 });
    await page.waitForLoadState('networkidle', { timeout: 3000 }).catch(() => {});
    await cdp.send('Profiler.startPreciseCoverage', { callCount: true, detailed: true });
  };
  const queue = [where('/', origin), ...seeds.map(seed => where(seed, origin))].filter(Boolean);
  const visited = new Set(), pages = [], gaps = [];
  let presses = 0;
  while (queue.length) {
    const url = queue.shift();
    if (visited.has(url)) continue;
    if (visited.size >= LIMITS.pages) { hit.add('pages'); break; }
    if ((Date.now() - started) / 1000 > LIMITS.seconds) { hit.add('seconds'); break; }
    visited.add(url);
    const record = { url, controls: [], errors: [] };
    pages.push(record);
    try {
      state.errors = []; await load(url);
      await cdp.send('Profiler.takePreciseCoverage'); await sleep(LIMITS.settle); // a still page's own runs
      const idle = await ran(cdp, read, origin, unmapped);
      const controls = controlsOf(await page.ariaSnapshotJSON({ mode: 'ai' }));
      record.errors = state.errors.slice(0, 5);
      if (!controls.length) { // nothing to press: say why (its error, what it shows), not a silence
        const shown = (await page.ariaSnapshot().catch(() => '')).replace(/\s+/g, ' ').trim().slice(0, 300);
        gaps.push({ kind: 'page_without_controls', path: url, errors: record.errors, detail: `${url} shows no control to press ` +
          `(title "${await page.title().catch(() => '')}"): ${record.errors.length ? `its first error: ${record.errors[0]}` : 'no page error'}; ` +
          `it shows: ${shown || 'nothing'}` });
      }
      for (const control of controls) {
        const entry = { role: control.role, name: control.name, url: control.url, occurrence: control.occurrence };
        record.controls.push(entry);
        if (VALUE.has(control.role)) { Object.assign(entry, { state: 'skipped', reason: 'needs_value' }); continue; }
        const target = control.url && where(control.url, origin);
        if (control.url && !target && !control.url.startsWith('#') && !control.url.startsWith('javascript:')) {
          Object.assign(entry, { state: 'skipped', reason: 'leaves_the_app' }); continue;
        }
        if (presses >= LIMITS.presses || (Date.now() - started) / 1000 > LIMITS.seconds) {
          hit.add(presses >= LIMITS.presses ? 'presses' : 'seconds'); Object.assign(entry, { state: 'skipped', reason: 'cap' }); continue;
        }
        presses += 1;
        try {
          await load(url);
          const now = controlsOf(await page.ariaSnapshotJSON({ mode: 'ai' }))
            .find(c => c.role === control.role && c.name === control.name && c.occurrence === control.occurrence);
          if (!now) { Object.assign(entry, { state: 'failed', reason: 'not_found_again' }); continue; }
          const locator = page.getByRef(now.ref);
          if (!await locator.isVisible() || !await locator.isEnabled()) { Object.assign(entry, { state: 'skipped', reason: 'not_operable' }); continue; }
          Object.assign(state, { requests: [], dialogs: [], popups: [] });
          await cdp.send('Profiler.takePreciseCoverage');
          await locator.click({ timeout: LIMITS.click });
          await page.waitForLoadState('networkidle', { timeout: 1500 }).catch(() => {});
          await sleep(LIMITS.settle);
          const after = await ran(cdp, read, origin, unmapped);
          const calls = [...after].filter(([key]) => !idle.has(key)).map(([, fn]) => fn);
          const landed = where(page.url(), origin);
          Object.assign(entry, { state: 'pressed', calls, requests: state.requests.slice(0, 10),
            ...(landed && landed !== url ? { navigated: landed } : {}),
            ...(!landed ? { left_the_app: page.url() } : {}),
            ...(state.dialogs.length ? { dialogs: state.dialogs } : {}), ...(state.popups.length ? { popups: state.popups } : {}) });
          if (landed && landed !== url) queue.push(landed);
          if (target && target !== url) queue.push(target);
        } catch (error) {
          Object.assign(entry, { state: 'failed', reason: String(error.message).split('\n')[0].slice(0, 200) });
        }
      }
    } catch (error) {
      gaps.push({ kind: 'explore_page_failed', path: url, detail: `${url} did not load: ${String(error.message).split('\n')[0].slice(0, 200)}` });
    }
  }
  if (queue.some(item => !visited.has(item))) hit.add('pages');
  if (unmapped.size) gaps.push({ kind: 'calls_unmapped', files: unmapped.size, examples: [...unmapped].slice(0, 5),
    detail: `${unmapped.size} scripts of the app ran with no source map: their functions are named by script, not by file` });
  if (hit.size) gaps.push({ kind: 'explore_cap', caps: [...hit], detail: `the exploration stopped at its cap (${[...hit].join(', ')}): ` +
    `${LIMITS.pages} pages, ${LIMITS.presses} presses, ${LIMITS.seconds} s` });
  const all = pages.flatMap(item => item.controls);
  const totals = { pages: pages.length, controls: all.length, pressed: all.filter(c => c.state === 'pressed').length,
    skipped: all.filter(c => c.state === 'skipped').length, failed: all.filter(c => c.state === 'failed').length };
  fs.writeFileSync(`${out}/explore-${name}.json`, JSON.stringify({ origin, pages, totals, limits: { ...LIMITS, declared: DECLARED }, gaps }));
  await browser.close();
}

if (require.main === module) {
  const argv = process.argv.slice(2), seeds = JSON.parse(argv[6] || '[]');
  app.run(argv.slice(0, 6), (ready, out, name) => explore(ready, out, name, seeds))
    .then(() => process.exit(0), error => { console.error('DRIVER FAILED', error); process.exit(1); });
}
module.exports = { explore, controlsOf, where };
