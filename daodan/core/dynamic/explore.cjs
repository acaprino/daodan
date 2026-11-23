'use strict';
// Explores the running app (plan task 11.3; spec of the project's interfaces, 7.4). Runs INSIDE the container, no
// network: `node explore.cjs <out dir> <name> <cwd> <port|-> <limit seconds> <command> [seeds json]` starts the app
// (`app.cjs`), opens headless Chromium on it, and for each page reads the controls from Playwright's own accessibility
// tree (`page.ariaSnapshotJSON({mode: 'ai'})`: role, name, ref), presses each once (`page.getByRef`) and records which
// functions of the project ran between the two takes of V8's precise coverage (the counters reset on each take),
// less what a still page runs by itself. The handler of a click is the first function of the project the event
// reaches: Chrome's own breakpoint on the `click` and `submit` events (`DOMDebugger.setEventListenerBreakpoint`), with the
// dependencies and the dev server's scripts blackboxed (`Debugger.setBlackboxPatterns`: the debugger leaves a
// blackboxed script by stepping in, so the pause lands in the project's own function), and the pause's top frame.
// Writes <out dir>/explore-<name>.json.
// Each press starts from a first visit: a browser context of its own, with no storage or cookie of the others (an
// onboarding or a cookie notice that an app remembers would change what the next control meets).
const fs = require('node:fs');
const { SourceMap } = require('node:module');
const { chromium, request: apiRequest } = require(process.env.DAODAN_PLAYWRIGHT || 'playwright-core');
const app = require('./app.cjs');

const LIMITS = { pages: 25, presses: 300, seconds: 900, settle: 400, click: 3000, render: 3000, depth: 3, workers: 4, revealed: 30, revealedPresses: 100 };
const PRESS = new Set(['button', 'link', 'tab', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'switch', 'checkbox', 'radio']);
const VALUE = new Set(['textbox', 'combobox', 'searchbox', 'spinbutton', 'slider']); // they ask for a value: not pressed
const LIBRARY = /\/node_modules\/|\/@vite\/|\/@react-refresh|\/@id\//; // a dependency's or the dev server's own script
const DECLARED = ['a control a press reveals is read after the press and pressed after the presses that show it, up to `depth` deep',
  'pages behind a login are not reached without a test credential',
  'a field is filled only to submit the form of a button, with a value of its HTML type (a proposal, not a decision); a field alone is not',
  'the presses of a page run in tabs at once: the answer is the same for an app with no state on a server, and may not be for one that has it',
  'each control is pressed once, from a freshly loaded page',
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

// The controls once the app has drawn them: an app answers its auth state or its data a while after the load, so the tree
// is read again until `done(found)`, up to `render` ms, and what is there then is what is pressed.
// `done(found, before, calm)`: `before` the count of the read before, `calm` how many reads in a row left it as it was.
async function controlsAfter(page, done) {
  const until = Date.now() + LIMITS.render;
  let found = [], calm = 0;
  for (;;) {
    const before = found.length;
    found = controlsOf(await page.ariaSnapshotJSON({ mode: 'ai' }));
    calm = found.length === before ? calm + 1 : 0;
    if (done(found, before, calm) || Date.now() > until) return found;
    await sleep(250);
  }
}
// Still for a second (4 reads in a row): what a page draws in steps is drawn. The reading a press is compared with must be this one, or the
// controls drawn after it would look like the press revealed them.
const still = (found, before, calm) => found.length > 0 && calm >= 3;

// The function a pause is in, as `{name, url, source, line, start}`: the place it paused at (the handler's first statement) and
// `start`, where the function begins (`callFrame.functionLocation`), both through the script's source map where it has one.
async function handlerOf(read, frame, url) {
  const { map } = await read(url);
  const place = location => {
    const entry = map ? map.findEntry(location.lineNumber, location.columnNumber) : null;
    return entry && entry.originalLine !== undefined
      ? { source: new URL(entry.originalSource, url).pathname, line: entry.originalLine + 1, column: entry.originalColumn }
      : { source: null, line: location.lineNumber + 1, column: location.columnNumber };
  };
  const here = place(frame.location), start = frame.functionLocation ? place(frame.functionLocation) : null;
  return { name: frame.functionName || '(anonymous)', url: new URL(url).pathname, source: here.source, line: here.line,
    ...(start && start.source === here.source ? { start: { line: start.line, column: start.column } } : {}) };
}

// The positions `[i, j]` of a longest common subsequence of two lists, in order.
function align(a, b) {
  const table = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      table[i][j] = a[i] === b[j] ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }
  const pairs = [];
  for (let i = 0, j = 0; i < a.length && j < b.length;) {
    if (a[i] === b[j]) { pairs.push([i, j]); i++; j++; }
    else if (table[i + 1][j] >= table[i][j + 1]) i++;
    else j++;
  }
  return pairs;
}

