import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const assets = new URL('../../daodan/assets/', import.meta.url);
const envelope = JSON.parse(await readFile(new URL('./fixture.json', import.meta.url)));
// What the fixture lacks for the details: evidence as the server writes it, and lists longer than what is in sight at first.
const parts = Array.from({ length: 9 }, (_, n) => `web/part${n}.tsx`);
envelope.technologies = [{ id: 'react', name: 'React', type: 'framework', paths: ['web/checkout.tsx', ...parts] }];
Object.assign(envelope.entities.find(entity => entity.ref === 'component:web'), { technologies: ['react'], evidence: parts.map((path, n) => ({ path, line: n + 1 })) });
envelope.flows.push({ ...envelope.flows[1], ref: 'flow:lungo', label: 'Flusso lungo', complete: true, gaps: [], steps: Array(43).fill(envelope.flows[1].steps[0]) });
let pathsClassified = false;
// What the fixture server does next, so that a test can make a route fail or wait.
const engineRequests = [], askRequests = [];
const mode = { graphStatus: 200, premapDelay: 0, linkStatus: 200, checkDelay: 0, exportBroken: false, exportDelay: 0 };
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
    if (path === '/api/app/symbols') return route.fulfill({ json: { file: 'child', symbols: [{ id: 'child::save', name: 'save', lines: [1, 5] }], calls: [] } });
    if (path === '/api/app/ask') {
      askRequests.push(1);
      return route.fulfill({ json: {} });
    }
    if (path === '/api/app/answer') return route.fulfill({ json: { events: [{ kind: 'tool', name: 'cerca', arguments: 'token' }], next: 1, state: 'done', text: 'Lo firma auth.ts', cause: null } });
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
        nodes: [{ ...groups[0], id: 'child', name: 'main.ts', kind: 'file', files: [], group: 'Client' }, groups[1]] } : graph });
    }
    if (path === '/api/app/premap') {
      await new Promise(resolve => setTimeout(resolve, mode.premapDelay));
      return route.fulfill({ json: {
      files: ['src/main.ts'], technologies: [], languages: [],
      units: [{ id: 'web', name: 'web', kind: 'npm', root: '.', manifest: 'package.json', status: 'confirmed',
        dependencies: [{ name: 'left-pad', scope: 'runtime', state: 'declared', source: 'package.json', version: '^1.3.0', direct: true }] }],
      } });
    }
    if (path === '/data/visual.json') {
      await new Promise(resolve => setTimeout(resolve, mode.exportDelay));
      return route.fulfill(mode.exportBroken ? { body: 'not json', contentType: 'text/plain' } : { json: envelope });
    }
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
  await page.getByLabel('Relazioni', { exact: true }).selectOption('imports');  // the kind filter: no relation of that kind
  await page.locator('.im-graph-legend').getByText('0 relazioni visibili').waitFor();
  await page.getByRole('button', { name: 'Azzera filtri' }).click();
  await page.locator('.im-graph-legend').getByText('4 relazioni visibili').waitFor();
  const legend = await page.locator('.im-graph-legend').innerText();
  assert.ok(legend.includes('Osservata in esecuzione') && legend.includes('Incerta') && !legend.includes('■'));
  await tonesAreCanon();
  await tabs.getByRole('tab', { name: /^Analisi/ }).click();
  await page.locator('#stage-analysis').click();
  await page.locator('#preview-diagram .im-graph-node').first().waitFor();
  assert.equal(await page.locator('#pipeline-steps li').count(), 6);
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
  // A node chosen while a file list is pushed on another group: the new group replaces both, and nothing stale comes back.
  await group.getByRole('button', { name: /Tutti i 6 file/ }).click();
  await diagram.locator('[data-im-node="Client"] .im-graph-node').click();
  assert.equal(await group.locator('h2:visible').innerText(), 'Client');
  assert.equal(await page.locator('.im-inspector .im-panel-title:visible').innerText(), 'Dettaglio del gruppo');
  await group.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  assert.ok(await page.locator('.im-inspector').isHidden());
  await diagram.getByRole('button', { name: 'Apri Client' }).click();
  await diagram.getByRole('button', { name: 'Chiudi Client' }).waitFor();
  await diagram.locator('[data-im-node="child"] .im-graph-node').click();  // a file: its symbols are asked and drawn
  await group.getByText('Simboli e chiamate').waitFor();
  await group.locator('code', { hasText: 'save' }).waitFor();
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
  await page.locator('#question').fill('Dove si firma il token?');  // the question and its answer, with the tools used
  await page.getByRole('button', { name: 'Chiedi' }).click();
  await page.locator('#answer-box').getByText('Lo firma auth.ts').waitFor();
  assert.match(await page.locator('#answer-box').innerText(), /cerca token/);
  assert.notEqual(await page.getByRole('button', { name: 'Chiedi' }).getAttribute('aria-busy'), 'true');
  // A busy button ignores the pointer, not the keyboard: Enter on it must not send the question a second time.
  assert.equal(askRequests.length, 1);
  await page.evaluate(() => window.setServerState({ asked: { state: 'running', question: 'Dove si firma il token?' } }));
  await page.locator('#ask-button[aria-busy="true"]').waitFor();
  await page.locator('#ask-button').focus();
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  assert.equal(askRequests.length, 1);
  await page.evaluate(() => window.setServerState({ asked: { state: 'done', question: 'Dove si firma il token?' } }));
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

  // The Codebase Map, on Sigrid: what a person meets, by role, name and words. The scheme is what `applyTheme` writes on the root.
  const schemeIs = (where, wanted) => where.waitForFunction(value => document.documentElement.dataset.scheme === value, wanted);
  const kept = () => page.evaluate(() => localStorage.getItem('daodan.theme'));
  const fits = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
  const focused = locator => locator.evaluate(el => el === document.activeElement);
  const main = page.getByRole('main');
  const line = text => page.getByRole('status').filter({ hasText: text });  // the status row, and what it says
  const nav = page.getByRole('navigation', { name: 'Mappa' });
  const row = name => nav.getByRole('button', { name });
  const elements = nav.getByRole('list', { name: 'Elementi visibili', exact: true });
  const whole = row('Tutta la mappa');
  const info = page.getByRole('complementary', { name: 'Informazioni sul progetto' });
  const details = page.getByRole('complementary', { name: 'Dettaglio' });
  const flowPanel = page.getByRole('complementary', { name: 'Flusso', exact: true });
  const infoButton = main.getByRole('button', { name: 'Informazioni sul progetto' });
  const up = main.getByRole('button', { name: 'Su', exact: true });
  const search = main.getByLabel('Cerca per nome');
  const place = path => main.getByText(new RegExp(`^${path} · \\d+ nod`));  // the line beside the panel's title
  const closeIn = region => region.getByRole('button', { name: 'Chiudi', exact: true }).click();
  const inMain = () => page.evaluate(() => !!document.activeElement?.closest('main'));
  await page.setViewportSize({ width: 1280, height: 850 });
  mode.exportBroken = true;  // an export that cannot be read: the page waits, then says what failed, with Riprova
  mode.exportDelay = 1000;
  await page.goto('http://daodan.test/');
  assert.equal(await page.title(), 'Codebase Map');
  await main.getByRole('progressbar', { name: "Carico l'export…" }).waitFor();
  await line("Carico l'export…").waitFor();
  await nav.getByText("In attesa dell'export.").waitFor();
  assert.equal(await main.locator('[aria-busy="true"]').count(), 1);
  const unreadable = main.getByRole('alert');
  await unreadable.waitFor();
  assert.match(await unreadable.innerText(), /Errore[\s\S]*Export non leggibile[\s\S]*Riprova/);
  await line('Export non leggibile').waitFor();
  assert.ok(await selectable(unreadable.getByText('unknown schema: undefined')));
  await nav.getByText("Nessuna mappa: l'export non si legge.").waitFor();
  assert.equal(await nav.getByText("In attesa dell'export.").count(), 0);
  for (const control of [search, up, infoButton]) assert.ok(await control.isDisabled());  // in their place, with nothing to do
  assert.equal(await main.locator('[aria-busy="true"]').count(), 0);
  mode.exportBroken = false;
  mode.exportDelay = 0;
  await unreadable.getByRole('button', { name: 'Riprova' }).click();
  await line('shop · run fixture').waitFor();
  assert.equal(await unreadable.count(), 0);
  await schemeIs(page, 'dark');  // the theme chosen on the App page
  const foot = page.getByRole('contentinfo');
  assert.match(await foot.innerText(), /\d+ entità · \d+ relazioni/);
  const keys = await foot.getByRole('list', { name: 'Tasti' }).innerText();  // Ctrl+K is on its button
  assert.match(keys, /Ctrl\s*F[\s\S]*Cerca in questa vista[\s\S]*F6[\s\S]*Area successiva/);
  assert.doesNotMatch(keys, /Ctrl\s*K/);
  assert.match(await page.getByRole('button', { name: 'Comandi', exact: true }).innerText(), /Ctrl\s*K/);
  // The content is one panel: the place and what is in view beside its title.
  const panel = main.getByRole('region', { name: 'Mappa logica', exact: true });
  await panel.getByText('Sistema · 8 nodi · 6 relazioni visibili', { exact: true }).waitFor();
  assert.ok(await up.isDisabled());
  assert.ok(await main.getByRole('button', { name: 'Azzera filtri (0 nascosti)' }).isDisabled());
  // The skip link goes to the content.
  await page.getByRole('link', { name: 'Vai al contenuto' }).press('Enter');
  await page.waitForFunction(() => document.activeElement?.tagName === 'MAIN');
  // The views are places of the bar.
  const view = name => page.getByRole('button', { name: new RegExp(`^${name}`) });
  assert.equal(await view('Logica').getAttribute('aria-current'), 'page');
  await view('Fisica').click();
  await page.getByRole('main', { name: 'Mappa fisica' }).waitFor();
  assert.equal(await view('Fisica').getAttribute('aria-current'), 'page');
  assert.equal(await view('Logica').getAttribute('aria-current'), null);
  await choose('Vista logica');
  await page.getByRole('main', { name: 'Mappa logica' }).waitFor();
  await view('Logica').press('ArrowRight');  // by keyboard: the arrows go from a view to the next, Enter goes to it
  await page.waitForFunction(() => document.activeElement?.textContent === 'Fisica');
  await page.keyboard.press('Enter');
  await page.getByRole('main', { name: 'Mappa fisica' }).waitFor();
  await page.keyboard.press('ArrowLeft');
  await page.waitForFunction(() => document.activeElement?.textContent === 'Logica');
  await page.keyboard.press('Enter');
  await page.getByRole('main', { name: 'Mappa logica' }).waitFor();
  // The palette, by its key and by its button; its Escape closes it and nothing else.
  await page.getByRole('button', { name: 'Comandi', exact: true }).click();
  await palette.waitFor();
  await page.keyboard.press('Escape');
  await palette.waitFor({ state: 'detached' });
  // What the project is, in the inspector: opened by its button or its command, closed by Escape or by its button.
  assert.equal(await info.count(), 0);
  await infoButton.click();
  await info.waitFor();
  await main.getByRole('button', { name: 'Informazioni sul progetto', pressed: true }).waitFor();
  assert.match(await info.innerText(), /shop[\s\S]*Collegamenti di dati[\s\S]*Tecnologie[\s\S]*React[\s\S]*framework[\s\S]*web\/checkout\.tsx/);
  assert.ok(await selectable(info.getByText('web/checkout.tsx', { exact: true })));
  assert.equal(await info.getByRole('list', { name: 'File di React' }).getByRole('listitem').count(), 8);
  await info.getByRole('button', { name: 'Altri 2 file' }).click();
  await info.getByRole('list', { name: 'Altri 2 file' }).getByText('web/part8.tsx').waitFor();
  await page.keyboard.press('Control+k');
  await palette.waitFor();
  await page.keyboard.press('Escape');
  await palette.waitFor({ state: 'detached' });
  assert.ok(await info.isVisible());  // the palette took that Escape
  await page.keyboard.press('Escape');
  await info.waitFor({ state: 'hidden' });
  await choose('Informazioni sul progetto');
  await info.waitFor();
  await closeIn(info);
  await info.waitFor({ state: 'hidden' });
  await infoButton.click();
  await info.waitFor();
  await infoButton.click();  // pressed again, it closes
  await info.waitFor({ state: 'hidden' });
  // The sidebar's places: the whole map, or a flow, whose steps are in the inspector.
  const current = locator => locator.getAttribute('aria-current');
  assert.equal(await current(whole), 'page');
  const pay = row(/^pay\b.*\b8\s*passi$/);
  await pay.click();
  await flowPanel.getByRole('heading', { name: 'pay', exact: true }).waitFor();
  assert.deepEqual([await current(pay), await pay.getAttribute('aria-pressed'), await current(whole)], ['page', null, null]);
  const steps = flowPanel.getByRole('list', { name: 'Passi del flusso', exact: true }).getByRole('listitem');
  assert.equal(await steps.count(), 8);
  assert.match(await steps.first().innerText(), /1\. pay chiama apiPost[\s\S]*web\/checkout\.tsx:12 · diretto/);
  assert.ok(await selectable(steps.first().getByText('web/checkout.tsx:12', { exact: false })));
  await page.keyboard.press('Escape');  // closing leaves the flow chosen, and its place shows its steps again
  await flowPanel.waitFor({ state: 'hidden' });
  assert.equal(await current(pay), 'page');
  await pay.click();
  await flowPanel.waitFor();
  await row(/^nightlyReconcile\b.*\bincompleto\s*2\s*passi$/).click();
  await flowPanel.getByRole('heading', { name: 'nightlyReconcile', exact: true }).waitFor();
  await flowPanel.getByRole('list', { name: 'Dove si ferma la prova' }).getByText('call to refund is unresolved').waitFor();
  const long = row(/^Flusso lungo\b.*\b43\s*passi$/);
  await long.click();
  await flowPanel.getByRole('heading', { name: 'Flusso lungo', exact: true }).waitFor();
  assert.equal(await steps.count(), 40);  // the others are behind a row that says how many, and go on counting
  await flowPanel.getByRole('button', { name: 'Altri 3 passi' }).click();
  const others = flowPanel.getByRole('list', { name: 'Altri 3 passi' }).getByRole('listitem');
  await others.first().waitFor();
  assert.equal(await others.count(), 3);
  assert.match(await others.first().innerText(), /^41\. /);
  // The sidebar's things: an element chosen is in the inspector, over the flow.
  await row(/^web/).click();
  await details.getByRole('heading', { name: 'web', exact: true }).waitFor();
  await flowPanel.waitFor({ state: 'hidden' });
  assert.equal(await current(row(/^web/)), 'true');
  assert.equal(await elements.locator('[aria-current="true"]').count(), 1);
  assert.equal(await current(long), 'page');
  const listed = name => details.getByRole('list', { name, exact: true }).getByRole('listitem');
  assert.match(await details.innerText(), /Schermate del negozio[\s\S]*Tipo\s+componente\s+Posizione\s+interno[\s\S]*React[\s\S]*framework/);
  assert.equal(await listed('Collegamenti visibili').count(), 4);
  assert.ok((await listed('Collegamenti visibili').allInnerTexts()).includes('→ API gateway usa'));
  assert.equal(await listed('Evidenze').count(), 8);
  await details.getByRole('button', { name: '1 altra evidenza' }).click();
  await listed('1 altra evidenza').getByText('web/part8.tsx:9').waitFor();
  assert.match(await details.innerText(), /Lacune[\s\S]*shared_member/);
  // One live region, with the name alone, which stays while what is chosen changes.
  await page.evaluate(() => { window.liveRegion = document.querySelector('aside[aria-label="Dettaglio"] [aria-live="polite"]'); });
  await row(/^server/).click();
  await details.getByRole('heading', { name: 'server', exact: true }).waitFor();
  assert.deepEqual(await page.evaluate(() => [window.liveRegion.isConnected, window.liveRegion.textContent]), [true, 'server']);
  assert.equal(await details.locator('[aria-live]').count(), 1);
  assert.equal(await listed('Collegamenti visibili').count(), 4);  // the view's relations: not the data links, nor a flow's steps
  assert.ok(!(await listed('Collegamenti visibili').allInnerTexts()).some(text => text.includes('db/orders')));
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
  assert.equal(await flowPanel.count(), 0);
  assert.equal(await current(long), 'page');
  await whole.click();
  await page.waitForFunction(() => document.querySelector('nav[aria-label="Mappa"] [aria-current="page"]').textContent === 'Tutta la mappa');
  // A group is entered by the inspector's action, by its row's own control, or by a double press; «Su» goes back.
  const still = async () => [(await view('Logica').boundingBox()).x, (await up.boundingBox()).x, (await infoButton.boundingBox()).x];
  const before = await still();
  await row(/^web/).click();
  await details.getByRole('button', { name: 'Entra in web', exact: true }).click();
  await place('Sistema / web').waitFor();
  await details.waitFor({ state: 'hidden' });
  assert.deepEqual(await still(), before);  // nothing moves with the place
  await row('Entra in checkout.tsx').click();
  await place('Sistema / web / checkout.tsx').waitFor();
  await up.click();
  await place('Sistema / web').waitFor();
  await details.getByRole('heading', { name: 'checkout.tsx', exact: true }).waitFor();  // what was left is chosen
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await row(/^server/).dblclick();
  await place('Sistema / server').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  // The project's information, left for an element, does not come back with the group entered.
  await infoButton.click();
  await info.waitFor();
  await row(/^web/).click();
  await details.waitFor();
  await details.getByRole('button', { name: 'Entra in web', exact: true }).click();
  await details.waitFor({ state: 'hidden' });
  assert.equal(await info.count(), 0);
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  // Ctrl+F is the search of the view; a search that leaves nothing says so, with the way back.
  await page.keyboard.press('Control+f');
  assert.ok(await focused(search));
  await search.fill('zzzz');
  await main.getByText('Nessun elemento visibile.').waitFor();
  assert.ok(await main.getByRole('button', { name: 'Azzera filtri (8 nascosti)' }).isEnabled());
  await main.getByRole('button', { name: 'Azzera filtri', exact: true }).click();
  await main.getByText('Nessun elemento visibile.').waitFor({ state: 'detached' });
  assert.equal(await search.inputValue(), '');
  // The type: its choices are those of the view, whatever the search hides, and the chosen one stays said.
  const kind = main.getByRole('combobox', { name: 'Tipo di entità' });
  await kind.click();
  await page.getByRole('option', { name: 'componente', exact: true }).click();
  await place('Sistema').filter({ hasText: '2 nodi' }).waitFor();
  await search.fill('zzzz');
  await main.getByText('Nessun elemento visibile.').waitFor();
  assert.match(await kind.innerText(), /componente/);
  await kind.click();
  await page.getByRole('option', { name: 'dato', exact: true }).waitFor();
  assert.deepEqual((await page.getByRole('option').allInnerTexts()).map(text => text.trim()), ['Tutti i tipi', 'componente', 'esterno', 'dato']);
  await page.keyboard.press('Escape');
  await page.getByRole('option').first().waitFor({ state: 'hidden' });
  await main.getByRole('button', { name: /Azzera filtri \(\d+ nascosti\)/ }).click();
  await main.getByRole('button', { name: 'Azzera filtri (0 nascosti)' }).waitFor();
  assert.match(await kind.innerText(), /Tutti i tipi/);
  // F6 and Shift+F6 go from a region to the next.
  await nav.getByRole('button').first().focus();
  await page.keyboard.press('F6');
  assert.ok(await inMain());
  await page.keyboard.press('Shift+F6');
  assert.ok(await nav.evaluate(el => el.closest('aside').contains(document.activeElement)));
  // The rail is the person's choice, and from 620 to 850 the frame's.
  await page.getByRole('button', { name: 'Riduci la barra laterale' }).click();
  await page.getByRole('button', { name: 'Espandi la barra laterale' }).waitFor();
  assert.ok((await nav.boundingBox()).width < 100);
  assert.deepEqual([await whole.isVisible(), await elements.count()], [true, 0]);  // the places, and no things
  await page.getByRole('button', { name: 'Espandi la barra laterale' }).click();
  await page.waitForFunction(() => document.querySelector('nav[aria-label="Mappa"]').getBoundingClientRect().width > 200);
  // Light, dark and the system's theme, kept for both pages.
  await choose('Tema come il sistema');
  await page.emulateMedia({ colorScheme: 'light' });
  await schemeIs(page, 'light');
  assert.equal(await kept(), 'system');
  await page.emulateMedia({ colorScheme: 'dark' });
  await schemeIs(page, 'dark');

  await page.setViewportSize({ width: 700, height: 820 });  // the sidebar is the rail: the places as icons, with their names, and no things
  await page.waitForFunction(() => document.querySelector('nav[aria-label="Mappa"]').getBoundingClientRect().width < 100);
  assert.deepEqual([await whole.isVisible(), await row(/^pay/).isVisible(), await elements.count()], [true, true, 0]);
  assert.ok(await fits());
  await page.setViewportSize({ width: 900, height: 820 });  // the inspector covers the end of the content, not modal
  await infoButton.click();
  const overlay = page.getByRole('dialog', { name: 'Informazioni sul progetto' });
  await overlay.waitFor();
  await closeIn(overlay);
  await overlay.waitFor({ state: 'detached' });
  await page.setViewportSize({ width: 390, height: 820 });  // the sidebar is a drawer, and the views are at the foot
  const drawer = page.getByRole('dialog', { name: 'Mappa' });
  await page.getByRole('button', { name: 'Apri il menu' }).click();
  await drawer.getByRole('button', { name: /^web/ }).waitFor();
  await page.keyboard.press('Escape');
  await drawer.waitFor({ state: 'detached' });
  await page.getByRole('button', { name: 'Apri il menu' }).click();  // an element chosen there closes it and shows its details
  await drawer.getByRole('button', { name: /^web/ }).click();
  await drawer.waitFor({ state: 'detached' });
  const sheet = page.getByRole('dialog', { name: 'Dettaglio' });
  await sheet.waitFor();
  await closeIn(sheet);
  await sheet.waitFor({ state: 'detached' });
  const footViews = page.getByRole('toolbar', { name: 'Viste in basso' });
  assert.equal(await view('Logica').count(), 1);
  await footViews.getByRole('button', { name: 'Fisica' }).click();
  await page.getByRole('main', { name: 'Mappa fisica' }).waitFor();
  await footViews.getByRole('button', { name: 'Logica' }).click();
  await page.getByRole('main', { name: 'Mappa logica' }).waitFor();
  assert.ok(await fits());
  await page.setViewportSize({ width: 1280, height: 850 });

  await context.route('**/api/runs', route => route.fulfill({ json: { runs: [] } }));
  await context.route('**/api/requests', route => route.fulfill({ json: { requests: [] } }));
  await context.route('**/api/findings', route => route.fulfill({ json: { findings: [], gaps: [] } }));
  await page.reload();
  await main.getByText('Creane uno qui sotto, o avvia una mappa nella sessione.').waitFor();
  await line('Nessun run').waitFor();
  await nav.getByText('Nessuna mappa: non ci sono run.').waitFor();
  await page.keyboard.press('Control+f');  // no map, no search
  await page.getByText('Questa vista non ha una ricerca.').waitFor();
  await context.route('**/api/runs', route => route.fulfill({ json: { runs: [{ run_id: 'prima', readable: true }, { run_id: 'rotto', readable: false }, { run_id: 'demo', readable: true }] } }));
  await context.route('**/api/events?*', route => route.fulfill({ json: { events: [{ cursor: 1, timestamp: '10:00', event: 'phase_completed', message: 'fatto', phase: 2 }], next_cursor: 1, has_more: false } }));
  mode.exportBroken = true;  // a run in progress has no readable export yet: its live event line shows all the same
  await page.reload();
  await main.getByRole('alert').waitFor();
  await line('10:00 · phase_completed · fase 2 · fatto').waitFor();
  mode.exportBroken = false;
  await context.route('**/api/findings', route => route.fulfill({ json: { findings: [{ file: 'web/checkout.tsx', line: 12, severity: 'High', title: 'Premessa', request: 1 }], gaps: ['lacuna della sessione'] } }));
  await page.reload();
  await line('10:00 · phase_completed · fase 2 · fatto').waitFor();
  const runPicker = main.getByRole('combobox', { name: 'Run' });  // the last readable run is the one shown
  assert.match(await runPicker.innerText(), /Run demo/);
  await runPicker.click();
  await page.getByRole('option', { name: 'Run prima', exact: true }).waitFor();
  assert.equal(await page.getByRole('option').count(), 2);
  const asked = page.waitForRequest(request => request.url().includes('/data/visual.json?run=prima'));
  await page.getByRole('option', { name: 'Run prima', exact: true }).click();
  await asked;
  assert.match(await runPicker.innerText(), /Run prima/);
  await line('shop · run fixture').waitFor();

  // ticket 17/18: the contract of what they port, in Imago's selectors: to restore by role and name, then delete from here.
  // ticket 17, the canvas and the flows on it
  // const canvas = page.getByRole('region', { name: 'Naviga il grafo' });
  // const node = canvas.locator('.im-graph-node').first();
  // await node.waitFor({ timeout: 15000 });
  // const name = await node.getAttribute('title');
  // await node.click();
  // await page.waitForFunction(label => document.querySelector('.im-inspector h2')?.textContent === label, name, { timeout: 5000 });
  // await node.focus();
  // await page.keyboard.press('Escape');
  // await inspectorBox.waitFor({ state: 'hidden' });
  // await node.click();
  // await inspectorBox.waitFor();
  // const flow = page.locator('.im-sidebar .im-row').first();
  // await flow.click();
  // await page.locator('.im-canvas-message').waitFor({ state: 'hidden' });
  // await canvas.locator('.im-graph-node').first().waitFor();
  // assert.ok((await canvas.boundingBox()).height >= 320);
  // await emptyMap.getByRole('button', { name: 'Azzera filtri' }).click();
  // await canvas.locator('.im-graph-node').first().waitFor();
  // (on the physical view) await canvas.locator('.im-graph-node').first().waitFor();
  // (at 900) await node.click(); await inspectorBox.waitFor();
  // (at 390) assert.ok((await canvas.boundingBox()).height >= 200);
  // ticket 18, the session, the findings and the other export
  // const file = page.locator('.im-file-selector');
  // await file.setInputFiles({ name: 'shop.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(envelope)) });
  // (with no runs) await page.getByLabel('Nome del run').waitFor();
  // const disclosure = page.locator('summary', { hasText: 'Sessione e review' });
  // await disclosure.press('Enter');
  // await page.getByRole('button', { name: 'Invia' }).waitFor();
  // assert.ok(await page.getByLabel('Perimetro').isVisible());
  // assert.ok(await page.locator('.im-btn--primary:visible').count() <= 1);  // "Entra in ..." is the page's only primary
  // for (const name of ['Invia', 'Crea il run']) assert.ok(!(await page.getByRole('button', { name }).getAttribute('class')).includes('im-btn--primary'));
  // await page.getByText('lacuna della sessione').waitFor();  // the session's gaps are a note
  // await page.getByRole('button', { name: /High/ }).click();  // a finding selects its file
  // assert.equal(await page.locator('.im-inspector h2').innerText(), 'checkout.tsx');
  // await page.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  // await disclosure.press('Enter');
  // await page.getByRole('button', { name: 'Invia' }).waitFor({ state: 'detached' });
  // end of ticket 17/18

  // The theme the person picks on one page is followed live by the other one (the storage event), on Sigrid or on Imago.
  await choose('Tema chiaro');
  await schemeIs(page, 'light');
  const tab = await context.newPage(), app = await context.newPage();
  await tab.goto('http://daodan.test/');
  await schemeIs(tab, 'light');
  await app.goto('http://daodan.test/app/?token=test');
  await app.waitForFunction(() => document.documentElement.dataset.imTheme === 'light');
  await page.bringToFront();
  await choose('Tema scuro');
  await schemeIs(tab, 'dark');
  await app.waitForFunction(() => document.documentElement.dataset.imTheme === 'dark');
  await app.bringToFront();
  await app.keyboard.press('Control+k');
  await app.getByRole('dialog', { name: 'Cerca un comando' }).getByRole('option', { name: 'Tema chiaro' }).click();
  await schemeIs(page, 'light');
  await tab.close();
  await app.close();
  assert.deepEqual(errors, []);
  console.log('Passed the App on Imago (navigation, tree, dialog, pipeline, graph groups) and the map on Sigrid (frame, palette, places and things, details, filters, runs, theme).');
} finally { await browser.close(); }
