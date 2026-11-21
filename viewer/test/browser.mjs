import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const assets = new URL('../../daodan/assets/', import.meta.url);
const envelope = JSON.parse(await readFile(new URL('./fixture.json', import.meta.url)));
envelope.technologies = [{ id: 'react', name: 'React', type: 'framework', paths: ['web/checkout.tsx'] }];
let pathsClassified = false;
// What the fixture server does next, so that a test can make a route fail or wait.
const engineRequests = [];
const mode = { graphStatus: 200, premapDelay: 0, linkStatus: 200, checkDelay: 0 };
const run = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'demo' };
const groups = ['Client', 'Server'].map(name => ({
  id: name, name, mark: name === 'Client' ? 'react' : undefined, kind: 'directory', files: Array.from({ length: name === 'Server' ? 6 : 1 }, (_, n) => `${name}/file${n}.ts`), location: 'internal', status: 'confirmed', group: null, evidence: [],
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
    if (path === '/api/app/engine') {
      engineRequests.push(JSON.parse(route.request().postData() ?? '{}'));
      return route.fulfill({ json: { engine: 'openai', engines: ['openai'], api_key: 'unset', base_url: 'https://api.test/v1', model: 'm' } });
    }
    if (path === '/api/app/link') return route.fulfill(mode.linkStatus === 200 ? { json: {} } : { status: mode.linkStatus, json: { error: 'collegamento non riuscito' } });
    if (path === '/api/app/check') {
      await new Promise(resolve => setTimeout(resolve, mode.checkDelay));
      return route.fulfill({ json: { state: 'accessible', repository: { owner: 'demo', name: 'shop' }, default: 'main',
        branches: [{ name: 'main', commit: '1'.repeat(40) }] } });
    }
    if (path === '/api/app/graph') {
      if (mode.graphStatus !== 200) return route.fulfill({ status: mode.graphStatus, json: { error: 'grafo non letto' } });
      const open = JSON.parse(url.searchParams.get('open') || '[]');
      return route.fulfill({ json: open.length ? { ...graph, open: [{ ...groups[0], parent: null }],
        nodes: [{ ...groups[0], id: 'child', name: 'main.ts', group: 'Client' }, groups[1]] } : graph });
    }
    if (path === '/api/app/premap') {
      await new Promise(resolve => setTimeout(resolve, mode.premapDelay));
      return route.fulfill({ json: {
      files: ['src/main.ts'], technologies: [], languages: [],
      units: [{ id: 'web', name: 'web', kind: 'npm', root: '.', manifest: 'package.json', status: 'confirmed',
        dependencies: [{ name: 'left-pad', scope: 'runtime', state: 'declared', source: 'package.json', version: '^1.3.0', direct: true }] }],
      } });
    }
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
        window.setServerState = patch => publish({ ...state, ...patch });
        setTimeout(() => publish(state), 0);
      }
      close() {}
    };
  }, { context: run, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: { engine: 'claude', engines: ['claude'] }, links: { state: 'idle' } });
  await page.goto('http://daodan.test/app/?token=test');
  const appCss = await page.locator('link[rel="stylesheet"]').getAttribute('href');
  assert.equal(await page.locator('body > .im-shell').count(), 1);
  const selectable = locator => locator.evaluate(el => getComputedStyle(el).userSelect !== 'none');
  const palette = page.getByRole('dialog', { name: 'Cerca un comando' });
  // A tone is one of the four statuses; the accent stays on a chip or a dot, as data. The graph's edges, and the samples of its key, have their own.
  const tonesAreCanon = async () => {
    const found = await page.evaluate(() => [...document.querySelectorAll('[data-im-tone]')].filter(el => !el.closest('svg, .im-graph-legend'))
      .map(el => [el.dataset.imTone, el.className]));
    for (const [tone, name] of found) assert.ok(['ok', 'warn', 'err', 'info'].includes(tone) || (tone === 'accent' && /(^| )im-(chip|dot)( |$)/.test(name)), `${tone} on ${name}`);
  };
  const choose = async command => {
    await page.keyboard.press('Control+k');
    await palette.getByRole('option', { name: command }).click();
  };
  const inContent = () => page.evaluate(() => !!document.activeElement?.closest('.im-content'));
  const theme = () => page.evaluate(() => document.documentElement.dataset.imTheme);
  await page.keyboard.press('Control+k');
  await palette.waitFor();
  assert.ok(await palette.getByRole('option', { name: 'Tema scuro' }).isVisible());
  await page.keyboard.press('Escape');
  await choose('Tema scuro');
  await page.waitForFunction(() => document.documentElement.dataset.imTheme === 'dark');
  assert.equal(await page.evaluate(() => localStorage.getItem('daodan.theme')), 'dark');
  await page.reload();
  await page.locator('#stage-premap').waitFor();
  assert.equal(await theme(), 'dark');
  const tabs = page.getByRole('tablist', { name: 'Schermate' });
  const screens = await tabs.getByRole('tab').allInnerTexts();
  assert.deepEqual(screens, ['Analisi', 'Grafo', 'Motore e domande']);
  assert.equal(await page.locator('.im-sidebar').count(), 0);
  assert.ok(await page.locator('#use-repository').getAttribute('title'));
  assert.ok(await page.getByLabel('Branch da analizzare').isDisabled());
  await page.getByLabel('URL GitHub').waitFor();
  await page.locator('#verify-repository').click();
  assert.match(await page.locator('#repository-error').innerText(), /^Errore: /);
  await page.locator('#repository-url').fill('https://github.com/demo/shop');
  mode.checkDelay = 600;
  await page.locator('#verify-repository').click();
  await page.waitForFunction(() => document.getElementById('verify-repository').getAttribute('aria-busy') === 'true');
  assert.equal(await page.locator('#verify-repository').innerText(), 'Verifica accesso');
  await page.waitForFunction(() => document.getElementById('verify-repository').getAttribute('aria-busy') !== 'true');
  await tonesAreCanon();
  mode.graphStatus = 500;
  mode.premapDelay = 1000;
  await page.locator('#stage-premap').click();
  await page.locator('[data-im-state-layer="loading"]').waitFor();
  await page.getByRole('tree').waitFor();
  mode.premapDelay = 0;
  await page.locator('#context-repo').waitFor();
  assert.equal(await page.locator('#context-repo').innerText(), 'demo/shop');
  assert.equal(await page.locator('#context-branch').innerText(), 'main');
  assert.equal(await page.locator('#context-commit').innerText(), '1'.repeat(12));
  assert.equal(await page.locator('#context-run-id').innerText(), 'demo');
  assert.ok(await selectable(page.locator('#context-commit')));
  assert.ok(await selectable(page.locator('.im-table td strong', { hasText: 'left-pad' })));
  const footer = page.locator('.im-footer');
  assert.match(await footer.innerText(), /App locale/);
  assert.match(await footer.locator('.im-footer-keys').innerText(), /Ctrl\s*K[\s\S]*Ctrl\s*F/);
  assert.equal(await page.locator('#service-dot').getAttribute('data-im-tone'), 'ok');
  await tabs.getByRole('tab', { name: 'Analisi' }).focus();
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('Enter');
  assert.equal(await page.getByRole('tab', { name: /^Grafo/ }).getAttribute('aria-selected'), 'true');
  await page.keyboard.press('ArrowLeft');
  await page.keyboard.press('Enter');
  assert.equal(await tabs.getByRole('tab', { name: 'Analisi' }).getAttribute('aria-selected'), 'true');
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
  const provenance = page.getByRole('button', { name: 'Provenienza', exact: true });
  await provenance.click();
  const detail = page.getByRole('region', { name: 'Provenienza della pre-mappa' });
  assert.ok(await detail.isVisible());
  await page.keyboard.press('Escape');
  assert.ok(await detail.isHidden());
  assert.equal(await page.evaluate(() => document.activeElement?.textContent?.trim()), 'Provenienza');
  await tabs.getByRole('tab', { name: 'Grafo' }).click();
  const failed = page.locator('.im-failure');
  assert.match(await failed.innerText(), /Errore[\s\S]*grafo non letto[\s\S]*Riprova/);
  mode.graphStatus = 200;
  await failed.getByRole('button', { name: 'Riprova' }).click();
  await page.getByRole('region', { name: 'Grafo del codice' }).waitFor();
  assert.equal(await tabs.getByRole('tab', { name: /^Grafo/ }).locator('.im-count').innerText(), '2');
  const legend = await page.locator('.im-graph-legend').innerText();
  assert.ok(legend.includes('Osservata in esecuzione') && legend.includes('Incerta') && !legend.includes('■'));
  await tonesAreCanon();
  await tabs.getByRole('tab', { name: /^Analisi/ }).click();
  await page.locator('#stage-analysis').click();
  await page.locator('#preview-diagram .im-graph-node').first().waitFor();
  assert.equal(await page.locator('#pipeline-steps li').count(), 5);
  await page.waitForFunction(() => !document.querySelector('img.im-inline-mark'));  // the mark that does not load is the icon
  assert.ok(await page.locator('#preview-diagram [data-im-node="Client"] .im-icon').count() > 0);
  mode.linkStatus = 500;
  await page.getByRole('button', { name: 'Trova i legami' }).click();
  const linkError = page.locator('.im-notice', { hasText: 'collegamento non riuscito' });
  await linkError.waitFor();
  assert.match(await linkError.innerText(), /Errore/);
  await page.waitForTimeout(6500);
  assert.equal(await linkError.count(), 1);
  await linkError.getByRole('button', { name: 'Chiudi' }).click();
  assert.equal(await linkError.count(), 0);
  await tonesAreCanon();
  const partialMap = { state: 'incomplete', cause: 'the recorded map still has stale or incomplete records',
    needs_review: { nodes: { count: 2, ids: ['a', 'b'] }, flows: { count: 1, ids: ['c'] },
      refused_proposals: { count: 1, ids: ['request:d'] } } };
  await page.evaluate(mapped => window.setMapState(mapped), partialMap);
  const notice = page.locator('#map-status .im-note');
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
  const preview = page.getByRole('region', { name: 'Client' });
  await preview.getByRole('button', { name: 'Apri nel grafo' }).waitFor();
  await page.keyboard.press('Escape');
  assert.ok(await preview.isHidden());
  await tabs.getByRole('tab', { name: /^Grafo/ }).click();
  const diagram = page.getByRole('region', { name: 'Grafo del codice' });
  await page.keyboard.press('Control+f');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'graph-search');
  await tabs.getByRole('tab', { name: /^Grafo/ }).focus();
  await page.keyboard.press('F6');
  assert.ok(await inContent());
  await diagram.locator('[data-im-node="Client"] .im-graph-node').press('ArrowRight');
  assert.equal(await page.evaluate(() => document.activeElement.closest('[data-im-node]').dataset.imNode), 'Server');
  await page.keyboard.press('Enter');
  const group = page.getByRole('region', { name: 'Dettaglio del gruppo' });
  assert.equal(await group.locator('h2').innerText(), 'Server');
  const titles = await diagram.locator('.im-graph-edge title').allTextContents();
  assert.ok(titles.some(label => label.includes('osservata in esecuzione')));
  assert.ok(titles.some(label => label.includes('campionata dal profiler')));
  assert.ok(titles.some(label => label.includes('destinazioni in conflitto')));
  await group.locator('summary', { hasText: 'Prove delle chiamate' }).click();
  await page.getByText('Client → Server · osservata in esecuzione', { exact: true }).waitFor();
  await page.getByText('Client → Server · campionata dal profiler', { exact: true }).waitFor();
  await page.getByText('Client → Server · osservata in esecuzione · destinazioni in conflitto', { exact: true }).waitFor();
  await group.getByRole('button', { name: /Tutti i 6 file/ }).click();
  assert.match(await page.locator('.im-inspector .im-panel-title:visible').innerText(), /File di Server/);
  await page.keyboard.press('Escape');
  assert.equal(await group.locator('h2').innerText(), 'Server');
  await diagram.getByRole('button', { name: 'Apri Client' }).click();
  await diagram.getByRole('button', { name: 'Chiudi Client' }).waitFor();
  assert.equal(await diagram.locator('.im-graph-group').count(), 1);
  await diagram.getByRole('button', { name: 'Chiudi Client' }).click();
  await diagram.getByRole('button', { name: 'Apri Client' }).waitFor();
  await tabs.getByRole('tab', { name: 'Analisi' }).click();
  assert.ok(await page.locator('.im-inspector').isHidden());
  await tabs.getByRole('tab', { name: /^Grafo/ }).click();
  await page.setViewportSize({ width: 900, height: 820 });
  await group.waitFor();
  const [content, inspector] = await Promise.all([page.locator('.im-content').boundingBox(), page.locator('.im-inspector').boundingBox()]);
  assert.ok(inspector.x < content.x + content.width - 100);
  await group.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  assert.ok(await page.locator('.im-inspector').isHidden());
  assert.equal(await page.getByRole('dialog').count(), 0);
  await page.setViewportSize({ width: 390, height: 820 });
  assert.equal(await tabs.isVisible(), false);
  await page.getByRole('button', { name: 'Schermate', exact: true }).click();
  await page.getByRole('menuitemradio', { name: 'Motore e domande' }).click();
  await page.getByRole('menu').waitFor({ state: 'detached' });
  await page.locator('#question').waitFor({ state: 'visible' });
  await tonesAreCanon();
  assert.equal(await page.locator('textarea.im-textarea#question').count(), 1);
  assert.ok(await page.getByRole('button', { name: 'Chiedi' }).isEnabled());
  await page.evaluate(() => window.setServerState({ engine: { engine: 'openai', engines: ['claude', 'openai'], api_key: 'set', base_url: 'https://api.test/v1', model: 'm' } }));
  await page.getByRole('combobox', { name: 'Motore', exact: true }).waitFor();
  await page.getByRole('combobox', { name: 'Motore', exact: true }).selectOption('openai');
  for (const label of [/^Indirizzo dell’endpoint/, /^Modello/, /^Chiave/, 'Domanda']) await page.getByLabel(label, { exact: typeof label === 'string' }).waitFor();
  assert.ok(await page.locator('.im-field-hint', { hasText: 'Chiave impostata' }).isVisible());
  const forget = page.getByRole('button', { name: 'Rimuovi la chiave' });
  await forget.click();
  const sure = page.getByRole('alertdialog', { name: 'Rimuovere la chiave?' });
  await sure.waitFor();
  assert.equal(await page.evaluate(() => document.activeElement.textContent.trim()), 'Annulla');
  assert.match(await sure.innerText(), /deposito delle credenziali[\s\S]*non si può recuperare/);
  await page.keyboard.press('Escape');
  await sure.waitFor({ state: 'detached' });
  assert.equal(engineRequests.length, 0);
  await forget.click();
  await sure.getByRole('button', { name: 'Rimuovi la chiave' }).click();
  await page.waitForFunction(() => document.querySelector('#engine-said')?.textContent.includes('Chiave rimossa'));
  assert.deepEqual(engineRequests, [{ api_key: '' }]);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));

  await page.setViewportSize({ width: 1280, height: 850 });
  await page.goto('http://daodan.test/');
  const viewerCss = await page.locator('link[rel="stylesheet"]').getAttribute('href');
  assert.deepEqual(await readFile(new URL('app/' + appCss, assets)), await readFile(new URL('viewer/' + viewerCss, assets)));
  const canvas = page.getByRole('region', { name: 'Naviga il grafo' });
  const node = canvas.locator('.im-graph-node').first();
  await node.waitFor({ timeout: 15000 });
  const name = await node.getAttribute('title');
  const inspectorBox = page.locator('.im-inspector');
  assert.ok(await inspectorBox.isHidden());
  await node.click();
  await page.waitForFunction(label => document.querySelector('.im-inspector h2')?.textContent === label, name, { timeout: 5000 });
  assert.equal(await page.locator('.im-inspector h2').innerText(), name);
  assert.equal(await page.locator('body > #app.im-root > .im-shell').count(), 1);
  assert.match(await page.locator('.im-footer').innerText(), /entità[\s\S]*nodi/);
  assert.match(await page.locator('.im-status').innerText(), /shop · run fixture/);
  await page.keyboard.press('Control+k');
  await palette.waitFor();
  await page.keyboard.press('Escape');
  await palette.waitFor({ state: 'detached' });
  assert.ok(await inspectorBox.isVisible());  // the palette took that Escape
  await node.focus();
  await page.keyboard.press('Escape');
  await inspectorBox.waitFor({ state: 'hidden' });
  await page.getByRole('button', { name: 'Informazioni sul progetto' }).click();
  assert.equal(await inspectorBox.locator('.im-panel-title').innerText(), 'Informazioni sul progetto');
  assert.match(await inspectorBox.innerText(), /Tecnologie[\s\S]*React/);
  await inspectorBox.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  assert.ok(await inspectorBox.isHidden());
  await node.click();
  await inspectorBox.waitFor();
  const flow = page.locator('.im-sidebar .im-row').first();
  await flow.click();
  assert.equal(await flow.getAttribute('aria-pressed'), 'true');
  assert.ok(await page.locator('.im-timeline li').count() > 0);
  assert.ok(await selectable(page.locator('.im-timeline li').first()));
  assert.ok(await selectable(page.locator('.im-inspector code').first()));
  await page.locator('.im-canvas-message').waitFor({ state: 'hidden' });
  await canvas.locator('.im-graph-node').first().waitFor();
  assert.ok((await canvas.boundingBox()).height >= 320);
  assert.equal(await theme(), 'dark');
  await page.keyboard.press('Control+f');
  assert.equal(await page.evaluate(() => document.activeElement?.getAttribute('aria-label')), 'Cerca per nome');
  await page.locator('.im-sidebar .im-row').first().focus();
  await page.keyboard.press('F6');
  assert.ok(await inContent());
  await choose('Tema come il sistema');
  await page.emulateMedia({ colorScheme: 'light' });
  await page.waitForFunction(() => document.documentElement.dataset.imTheme === 'light');
  const file = page.locator('.im-file-selector');
  await file.setInputFiles({ name: 'shop.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(envelope)) });
  await page.getByRole('tab', { name: 'Logica' }).press('ArrowRight');
  await page.keyboard.press('Enter');
  assert.equal(await page.getByRole('tab', { name: 'Fisica' }).getAttribute('aria-selected'), 'true');
  await canvas.locator('.im-graph-node').first().waitFor();
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.waitForFunction(() => document.documentElement.dataset.imTheme === 'dark');
  await tonesAreCanon();
  await page.setViewportSize({ width: 700, height: 820 });  // the sidebar is the rail: a row is its rail item
  const rows = await page.locator('.im-sidebar .im-row').count();
  assert.ok(rows > 0);
  assert.equal(await page.locator('.im-sidebar .im-row > .im-rail-item:visible').count(), rows);
  await page.setViewportSize({ width: 900, height: 820 });  // the inspector covers the content's edge
  await node.click();
  await inspectorBox.waitFor();
  await inspectorBox.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  assert.ok(await inspectorBox.isHidden());
  await page.setViewportSize({ width: 390, height: 820 });
  await page.getByRole('button', { name: 'Viste', exact: true }).click();
  await page.getByRole('menuitemradio', { name: 'Logica' }).click();
  await page.waitForFunction(() => document.getElementById('logical-tab').getAttribute('aria-selected') === 'true');
  await page.getByRole('button', { name: 'Viste', exact: true }).click();
  await page.getByRole('menuitemradio', { name: 'Fisica' }).click();
  await page.waitForFunction(() => document.getElementById('physical-tab').getAttribute('aria-selected') === 'true');
  await canvas.locator('.im-graph-node').first().waitFor();
  assert.ok((await canvas.boundingBox()).height >= 200);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.setViewportSize({ width: 1280, height: 850 });
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