// The value a field takes so that its form can be submitted: one per HTML input type, none invented. A field the browser still
// refuses (`checkValidity()`: a `pattern`, a `max`) is said in `invalid`, and the form is not forced.
// shortcut: a table by the type the HTML standard names, not a value derived from `pattern` or `step`; when a form is refused for a
// constraint of its own, the entry says which and the form stays unsubmitted. Credentials are not guessed: the value is the same for
// every field of a type, and a login answers with its own refusal.
const VALUES = { email: 'test@example.com', password: 'Test-password-1', url: 'https://example.com/', tel: '0123456789', search: 'test',
  date: '2000-01-01', time: '12:00', 'datetime-local': '2000-01-01T12:00', month: '2000-01', week: '2000-W01' };

async function fillForm(page, locator) {
  const fields = await locator.evaluate(button => {
    if (!button.form) return [];
    const skipped = ['hidden', 'submit', 'button', 'reset', 'image', 'file', 'color'];
    return [...button.form.elements].filter(f => ['INPUT', 'TEXTAREA', 'SELECT'].includes(f.tagName) && !f.disabled && f !== button && !skipped.includes(f.type))
      .map((f, i) => { f.setAttribute('data-daodan-field', String(i));
        const label = f.getAttribute('aria-label') || (f.labels && f.labels[0] && f.labels[0].textContent.trim()) || f.name || f.id || '';
        return { i, type: f.type, name: label, min: f.min, options: f.tagName === 'SELECT' ? [...f.options].map(o => o.value) : [] }; });
  });
  const filled = [];
  for (const field of fields) {
    const target = page.locator(`[data-daodan-field="${field.i}"]`);
    try {
      if (field.type === 'checkbox' || field.type === 'radio') await target.check({ timeout: LIMITS.click });
      else if (field.type.startsWith('select')) await target.selectOption(field.options.find(value => value) || { index: 0 }, { timeout: LIMITS.click });
      else await target.fill(field.type === 'number' || field.type === 'range' ? (field.min || '1') : (VALUES[field.type] || 'test'), { timeout: LIMITS.click });
      filled.push({ type: field.type, name: field.name });
    } catch (error) { filled.push({ type: field.type, name: field.name, error: String(error.message).split('\n')[0].slice(0, 160) }); }
  }
  const invalid = await locator.evaluate(button => button.form ? [...button.form.elements].filter(f => f.willValidate && !f.checkValidity())
    .map(f => ({ name: f.getAttribute('aria-label') || (f.labels && f.labels[0] && f.labels[0].textContent.trim()) || f.name || f.id || '', message: f.validationMessage })) : []);
  return { filled, invalid };
}

const offsetToLine = (text, offset) => { // V8 gives an offset into the script; the source map wants line and column
  const before = text.slice(0, offset), line = before.split('\n').length - 1;
  return [line, offset - (before.lastIndexOf('\n') + 1)];
};

