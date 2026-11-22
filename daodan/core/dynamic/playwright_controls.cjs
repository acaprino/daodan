// Node preload for a project's declared Playwright tests. Playwright reporters see test steps, not the
// DOM state of the control actually used. Install the same DOM reader as the explorer on each context.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const {threadId} = require('node:worker_threads');

// Runs in the main frame. A new document gets a new namespace even when its URL stays the same.
function installPublisher() {
  if (globalThis.__daodanControlSnapshot) return;
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  const documentId = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  let sequence = 0;
  const snapshot = () => {
    const report = globalThis.__daodanControls.report();
    if (location.href === 'about:blank' && !report.observed.length && !report.pending.length) return null;
    return {document: documentId, sequence: ++sequence, ...report};
  };
  Object.defineProperty(globalThis, '__daodanControlSnapshot', {value: snapshot});
  let timer;
  const publish = (final = false) => {
    clearTimeout(timer);
    timer = undefined;
    try {
      const data = snapshot();
      if (data) globalThis.__daodanReportControls(data, final).catch(() => {});
    } catch { /* The missing final snapshot is a gap when the document closes. */ }
  };
  if (location.href !== 'about:blank') globalThis.__daodanReportControls({opened: documentId}).catch(() => {});
  const schedule = () => { if (timer === undefined) timer = setTimeout(publish, 100); };
  for (const event of ['click', 'change', 'DOMContentLoaded']) addEventListener(event, schedule, true);
  addEventListener('pagehide', () => publish(true), true);
  addEventListener('pageshow', schedule, true);
}

