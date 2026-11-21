import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const assets = new URL('../../daodan/assets/', import.meta.url);
const envelope = JSON.parse(await readFile(new URL('./fixture.json', import.meta.url)));
let pathsClassified = false;
const run = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'demo' };
const groups = ['Client', 'Server'].map(name => ({
  id: name, name, kind: 'directory', files: [name + '/main.ts'], location: 'internal', status: 'confirmed', group: null, evidence: [],
}));
const graph = { grouping: 'directories', nodes: groups, open: [], edges: ['confirmed', 'observed', 'sampled'].map(status => ({
    source: 'Client', target: 'Server', counts: { calls: 1 }, status, evidence: [],
  })).concat({source: 'Client', target: 'Server', counts: { calls: 1 }, status: 'observed', conflict: true, evidence: []}),
  gaps: [], files: 2, levels: ['codice'], meta: {}, unassigned: { count: 0 } };
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH });
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 850 } });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  const errors = [];
  page.on('pageerror', error => { errors.push(error.message); console.error(error); });
  // Deliver real packaged assets and the layout worker. Only the repository and run responses are fixtures.
  await context.route('http://daodan.test/**', async route => {
    const url = new URL(route.request().url()), path = url.pathname;
    if (path === '/api/app/paths') {
      const offset = Number(url.searchParams.get('offset'));
      const card = { card_id: 'save', handler: 'ui.ts::save', kind: 'azione', site: 'ui.ts:4',
        event: 'onClick', label: 'Salva ordine' };
      if (url.searchParams.get('effects') === '1') return route.fulfill({ json: {
        offset, count: 2, writes: 3, reached: 1, without_entry: 2, next_offset: offset ? null : 1,
        effects: [{ n: offset + 1, writer: 'store.py::write', site: 'store.py:5',
          effect: offset ? 'store:audit' : 'store:registro', reason: 'Nessun ingresso raggiunge il gestore',
          stopped_at: 'ui.ts:8' }] } });
      if (!pathsClassified) return route.fulfill({ json: { cards: [], count: 0, offset, next_offset: null } });
      if (!url.searchParams.has('id')) return route.fulfill({ json: { offset, count: 2, next_offset: offset ? null : 1,
        cards: [offset ? { ...card, card_id: 'cancel', label: 'Annulla ordine' } : card] } });
      const steps = [{ n: 1, type: 'scrive', from: card.handler, to: 'store:ordini', site: 'ui.ts:6',
        end: 'effetto', origin: 'dedotto' }, { n: 2, type: 'chiama', from: card.handler, to: 'ui.ts::notify',
        site: 'ui.ts:8', end: 'lacuna', confidence: 'sampled', reason: 'Destinazione campionata' }];
      return route.fulfill({ json: { card, steps: [steps[offset]], offset, count: 2, next_offset: offset ? null : 1 } });
    }
    if (path === '/api/app/graph') {
      const open = JSON.parse(url.searchParams.get('open') || '[]');
      return route.fulfill({ json: open.length ? { ...graph, open: [{ ...groups[0], parent: null }],
        nodes: [{ ...groups[0], id: 'child', name: 'main.ts', group: 'Client' }, groups[1]] } : graph });
    }
    if (path === '/api/app/premap') return route.fulfill({ json: {
      files: ['src/main.ts'], units: [], technologies: [], languages: [], dependencies: [],
    } });
    if (path === '/data/visual.json') return route.fulfill({ json: envelope });
    if (path.startsWith('/api/')) return route.fulfill({ status: 404, json: {} });
    const app = path.startsWith('/app/');
    const part = path.slice(app ? 5 : 1) || 'index.html';
    const mime = { html: 'text/html', css: 'text/css', js: 'text/javascript' }[part.split('.').at(-1)];
    await route.fulfill({ body: await readFile(new URL((app ? 'app/' : 'viewer/') + part, assets)), contentType: mime });
  });
  await page.addInitScript(state => {
    window.EventSource = class extends EventTarget {
      constructor() {
        super();
        const publish = frame => this.dispatchEvent(new MessageEvent('app', { data: JSON.stringify(frame) }));
        window.setMapState = mapped => publish({ ...state, mapped });
        setTimeout(() => publish(state), 0);
      }
      close() {}
    };
  }, { context: run, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: {}, links: { state: 'idle' } });
  await page.goto('http://daodan.test/app/?token=test');
  const appCss = await page.locator('link[rel="stylesheet"]').getAttribute('href');
  const nav = page.getByRole('navigation', { name: 'Navigazione principale' });
  await page.locator('#stage-premap').click();
  const directories = page.getByRole('radio', { name: 'Directory', exact: true });
  const units = page.getByRole('radio', { name: 'Unità tecniche' });
  await directories.focus();
  await directories.press('ArrowRight');
  assert.ok(await units.isChecked());
  assert.ok(await units.evaluate(el => document.activeElement === el));
  await units.press('ArrowLeft');
  assert.ok(await directories.isChecked());
  assert.equal(await page.locator('.im-metric').count(), 4);
  const tree = page.getByRole('tree');
  await tree.getByRole('treeitem', { name: 'main.ts' }).press('Enter');
  assert.match(await page.locator('#tree-selection').innerText(), /src\/main.ts/);
  await page.getByRole('button', { name: 'Provenienza', exact: true }).click();
  assert.ok(await page.getByRole('dialog').isVisible());
  await page.keyboard.press('Escape');
  assert.equal(await page.getByRole('dialog').count(), 0);
  await page.locator('#stage-analysis').click();
  await page.locator('#preview-diagram .im-graph-node').first().waitFor();
  assert.equal(await page.locator('#pipeline-steps li').count(), 5);
  const partialMap = { state: 'incomplete', cause: 'the recorded map still has stale or incomplete records',
    needs_review: { nodes: { count: 2, ids: ['a', 'b'] }, flows: { count: 1, ids: ['c'] },
      refused_proposals: { count: 1, ids: ['request:d'] } } };
  await page.evaluate(mapped => window.setMapState(mapped), partialMap);
  const notice = page.locator('#map-status [role="status"]');
  await notice.getByText('Mappa del sistema parziale').waitFor();
  assert.match(await notice.innerText(), /2 nodi, 1 flusso, 1 proposta rifiutata/);
  assert.match(await notice.innerText(), /revisione precedente/);
  await page.locator('#stage-synthesis').click();
  const paths = page.getByRole('region', { name: 'Percorsi per ingresso' });
  await paths.getByText('Nessun ingresso classificato per questo snapshot.').waitFor();
  pathsClassified = true;
  await page.evaluate(() => window.setMapState({ state: 'done', discovery: { count: 2 } }));
  await paths.getByRole('button', { name: /Salva ordine/ }).click();
  await paths.getByText('store:ordini', { exact: true }).waitFor();
  await paths.getByText('Effetto', { exact: true }).waitFor();
  await paths.getByRole('button', { name: 'Passaggi successivi' }).click();
  await paths.getByText('Destinazione campionata', { exact: true }).waitFor();
  assert.match(await paths.innerText(), /campionata dal profiler/);
  await paths.getByRole('button', { name: 'Torna agli ingressi' }).click();
  await paths.getByRole('button', { name: 'Ingressi successivi' }).click();
  await paths.getByRole('button', { name: /Annulla ordine/ }).waitFor();
  await paths.getByRole('button', { name: 'Ingressi precedenti' }).click();
  await paths.getByRole('button', { name: 'Scritture senza ingresso' }).click();
  await paths.getByText('store:registro', { exact: true }).waitFor();
  assert.match(await paths.innerText(), /2 di 3 scritture/);
  await paths.getByRole('button', { name: 'Scritture successive' }).click();
  await paths.getByText('store:audit', { exact: true }).waitFor();
  await paths.getByRole('button', { name: 'Torna agli ingressi' }).click();
  await paths.getByRole('button', { name: /Salva ordine/ }).waitFor();
  await page.evaluate(mapped => window.setMapState(mapped), partialMap);
  await page.getByText('Mappa del sistema parziale').waitFor();
  await page.getByText('1 osservata in esecuzione · 1 campionata dal profiler · 1 in conflitto').waitFor();
  await page.evaluate(() => window.setMapState({ state: 'done' }));
  await page.getByText('Mappa del sistema registrata').waitFor();
  assert.equal(await page.getByText('Mappa del sistema parziale').count(), 0);
  await page.locator('#stage-analysis').click();
  await page.locator('#preview-diagram .im-graph-node').first().click();
  assert.ok(await page.getByRole('dialog').isVisible());
  await page.keyboard.press('Escape');
  await nav.getByRole('button', { name: 'Grafo', exact: true }).click();
  const diagram = page.getByRole('region', { name: 'Grafo del codice' });
  await diagram.locator('[data-im-node="Client"] .im-graph-node').press('ArrowRight');
  assert.equal(await page.evaluate(() => document.activeElement.closest('[data-im-node]').dataset.imNode), 'Server');
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('.im-detail-panel h2').innerText(), 'Server');
  const titles = await diagram.locator('.im-graph-edge title').allTextContents();
  assert.ok(titles.some(label => label.includes('osservata in esecuzione')));
  assert.ok(titles.some(label => label.includes('campionata dal profiler')));
  assert.ok(titles.some(label => label.includes('destinazioni in conflitto')));
  await page.locator('.im-detail-panel summary', { hasText: 'Prove delle chiamate' }).click();
  await page.getByText('Client → Server · osservata in esecuzione', { exact: true }).waitFor();
  await page.getByText('Client → Server · campionata dal profiler', { exact: true }).waitFor();
  await page.getByText('Client → Server · osservata in esecuzione · destinazioni in conflitto', { exact: true }).waitFor();
  await diagram.getByRole('button', { name: 'Apri Client' }).click();
  await diagram.getByRole('button', { name: 'Chiudi Client' }).waitFor();
  assert.equal(await diagram.locator('.im-graph-group').count(), 1);
  await diagram.getByRole('button', { name: 'Chiudi Client' }).click();
  await diagram.getByRole('button', { name: 'Apri Client' }).waitFor();
  await page.setViewportSize({ width: 390, height: 820 });
  await page.getByRole('button', { name: 'Navigazione', exact: true }).click();
  await nav.getByRole('button', { name: 'Motore e domande' }).click();
  await page.locator('#question').waitFor({ state: 'visible' });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));

  await page.setViewportSize({ width: 1280, height: 850 });
  await page.goto('http://daodan.test/');
  const viewerCss = await page.locator('link[rel="stylesheet"]').getAttribute('href');
  assert.deepEqual(await readFile(new URL('app/' + appCss, assets)), await readFile(new URL('viewer/' + viewerCss, assets)));
  const canvas = page.getByRole('region', { name: 'Naviga il grafo' });
  const node = canvas.locator('.im-graph-node').first();
  await node.waitFor({ timeout: 15000 });
  const name = await node.getAttribute('title');
  await node.click();
  await page.waitForFunction(label => document.querySelector('.im-detail-panel h2')?.textContent === label, name, { timeout: 5000 });
  assert.equal(await page.locator('.im-detail-panel h2').innerText(), name);
  const flow = page.locator('.im-navigation-panel .im-row').first();
  await flow.click();
  assert.equal(await flow.getAttribute('aria-pressed'), 'true');
  assert.ok(await page.locator('.im-timeline li').count() > 0);
  await page.locator('.im-canvas-message').waitFor({ state: 'hidden' });
  await canvas.locator('.im-graph-node').first().waitFor();
  const file = page.locator('.im-file-selector');
  await file.setInputFiles({ name: 'shop.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(envelope)) });
  await page.getByRole('tab', { name: 'Logica' }).press('ArrowRight');
  await page.keyboard.press('Enter');
  assert.equal(await page.getByRole('tab', { name: 'Fisica' }).getAttribute('aria-selected'), 'true');
  await canvas.locator('.im-graph-node').first().waitFor();
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.waitForFunction(() => document.documentElement.dataset.imTheme === 'dark');
  await context.route('**/api/runs', route => route.fulfill({ json: { runs: [{ run_id: 'demo', readable: true }] } }));
  await context.route('**/api/events?*', route => route.fulfill({ json: { events: [], next_cursor: 0, has_more: false } }));
  await context.route('**/api/requests', route => route.fulfill({ json: { requests: [] } }));
  await context.route('**/api/findings', route => route.fulfill({ json: { findings: [], gaps: [] } }));
  await page.reload();
  const disclosure = page.locator('summary', { hasText: 'Sessione e review' });
  await disclosure.press('Enter');
  await page.getByRole('button', { name: 'Invia' }).waitFor();
  await disclosure.press('Enter');
  await page.getByRole('button', { name: 'Invia' }).waitFor({ state: 'detached' });
  assert.deepEqual(errors, []);
  console.log('Passed app navigation, tree, dialog, pipeline, graph groups, mobile drawer, ELK worker, JSON import and theme.');
} finally { await browser.close(); }