// The scripts' texts and their source maps, once per script (an inline map, or the file the comment names).
function scriptReader(api) {
  const cache = new Map();
  return async url => {
    if (!cache.has(url)) {
      let text = '', map = null;
      try {
        text = await (await api.get(url)).text();
        const comment = /\/\/# sourceMappingURL=(\S+)\s*$/m.exec(text);
        if (comment) {
          const inline = /^data:application\/json[^,]*;base64,(.+)$/.exec(comment[1]);
          const payload = inline ? Buffer.from(inline[1], 'base64').toString('utf8')
            : await (await api.get(new URL(comment[1], url).href)).text();
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
  const started = Date.now(), origin = new URL(ready.address).origin, hit = new Set(), cut = [];
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const api = await apiRequest.newContext(); // the scripts and their maps are fetched apart from any page's state
  const read = scriptReader(api), unmapped = new Set();
  // A tab is one browser context of its own with its CDP session and what the page did: a press runs in one, from a first visit. The
  // presses of a page are independent, so `LIMITS.workers` tabs take them from the worklist at once.
  const makeTab = () => {
    const tab = { state: { requests: [], dialogs: [], popups: [], errors: [], frame: null }, context: null, page: null, cdp: null };
    const { state } = tab;
    tab.open = async () => { // a clean context: what a first visit meets
      if (tab.context) await tab.context.close().catch(() => {});
      const context = tab.context = await browser.newContext();
      const page = tab.page = await context.newPage();
      const cdp = tab.cdp = await context.newCDPSession(page);
      await cdp.send('Profiler.enable');
      await cdp.send('Debugger.enable');
      await cdp.send('Debugger.setBlackboxPatterns', { patterns: [LIBRARY.source] });
      const scripts = new Map(); // a call frame's `url` is empty in recent Chromium: its script's url comes from `scriptParsed`
      cdp.on('Debugger.scriptParsed', event => scripts.set(event.scriptId, event.url));
      cdp.on('Debugger.paused', event => { // the first pause of a press names the handler; every pause resumes at once
        const top = event.callFrames[0], url = top && scripts.get(top.location.scriptId);
        if (!state.frame && url && url.startsWith(origin)) state.frame = { frame: top, url };
        cdp.send('Debugger.resume').catch(() => {});
      });
      page.on('request', request => { if (['fetch', 'xhr'].includes(request.resourceType())) state.requests.push({ method: request.method(), url: request.url() }); });
      page.on('dialog', dialog => { state.dialogs.push(dialog.type()); dialog.dismiss().catch(() => {}); });
      page.on('pageerror', error => state.errors.push(String(error.message).slice(0, 200)));
      context.on('page', popup => { if (popup !== page) { state.popups.push(popup.url()); popup.close().catch(() => {}); } });
    };
    tab.load = async url => {
      await tab.open();
      await tab.page.goto(url, { waitUntil: 'load', timeout: 15000 });
      await tab.page.waitForLoadState('networkidle', { timeout: 3000 }).catch(() => {});
      await tab.cdp.send('Profiler.startPreciseCoverage', { callCount: true, detailed: true });
    };
    tab.close = async () => { if (tab.context) await tab.context.close().catch(() => {}); };
    return tab;
  };
  const queue = [where('/', origin), ...seeds.map(seed => where(seed, origin))].filter(Boolean);
  const visited = new Set(), pages = [], gaps = [];
  let presses = 0, revealedUsed = 0;
  while (queue.length) {
    const url = queue.shift();
    if (visited.has(url)) continue;
    if (visited.size >= LIMITS.pages) { hit.add('pages'); break; }
    if ((Date.now() - started) / 1000 > LIMITS.seconds) { hit.add('seconds'); break; }
    visited.add(url);
    const record = { url, controls: [], errors: [] };
    pages.push(record);
    try {
      const main = makeTab();
      await main.load(url);
      await main.cdp.send('Profiler.takePreciseCoverage'); await sleep(LIMITS.settle); // a still page's own runs
      const idle = await ran(main.cdp, read, origin, unmapped);
      const controls = await controlsAfter(main.page, still);
      record.errors = main.state.errors.slice(0, 5);
      if (!controls.length) { // nothing to press: say why (its error, what it shows), not a silence
        const shown = (await main.page.ariaSnapshot().catch(() => '')).replace(/\s+/g, ' ').trim().slice(0, 300);
        gaps.push({ kind: 'page_without_controls', path: url, errors: record.errors, detail: `${url} shows no control to press ` +
          `(title "${await main.page.title().catch(() => '')}"): ${record.errors.length ? `its first error: ${record.errors[0]}` : 'no page error'}; ` +
          `it shows: ${shown || 'nothing'}` });
      }
      await main.close();
      // A worklist: the page's own controls, then the ones a press reveals (a menu, a dialog), each pressed after the
      // presses that show it, from a page loaded again.
      const sameAs = wanted => c => c.role === wanted.role && c.name === wanted.name && c.occurrence === wanted.occurrence;
      const keyOf = c => `${c.role}\0${c.name}\0${c.occurrence}`;
      const work = controls.map(control => ({ control, path: [], owner: record.controls }));
      const press = async (tab, { control, path, owner }) => {
        const entry = { role: control.role, name: control.name, url: control.url, occurrence: control.occurrence,
          ...(path.length ? { opened_by: path.map(step => step.name) } : {}) };
        owner.push(entry);
        if (VALUE.has(control.role)) { Object.assign(entry, { state: 'skipped', reason: 'needs_value' }); return; }
        const target = control.url && where(control.url, origin);
        if (control.url && !target && !control.url.startsWith('#') && !control.url.startsWith('javascript:')) {
          Object.assign(entry, { state: 'skipped', reason: 'leaves_the_app' }); return;
        }
        const spent = path.length ? revealedUsed >= LIMITS.revealedPresses : presses >= LIMITS.presses; // a budget of its own for the revealed
        if (spent || (Date.now() - started) / 1000 > LIMITS.seconds) {
          hit.add(spent ? (path.length ? 'revealed' : 'presses') : 'seconds'); Object.assign(entry, { state: 'skipped', reason: 'cap' }); return;
        }
        if (path.length) revealedUsed += 1; else presses += 1;
        try {
          await tab.load(url);
          const { page, cdp, state } = tab;
          for (const step of path) { // the presses that show this control
            const shown = (await controlsAfter(page, found => found.some(sameAs(step)))).find(sameAs(step));
            if (!shown) throw new Error('not_found_again');
            await fillForm(page, page.getByRef(shown.ref)); // the press that showed it was of a filled form
            await page.getByRef(shown.ref).click({ timeout: LIMITS.click });
            await page.waitForLoadState('networkidle', { timeout: 1500 }).catch(() => {});
            await sleep(LIMITS.settle);
          }
          const before = await controlsAfter(page, (found, prev, calm) => found.some(sameAs(control)) && still(found, prev, calm));
          const now = before.find(sameAs(control));
          if (!now) { Object.assign(entry, { state: 'failed', reason: 'not_found_again' }); return; }
          const locator = page.getByRef(now.ref);
          if (!await locator.isVisible() || !await locator.isEnabled()) { Object.assign(entry, { state: 'skipped', reason: 'not_operable' }); return; }
          const form = await fillForm(page, locator); // before the state is reset: what filling runs is not the press's
          if (form.filled.length) Object.assign(entry, { filled: form.filled, invalid: form.invalid });
          Object.assign(state, { requests: [], dialogs: [], popups: [], frame: null });
          for (const eventName of ['click', 'submit']) await cdp.send('DOMDebugger.setEventListenerBreakpoint', { eventName });
          await cdp.send('Profiler.takePreciseCoverage');
          await locator.click({ timeout: LIMITS.click });
          for (const eventName of ['click', 'submit']) await cdp.send('DOMDebugger.removeEventListenerBreakpoint', { eventName }).catch(() => {});
          await page.waitForLoadState('networkidle', { timeout: 1500 }).catch(() => {});
          await sleep(LIMITS.settle);
          const after = await ran(cdp, read, origin, unmapped);
          const calls = [...after].filter(([key]) => !idle.has(key)).map(([, fn]) => fn);
          const landed = where(page.url(), origin);
          Object.assign(entry, { state: 'pressed', ...(state.frame ? { handler: await handlerOf(read, state.frame.frame, state.frame.url) } : {}), calls, requests: state.requests.slice(0, 10),
            ...(landed && landed !== url ? { navigated: landed } : {}),
            ...(!landed ? { left_the_app: page.url() } : {}),
            ...(state.dialogs.length ? { dialogs: state.dialogs } : {}), ...(state.popups.length ? { popups: state.popups } : {}) });
          if (landed && landed !== url) queue.push(landed);
          if (target && target !== url) queue.push(target);
          // what the press drew that the page did not show before; a link navigates or scrolls, it opens nothing
          if (landed === url && control.role !== 'link' && path.length + 1 < LIMITS.depth) {
            const known = new Set(before.map(keyOf));
            const now = await controlsAfter(page, still);
            // A press that leaves the page's structure as it was has drawn it again: a language or theme toggle renames the
            // controls, and may add one (a skip link), and reveals none. A menu keeps the names the page had; a dialog changes the
            // structure, even a modal one that takes the page's controls out of the accessibility tree.
            // shortcut: structure is the role sequence; "as it was" is 90 % of it in common with a quarter of the common controls
            // renamed. A page redrawn into another structure, or with fewer names changed, reads as controls revealed; so does one
            // that is renamed and also shows new controls (a language toggle that draws a section): its renamed controls read as
            // new too, are pressed twice and take places of the per-press cap, which `explore_cap` says when it cuts.
            const roles = list => list.map(c => c.role);
            const pairs = align(roles(before), roles(now));
            const renamed = pairs.filter(([i, j]) => before[i].name !== now[j].name).length;
            const redrawn = roles(before).join() === roles(now).join() ||
              (pairs.length >= 0.9 * Math.max(before.length, now.length) && renamed >= pairs.length / 4);
            entry.structure = { before: before.length, after: now.length, common: pairs.length, renamed, redrawn }; // the numbers of the rule
            const shown = redrawn ? [] : now.filter(c => !known.has(keyOf(c))), fresh = shown.slice(0, LIMITS.revealed);
            if (shown.length > fresh.length) { hit.add('revealed_per_press'); cut.push(`${shown.length - fresh.length} more after "${control.name}"`); }
            if (fresh.length) {
              entry.revealed = [];
              for (const c of fresh) work.push({ control: c, path: [...path, control], owner: entry.revealed });
            }
          }
        } catch (error) {
          // Playwright's call log says why a click waited (`<div id=banner> intercepts pointer events`): keep that line too
          const lines = String(error.message).split('\n').map(line => line.trim()).filter(Boolean);
          const why = lines.find(line => /intercepts pointer events|is not visible|outside of the viewport|is not stable|not enabled/.test(line));
          Object.assign(entry, { state: 'failed', reason: (lines[0] + (why ? ` — ${why}` : '')).slice(0, 320) });
        }
      };
      let active = 0;
      const worker = async () => {
        const tab = makeTab();
        try {
          for (;;) {
            const item = work.shift(); // the entry is made at once, before the press's first wait: the order is the worklist's
            if (item) { active += 1; try { await press(tab, item); } finally { active -= 1; } }
            else if (active === 0) return; // nothing left, and nobody who could add what a press reveals
            else await sleep(50);
          }
        } finally { await tab.close(); }
      };
      await Promise.all(Array.from({ length: LIMITS.workers }, worker));
    } catch (error) {
      gaps.push({ kind: 'explore_page_failed', path: url, detail: `${url} did not load: ${String(error.message).split('\n')[0].slice(0, 200)}` });
    }
  }
  if (queue.some(item => !visited.has(item))) hit.add('pages');
  if (unmapped.size) gaps.push({ kind: 'calls_unmapped', files: unmapped.size, examples: [...unmapped].slice(0, 5),
    detail: `${unmapped.size} scripts of the app ran with no source map: their functions are named by script, not by file` });
  if (hit.size) gaps.push({ kind: 'explore_cap', caps: [...hit], detail: `the exploration stopped at its cap (${[...hit].join(', ')}): ` +
    `${LIMITS.pages} pages, ${LIMITS.presses} presses, ${LIMITS.seconds} s, ${LIMITS.revealed} controls revealed by one press` +
    (cut.length ? `; not looked at: ${cut.slice(0, 5).join(', ')}` : '') });
  const flat = list => list.flatMap(c => [c, ...flat(c.revealed || [])]);
  const all = flat(pages.flatMap(item => item.controls));
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