function observe(output) {
  const documents = new Map();
  const open = new Set();
  const sequence = new Map();
  const gaps = new Set();
  const browsers = new WeakSet();
  const contexts = new WeakMap();
  const pages = new WeakSet();
  const patched = new WeakSet();
  const limit = 256; // documents per test worker; a larger run reports its partial coverage
  const rowLimit = 32768;
  let retainedRows = 0;
  let dirty = false;
  let timer;
  let script;
  function save() {
    clearTimeout(timer);
    timer = undefined;
    if (!dirty) return;
    try {
      const report = {documents: [...documents.values()], gaps: [...gaps, ...(open.size ? ['unfinished_document'] : [])].sort()};
      fs.writeFileSync(output + '.tmp', JSON.stringify(report));
      fs.renameSync(output + '.tmp', output);
      dirty = false;
    } catch { /* The observer reports missing/unreadable outputs as a gap. */ }
  }
  function changed() {
    dirty = true;
    if (!timer) timer = setTimeout(save, 1000).unref();
  }
  function gap(code) {
    if (!gaps.has(code)) { gaps.add(code); changed(); }
  }
  function rows(items, room) {
    if (!Array.isArray(items)) { gap('invalid_report'); return []; }
    const valid = [];
    for (const row of items) {
      if (valid.length >= room) { gap('report_limit'); break; }
      if (row && Number.isSafeInteger(row.control) && row.control > 0 &&
          Number.isSafeInteger(row.state) && row.state > 0 && ['click', 'change'].includes(row.event))
        valid.push({control: row.control, event: row.event, state: row.state});
      else gap('invalid_report');
    }
    return valid;
  }
  function accept(data, final) {
    if (!data) return;
    if (typeof data.document !== 'string' || !/^[0-9a-f]{32}$/.test(data.document)) {
      gap('invalid_report');
      return;
    }
    if (!Number.isSafeInteger(data.sequence) || data.sequence <= 0) { gap('invalid_report'); return; }
    if (!sequence.has(data.document) && documents.size >= limit) { gap('report_limit'); return; }
    if (data.truncated) gap('report_limit');
    if ((sequence.get(data.document) || 0) >= data.sequence) return;
    sequence.set(data.document, data.sequence);
    if (final) open.delete(data.document);
    else open.add(data.document);
    const previous = documents.get(data.document);
    if (previous) retainedRows -= previous.observed.length + previous.pending.length;
    const observed = rows(data.observed, rowLimit - retainedRows);
    const pending = rows(data.pending, rowLimit - retainedRows - observed.length);
    const record = {document: data.document, observed, pending};
    retainedRows += observed.length + pending.length;
    documents.set(record.document, record);
    changed();
  }
  async function collect(page) {
    if (page.isClosed()) return;
    try {
      const report = await page.evaluate(() => globalThis.__daodanControlSnapshot
        ? globalThis.__daodanControlSnapshot() : location.href === 'about:blank' ? null : false);
      if (report === false) gap('reader_unavailable');
      else accept(report, true);
    }
    catch { gap('page_unreadable'); }
  }
  function beforeClose(owner, read) {
    const close = owner.close;
    owner.close = async function(...args) {
      let timeout;
      try {
        await Promise.race([read(), new Promise(resolve => {
          timeout = setTimeout(() => { gap('teardown_timeout'); resolve(); }, 1000);
        })]);
      } catch { gap('page_unreadable'); }
      finally { clearTimeout(timeout); }
      return close.apply(this, args);
    };
  }
  function attachPage(page) {
    if (pages.has(page)) return;
    pages.add(page);
    beforeClose(page, () => collect(page));
  }
  function attachContext(context) {
    if (contexts.has(context)) return contexts.get(context);
    const ready = (async () => {
      try {
        await context.exposeBinding('__daodanReportControls', ({page, frame}, data, final) => {
          if (frame !== page.mainFrame()) return;
          if (typeof data?.opened === 'string' && /^[0-9a-f]{32}$/.test(data.opened)) {
            if (!sequence.has(data.opened)) {
              if (open.size < limit) { open.add(data.opened); changed(); }
              else gap('report_limit');
            }
          } else accept(data, final === true);
        });
        await context.addInitScript({content: script});
        context.on('page', attachPage);
        beforeClose(context, () => Promise.all(context.pages().map(collect)));
        for (const page of context.pages()) {
          attachPage(page);
          if (!page.isClosed()) await page.evaluate(script).catch(() => gap('page_unreadable'));
        }
      } catch { gap('context_unavailable'); }
    })();
    contexts.set(context, ready);
    return ready;
  }
  function after(owner, method, attach) {
    const original = owner[method];
    if (typeof original !== 'function') return;
    owner[method] = async function(...args) {
      const value = await original.apply(this, args);
      try { await attach(value); } catch { gap('context_unavailable'); }
      return value;
    };
  }
  async function attachBrowser(browser) {
    if (browsers.has(browser)) return;
    browsers.add(browser);
    // The event also catches contexts created by the runner internally. Await the public creator for older
    // Playwright versions and so the page's first navigation cannot race the registration of its init script.
    browser.on('context', context => { void attachContext(context); });
    after(browser, 'newContext', attachContext);
    beforeClose(browser, () => Promise.all(browser.contexts().flatMap(context => context.pages().map(collect))));
    await Promise.all(browser.contexts().map(attachContext));
  }
  process.on('exit', save);
  try {
    const reader = fs.readFileSync(path.join(__dirname, 'control_coverage.js'), 'utf8');
    script = '(() => { if (window !== window.top || globalThis.__daodanControlSnapshot) return;\n' +
      reader + '\n;(' + installPublisher.toString() + ')(); })()';
  } catch { gap('reader_unavailable'); return; }
  // Hook module loading so pnpm workspaces and nested packages use their own Playwright version.
  const load = Module._load;
  Module._load = function(request, ...args) {
    const value = load.call(this, request, ...args);
    if (request === 'playwright' || request === 'playwright-core') {
      for (const type of [value.chromium, value.webkit, value.firefox]) {
        if (!type || patched.has(type)) continue;
        patched.add(type);
        for (const method of ['launch', 'connect', 'connectOverCDP']) after(type, method, attachBrowser);
        after(type, 'launchPersistentContext', attachContext);
      }
    }
    return value;
  };
}

const prefix = process.env.DYN_CONTROLS_OUT;
if (prefix) observe(prefix + '-' + process.pid + '-' + threadId + '.json');
