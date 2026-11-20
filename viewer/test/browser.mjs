import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const assets = new URL('../../daodan/assets/', import.meta.url);
const envelope = JSON.parse(await readFile(new URL('./fixture.json', import.meta.url)));
const run = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'demo' };
const groups = ['Client', 'Server'].map(name => ({
  id: name, name, kind: 'directory', files: [name + '/main.ts'], location: 'internal', status: 'confirmed', group: null, evidence: [],
}));
const graph = { grouping: 'directories', nodes: groups, open: [], edges: [{ source: 'Client', target: 'Server', counts: { imports: 1 }, evidence: [] }],
  gaps: [], files: 2, levels: ['codice'], meta: {}, unassigned: { count: 0 } };
const browser = await chromium.launch();
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 850 } });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  const errors = [];
  page.on('pageerror', error => { errors.push(error.message); console.error(error); });
  // Deliver real packaged assets and the layout worker. Only the repository and run responses are fixtures.
  await context.route('http://daodan.test/**', async route => {
    const url = new URL(route.request().url()), path = url.pathname;
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
      constructor() { super(); setTimeout(() => this.dispatchEvent(new MessageEvent('app', { data: JSON.stringify(state) })), 0); }
      close() {}
    };
  }, { context: run, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: {}, links: { state: 'idle' } });
  await page.goto('http://daodan.test/app/?token=test');
  const nav = page.getByRole('navigation', { name: 'Navigazione principale' });
  await page.locator('#stage-premap').click();
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
  await page.locator('#preview-diagram .im-graph-node').first().click();
  assert.ok(await page.getByRole('dialog').isVisible());
  await page.keyboard.press('Escape');
  await nav.getByRole('button', { name: 'Grafo', exact: true }).click();
  const diagram = page.getByRole('region', { name: 'Grafo del codice' });
  await diagram.locator('[data-im-node="Client"] .im-graph-node').press('ArrowRight');
  assert.equal(await page.evaluate(() => document.activeElement.closest('[data-im-node]').dataset.imNode), 'Server');
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('.graph-inspector h2').innerText(), 'Server');
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
  const canvas = page.getByRole('region', { name: 'Naviga il grafo' });
  const node = canvas.locator('.im-graph-node').first();
  await node.waitFor({ timeout: 15000 });
  const name = await node.getAttribute('title');
  await node.click();
  await page.waitForFunction(label => document.querySelector('.inspector h2')?.textContent === label, name, { timeout: 5000 });
  assert.equal(await page.locator('.inspector h2').innerText(), name);
  const file = page.locator('.im-file-selector');
  await file.setInputFiles({ name: 'shop.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(envelope)) });
  await page.getByRole('tab', { name: 'Fisica' }).click();
  await canvas.locator('.im-graph-node').first().waitFor();
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.waitForFunction(() => document.documentElement.dataset.imTheme === 'dark');
  assert.deepEqual(errors, []);
  console.log('Passed app navigation, tree, dialog, pipeline, graph groups, mobile drawer, ELK worker, JSON import and theme.');
} finally { await browser.close(); }
