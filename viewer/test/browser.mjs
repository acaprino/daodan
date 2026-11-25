import assert from 'node:assert/strict';
import { mkdir, readFile, rm } from 'node:fs/promises';
import { chromium } from 'playwright';

const assets = new URL('../../daodan/assets/', import.meta.url);
const envelope = JSON.parse(await readFile(new URL('./fixture.json', import.meta.url)));
// What the fixture lacks for the details: evidence as the server writes it, and lists longer than what is in sight at first.
const parts = Array.from({ length: 9 }, (_, n) => `web/part${n}.tsx`);
envelope.technologies = [{ id: 'react', name: 'React', type: 'framework', category: 'framework', mark: 'react', paths: ['web/checkout.tsx', ...parts] }];
// The logos the server has, and one it has not.
for (const [ref, mark] of [['external:card payment provider', 'stripe'], ['external:api gateway', 'gone']]) envelope.entities.find(entity => entity.ref === ref).mark = mark;
const LOGO = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>';
const marksAsked = [];
Object.assign(envelope.entities.find(entity => entity.ref === 'component:web'), { technologies: ['react'], evidence: parts.map((path, n) => ({ path, line: n + 1 })) });
envelope.flows.push({ ...envelope.flows[1], ref: 'flow:lungo', label: 'Flusso lungo', complete: true, gaps: [], steps: Array(43).fill(envelope.flows[1].steps[0]) });
let pathsClassified = false;
// What the fixture server does next, so that a test can make a route fail or wait.
const engineRequests = [], askRequests = [], checkRequests = [], selectRequests = [], markRequests = [];
const mode = { graphStatus: 200, premapStatus: 200, premapDelay: 0, linkStatus: 200, checkDelay: 0, selectRefused: '', exportBroken: false, exportDelay: 0, exportBusy: 0, layoutLost: false, pathsBroken: false, marks: false };
const run = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'demo' };
const groups = ['Client', 'Server'].map(name => ({
  id: name, name, mark: null, kind: 'directory', files: Array.from({ length: name === 'Server' ? 6 : 1 }, (_, n) => `${name}/file${n}.ts`), location: 'internal', status: 'confirmed', group: null, evidence: [],
  ...(name === 'Client' && { projects: [{ mark: 'react', name: 'React', category: 'framework', evidence: [{ path: 'package.json', line: 12 }] }], other_dependencies: 3 }),
}));
const graph = { grouping: 'directories', nodes: groups, open: [], edges: ['confirmed', 'observed', 'sampled'].map(status => ({
    source: 'Client', target: 'Server', counts: { calls: 1 }, status,
    evidence: status === 'observed' ? [{ path: 'Client/file0.ts', line: 3, target: 'Server/file1.ts', kind: 'calls', key: 'save' }] : [],
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
  const respond = async route => {
    const url = new URL(route.request().url()), path = url.pathname;
    if (path === '/api/app/paths') {
      if (mode.pathsBroken) return route.fulfill({ status: 500, json: { error: 'percorsi non letti' } });
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
    if (path === '/api/app/mark') {
      markRequests.push(url.search);
      return route.fulfill(mode.marks ? { contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>' }
        : { status: 404, json: { error: 'nessun logo' } });
    }
    if (path === '/api/app/symbols') return route.fulfill({ json: { file: 'child', symbols: [{ id: 'child::save', name: 'save', lines: [1, 5] }], calls: [] } });
    if (path === '/api/app/ask') {
      askRequests.push(1);
      return route.fulfill({ json: {} });
    }
    if (path === '/api/app/answer') return route.fulfill({ json: { events: [{ kind: 'tool', name: 'cerca', arguments: 'token' }], next: 1, state: 'done', text: 'Lo firma auth.ts', cause: null } });
    if (path === '/api/app/link') return route.fulfill(mode.linkStatus === 200 ? { json: {} } : { status: mode.linkStatus, json: { error: 'collegamento non riuscito' } });
    if (path === '/api/app/check') {
      checkRequests.push(route.request().postDataJSON());
      await new Promise(resolve => setTimeout(resolve, mode.checkDelay));
      return route.fulfill({ json: { state: 'accessible', repository: { owner: 'demo', name: 'shop' }, default: 'main',
        branches: [{ name: 'main', commit: '1'.repeat(40) }, { name: 'dev', commit: '2'.repeat(40) }] } });
    }
    if (path === '/api/app/select') {
      selectRequests.push(route.request().postDataJSON());
      return route.fulfill(mode.selectRefused ? { status: 400, json: { error: mode.selectRefused } }
        : { json: { context: null, job: { state: 'preparing', step: 'checkout', detail: 'dev' }, engine: { engine: 'claude', engines: ['claude'] } } });
    }
    if (path === '/api/app/graph') {
      if (mode.graphStatus !== 200) return route.fulfill({ status: mode.graphStatus, json: { error: 'grafo non letto' } });
      const open = JSON.parse(url.searchParams.get('open') || '[]');
      return route.fulfill({ json: open.length ? { ...graph, open: [{ ...groups[0], parent: null }],
        nodes: [{ ...groups[0], id: 'child', name: 'main.ts', kind: 'file', files: [], group: 'Client' }, groups[1]] } : graph });
    }
    if (path === '/api/app/premap') {
      await new Promise(resolve => setTimeout(resolve, mode.premapDelay));
      if (mode.premapStatus !== 200) return route.fulfill({ status: mode.premapStatus, json: { error: 'snapshot non leggibile' } });
      return route.fulfill({ json: {
      files: ['README.md', 'src/lib/util.ts', 'src/main.ts'], languages: [{ name: 'TypeScript', files: 2 }],
      technologies: [{ name: 'React', category: 'framework', state: 'recognized', source: 'package.json:12', mark: 'react' },
        { name: 'node', category: 'toolchain', state: 'declared', version: '24', source: '.nvmrc' }],
      units: [{ id: 'web', name: 'web', kind: 'npm', root: '.', manifest: 'package.json', status: 'confirmed', parent: null,
        dependencies: [{ name: 'left-pad', scope: 'runtime', state: 'declared', source: 'package.json', version: '^1.3.0', direct: true },
          { name: 'tiny', scope: 'npm', state: 'resolved', source: 'package-lock.json', resolved_version: '2.0.1', direct: false }] },
      { id: 'api', name: 'api', kind: 'npm', root: 'server', manifest: null, status: 'inferred', parent: 'web', dependencies: [] }],
      } });
    }
    if (path === '/data/visual.json') {
      await new Promise(resolve => setTimeout(resolve, mode.exportDelay));
      if (mode.exportBusy > 0) {
        mode.exportBusy -= 1;
        return route.fulfill({ status: 503, json: { error: 'project lock is held by another helper' } });
      }
      return route.fulfill(mode.exportBroken ? { body: 'not json', contentType: 'text/plain' } : { json: envelope });
    }
    if (path === '/api/mark') {
      marksAsked.push(url.search);
      return route.fulfill(['react', 'stripe'].includes(url.searchParams.get('id')) ? { body: LOGO, contentType: 'image/svg+xml' } : { status: 404, json: {} });
    }
    if (path.startsWith('/api/')) return route.fulfill({ status: 404, json: {} });
    if (mode.layoutLost && path.includes('layout.worker')) return route.fulfill({ body: '', contentType: 'text/javascript' });  // it never answers
    const app = path.startsWith('/app/');
    const part = path.slice(app ? 5 : 1) || 'index.html';
    const mime = { html: 'text/html', css: 'text/css', js: 'text/javascript' }[part.split('.').at(-1)];
    await route.fulfill({ body: await readFile(new URL((app ? 'app/' : 'viewer/') + part, assets)), contentType: mime });
  };
  await context.route('http://daodan.test/**', respond);
  const stream = state => {
    window.EventSource = class extends EventTarget {
      constructor() {
        super();
        const send = (name, frame) => this.dispatchEvent(new MessageEvent(name, { data: JSON.stringify(frame) }));
        const publish = frame => send('app', frame);
        window.setMapState = mapped => publish({ ...state, mapped });
        window.setServerState = patch => publish({ ...state, ...patch });
        window.failServer = error => send('failure', { error });
        window.sendEvents = events => send('update', { run_events: { run_id: 'demo', next_cursor: 0, events: [], pipeline: { next_cursor: 0, events } }, pulse: { next_cursor: 0 } });
        setTimeout(() => publish(state), 0);
      }
      close() {}
    };
  };
  const fresh = { context: run, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: { engine: 'claude', engines: ['claude'] }, links: { state: 'idle' } };
  await page.addInitScript(stream, fresh);
  await page.goto('http://daodan.test/app/?token=test');
  // What a person meets, by role, name and words, on the two pages. The scheme is what `applyTheme` writes on the root.
  const selectable = locator => locator.evaluate(el => getComputedStyle(el).userSelect !== 'none');
  const palette = page.getByRole('dialog', { name: 'Cerca un comando' });
  const choose = async command => {
    await page.keyboard.press('Control+k');
    await palette.getByRole('option', { name: command }).click();
  };
  const schemeIs = (where, wanted) => where.waitForFunction(value => document.documentElement.dataset.scheme === value, wanted);
  const kept = () => page.evaluate(() => localStorage.getItem('daodan.theme'));
  const fits = () => page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth).then(() => true, () => false);  // once the frame has the width
  const focused = locator => locator.evaluate(el => el === document.activeElement);
  const main = page.getByRole('main');
  const line = text => page.getByRole('status').filter({ hasText: text });  // the status row, and what it says
  const inMain = () => page.evaluate(() => !!document.activeElement?.closest('main'));
  const onContent = () => page.waitForFunction(() => document.activeElement?.tagName === 'MAIN');  // the focus is on the content itself
  const busyNow = button => button.and(page.locator('[aria-busy="true"]')).waitFor();

  {  // The App.
    const bar = page.getByRole('toolbar', { name: 'Daodan', exact: true });
    const tab = name => bar.getByRole('button', { name: new RegExp(`^${name}`) });
    const screen = name => page.getByRole('main', { name, exact: true }).waitFor();
    const panel = name => main.getByRole('region', { name, exact: true });
    const path = main.getByRole('list', { name: 'Percorso di analisi', exact: true });
    const stage = name => path.getByRole('button', { name: new RegExp(`^${name}`) });
    const stageSays = (name, text) => stage(name).filter({ hasText: text }).waitFor();
    const wrong = text => main.getByRole('alert').filter({ hasText: text });  // what a field, or the server, says is wrong
    const serve = patch => page.evaluate(state => window.setServerState(state), patch);
    await stage('Repository').waitFor();
    assert.equal(await page.title(), 'Daodan · Analisi');
    // Light, dark and the system's theme are commands, and the choice is kept.
    await page.keyboard.press('Control+k');
    await palette.getByRole('option', { name: 'Tema scuro' }).waitFor();
    await page.keyboard.press('Escape');
    await palette.waitFor({ state: 'detached' });
    await choose('Tema scuro');
    await schemeIs(page, 'dark');
    assert.equal(await kept(), 'dark');
    await page.reload();
    await stage('Repository').waitFor();
    await schemeIs(page, 'dark');
    await page.getByRole('button', { name: 'Comandi', exact: true }).click();
    await palette.waitFor();
    await page.keyboard.press('Escape');
    await palette.waitFor({ state: 'detached' });
    // The frame: the screens in the bar, no sidebar, the context in the status row, the service and the keys at the foot.
    assert.deepEqual((await bar.getByRole('button').allInnerTexts()).slice(0, 3), ['Analisi', 'Grafo', 'Motore e domande']);
    assert.equal(await tab('Analisi').getAttribute('aria-current'), 'page');
    await page.evaluate(() => document.fonts.ready);
    const beside = (await tab('Motore').boundingBox()).x;  // before there is a graph to count
    assert.equal(await page.getByRole('navigation').count(), 0);
    await line('Contesto pronto').waitFor();
    const where = line('Pipeline completata').getByText(`demo/shop · main · ${'1'.repeat(12)} · run demo`, { exact: true });
    await where.waitFor();
    assert.ok(await selectable(where));
    const foot = page.getByRole('contentinfo');
    assert.match(await foot.innerText(), /App locale: il codice resta sul tuo disco · Motore: claude/);
    const keys = () => foot.getByRole('list', { name: 'Tasti' }).innerText();  // Ctrl+K is on its button
    assert.match(await keys(), /F6\s*Area successiva/);
    assert.doesNotMatch(await keys(), /Ctrl\s*[KF]/);  // this stage has no search
    // The stages say how they are, and one that cannot be opened says why.
    assert.equal(await stage('Repository').getAttribute('aria-current'), 'true');
    for (const name of ['Repository', 'Pre-mappa', 'Analisi', 'Sintesi e grafo']) await stageSays(name, 'fatta');
    await serve({ context: null, job: { state: 'idle' } });
    await line('Nessuna repository').waitFor();
    await stageSays('Repository', 'da fare');
    const why = text => path.getByText(text, { exact: true });
    const atFullStrength = locator => locator.evaluate(el => {
      for (let at = el; at; at = at.parentElement) if (getComputedStyle(at).opacity !== '1') return false;
      return true;
    });
    const first = why('Scegli prima una repository e un branch.');
    await first.first().waitFor();
    assert.equal(await first.count(), 3);  // one under each row that cannot be opened
    for (const reason of await first.all()) assert.ok(await atFullStrength(reason));
    for (const name of ['Pre-mappa', 'Analisi', 'Sintesi']) assert.ok(await stage(name).isDisabled());
    await main.getByText('Nessuna repository selezionata sul server.').waitFor();
    await serve({ run: { pass: { state: 'running' } } });
    await stageSays('Analisi', 'in corso');
    await why('La sintesi è pronta quando la pipeline è conclusa.').waitFor();
    assert.ok(await stage('Sintesi').isDisabled());
    await line('Analisi in corso').filter({ hasText: '0%' }).waitFor();
    assert.equal(await line('Analisi in corso').getByText('0%', { exact: true }).getAttribute('aria-hidden'), 'true');  // the row is announced: not at every percent
    await page.getByRole('progressbar', { name: 'Passi completati della pipeline' }).waitFor();
    await serve({ run: { pass: { state: 'failed' } } });
    await stageSays('Analisi', 'non riuscita');
    await serve({});
    await stageSays('Analisi', 'fatta');
    // The repository: its address is checked, then a branch is chosen; what cannot be done now says why.
    const address = main.getByRole('textbox', { name: 'URL GitHub' });
    const verify = main.getByRole('button', { name: 'Verifica accesso', exact: true });
    const branch = main.getByRole('combobox', { name: 'Branch da analizzare' });
    const prepare = page.getByRole('button', { name: 'Apri pre-mappa', exact: true });
    const unchecked = page.getByText('Verifica prima l’accesso alla repository.', { exact: true });
    await unchecked.waitFor();
    assert.deepEqual([await branch.isDisabled(), await prepare.isDisabled()], [true, true]);
    await verify.click();
    await wrong('Inserisci l’URL GitHub della repository.').waitFor();
    assert.ok(await focused(address));
    await address.fill('https://github.com/demo');
    await wrong('Inserisci l’URL').waitFor({ state: 'detached' });
    await address.press('Enter');
    await wrong('senza percorsi aggiuntivi').waitFor();
    assert.equal(checkRequests.length, 0);
    await address.fill('https://github.com/demo/shop');
    mode.checkDelay = 1000;
    await verify.click();
    await busyNow(verify);
    assert.equal((await verify.innerText()).trim(), 'Verifica accesso');
    await page.getByText('Verifica in corso.', { exact: true }).waitFor();
    await address.press('Enter');  // a check in course is not asked again
    await page.getByText('demo/shop: 2 branch letti da GitHub.', { exact: true }).waitFor();
    assert.deepEqual(checkRequests, [{ url: 'https://github.com/demo/shop' }]);
    mode.checkDelay = 0;
    assert.equal(await unchecked.count(), 0);
    assert.match(await branch.innerText(), /main · 1{12}/);
    await branch.click();
    await page.getByRole('option', { name: /^dev/ }).click();
    assert.match(await branch.innerText(), /dev · 2{12}/);
    mode.selectRefused = 'lavoro in corso';
    await prepare.click();
    await wrong('Selezione non riuscita.').filter({ hasText: 'lavoro in corso' }).waitFor();
    mode.selectRefused = '';
    await prepare.click();
    await line('Preparazione in corso').waitFor();
    assert.deepEqual(selectRequests.at(-1), { url: 'https://github.com/demo/shop', branch: 'dev' });
    await busyNow(prepare);
    await main.getByText('Preparazione in corso: Checkout del branch · dev.', { exact: true }).waitFor();
    await main.getByRole('progressbar', { name: 'Preparazione in corso' }).waitFor();
    await stageSays('Repository', 'in corso');
    assert.equal(await wrong('Selezione non riuscita.').count(), 0);
    await serve({ context: null, job: { state: 'failed', step: 'checkout', detail: 'branch non trovato' } });
    await wrong('Preparazione non riuscita (Checkout del branch).').filter({ hasText: 'branch non trovato' }).waitFor();
    await stageSays('Repository', 'non riuscita');
    await prepare.click();
    await line('Preparazione in corso').waitFor();
    mode.premapStatus = 500;
    await serve({});  // the context is ready: its pre-map opens, and its graph is read
    await page.getByText('Contesto pronto: demo/shop · main', { exact: true }).waitFor();
    await panel('Pre-mappa').waitFor();
    assert.equal(await stage('Pre-mappa').getAttribute('aria-current'), 'true');
    // A pre-map that cannot be read says why, with Riprova; while it is read the panel waits.
    const unread = wrong('Pre-mappa non disponibile.'), provenance = main.getByRole('button', { name: 'Provenienza', exact: true });
    await unread.filter({ hasText: 'snapshot non leggibile' }).waitFor();
    assert.ok(await selectable(unread.getByText('snapshot non leggibile')));
    await stageSays('Pre-mappa', 'non riuscita');
    assert.ok(await provenance.isDisabled());
    mode.premapStatus = 200;
    mode.premapDelay = 1000;
    await unread.getByRole('button', { name: 'Riprova' }).click();
    await main.getByRole('progressbar', { name: 'Lettura della pre-mappa…' }).waitFor();
    assert.equal(await unread.count(), 0);
    await onContent();
    const tree = main.getByRole('tree'), treeRow = name => tree.getByRole('treeitem', { name, exact: true });
    await tree.waitFor();
    assert.match(await keys(), /Ctrl\s*F[\s\S]*Cerca in questa vista[\s\S]*F6[\s\S]*Area successiva/);
    mode.premapDelay = 0;
    await stageSays('Pre-mappa', 'fatta');
    await foot.getByText(/ · 2 gruppi nel grafo$/).waitFor();
    assert.equal((await tab('Motore').boundingBox()).x, beside);  // a count that comes moves no tab
    // Choosing a stage shows it. The context in use, to read and copy, is with the repository.
    for (const name of ['Analisi', 'Sintesi', 'Repository']) {
      await stage(name).click();
      await panel(name).waitFor();
      assert.equal(await path.locator('[aria-current="true"]').count(), 1);
    }
    const facts = panel('Contesto attivo');
    for (const text of ['demo/shop', 'main', '1'.repeat(12), 'demo']) assert.ok(await selectable(facts.getByText(text, { exact: true })), text);
    await facts.getByRole('button', { name: 'Torna alla pre-mappa' }).click();
    await panel('Pre-mappa').waitFor();
    await onContent();  // what was pressed has gone with its stage
    await panel('Pre-mappa').getByText('3 file · 2 unità tecniche', { exact: true }).waitFor();
    // The pre-map: the context and what it holds, what it is made with and what it depends on, in words to read and copy.
    for (const text of ['demo/shop', '1'.repeat(12)]) assert.ok(await selectable(facts.getByText(text, { exact: true })), text);
    assert.match(await panel('Inventario').innerText(), /File nello snapshot\s*3[\s\S]*Linguaggi rilevati\s*1[\s\S]*Unità tecniche\s*2[\s\S]*Dipendenze per unità\s*2/);
    assert.match(await panel('Linguaggi').innerText(), /TypeScript\s*2 file/);
    assert.match(await panel('Tecnologie e framework').innerText(),
      /React\s*framework · Versione non registrata\s*package\.json:12[\s\S]*node\s*toolchain · 24\s*\.nvmrc/);
    for (const text of ['Inventario del checkout', 'File nello snapshot', '2 file', 'framework · Versione non registrata', '.nvmrc']) {
      assert.ok(await selectable(main.getByText(text, { exact: true }).first()), text);
    }
    // A technology asks for its logo, and keeps its icon where none comes; a toolchain has none to ask for.
    const technologies = panel('Tecnologie e framework').getByRole('term');
    await technologies.filter({ hasText: 'React' }).locator('img').waitFor({ state: 'detached' });
    assert.deepEqual(await Promise.all(['React', 'node'].map(text => technologies.filter({ hasText: text }).locator('svg').count())), [1, 1]);
    assert.deepEqual([...new Set(markRequests)], ['?id=react&token=test']);
    const dependencies = main.getByRole('table', { name: 'Dipendenze per unità' });
    const dependency = name => dependencies.getByRole('row').filter({ hasText: name });
    assert.match(await dependency('left-pad').innerText(), /left-pad\s+runtime\s+web\s+\^1\.3\.0\s+package\.json\s+—\s+Diretta/);
    assert.match(await dependency('tiny').innerText(), /tiny\s+npm\s+web\s+—\s+2\.0\.1\s+package-lock\.json\s+Transitiva/);
    assert.ok(await selectable(dependencies.getByText('left-pad', { exact: true })));
    // Its tree: the first level is open; a row chosen is in the details, and closing them leaves it.
    const details = name => page.getByRole('complementary', { name, exact: true });
    const chosen = name => tree.getByRole('treeitem', { name, exact: true, selected: true });
    const fileDetails = details('File dell’inventario'), unitDetails = details('Unità tecnica');
    const counted = text => main.getByText(text, { exact: true });
    await main.getByRole('tree', { name: 'Albero delle directory' }).waitFor();
    await counted('shop · 3 file').waitFor();
    for (const name of ['src', 'lib', 'main.ts', 'README.md']) await treeRow(name).waitFor();
    assert.equal(await treeRow('util.ts').count(), 0);
    assert.equal(await tree.getByRole('treeitem', { selected: true }).count(), 0);
    await treeRow('main.ts').press('Enter');
    await fileDetails.getByRole('heading', { name: 'main.ts', exact: true }).waitFor();
    assert.match(await fileDetails.innerText(), /Percorso\s*src\/main\.ts[\s\S]*Tipo\s*ts[\s\S]*snapshot del commit 1{12}/);
    assert.ok(await selectable(fileDetails.getByText('src/main.ts', { exact: true })));
    await chosen('main.ts').waitFor();
    await page.keyboard.press('Escape');
    await fileDetails.waitFor({ state: 'hidden' });
    await chosen('main.ts').waitFor({ state: 'detached' });
    await treeRow('main.ts').click();
    await fileDetails.waitFor();
    await treeRow('lib').click();  // a directory opens and closes, and the choice stays
    await treeRow('util.ts').waitFor();
    await chosen('main.ts').waitFor();
    // One live region, with the name alone, which stays while what is chosen changes. Closed from within, they give the focus back.
    await page.evaluate(() => { window.liveRegion = document.querySelector('aside [aria-live="polite"]'); });
    await treeRow('util.ts').click();
    await fileDetails.getByRole('heading', { name: 'util.ts', exact: true }).waitFor();
    assert.deepEqual(await page.evaluate(() => [window.liveRegion.isConnected, window.liveRegion.textContent]), [true, 'util.ts']);
    assert.equal(await fileDetails.locator('[aria-live]').count(), 1);
    await page.keyboard.press('F6');
    await page.waitForFunction(() => document.activeElement?.closest('aside'));
    await page.keyboard.press('Escape');
    await fileDetails.waitFor({ state: 'hidden' });
    assert.ok(await focused(treeRow('util.ts')));
    await treeRow('main.ts').click();
    await fileDetails.getByRole('heading', { name: 'main.ts', exact: true }).waitFor();
    // Another stage takes the details away, and they are there again with their stage.
    await stage('Repository').click();
    await fileDetails.waitFor({ state: 'hidden' });
    await stage('Pre-mappa').click();
    await fileDetails.waitFor();
    // Where it comes from takes the place of the choice; Escape closes it, and the focus stays on its button.
    await provenance.click();
    const origin = details('Provenienza della pre-mappa');
    await origin.waitFor();
    assert.match(await origin.innerText(), /Commit\s*1{40}[\s\S]*File nello snapshot\s*3[\s\S]*Unità tecniche\s*2[\s\S]*Dipendenze per unità\s*2/);
    await chosen('main.ts').waitFor({ state: 'detached' });
    await page.keyboard.press('Escape');
    await origin.waitFor({ state: 'hidden' });
    assert.ok(await focused(provenance));
    await provenance.click();
    await origin.getByRole('button', { name: 'Chiudi', exact: true }).click();
    await origin.waitFor({ state: 'hidden' });
    assert.ok(await focused(provenance));
    // Ctrl+F is the tree's search, on the whole path; it says how many it finds.
    const treeSearch = main.getByRole('searchbox', { name: 'Cerca nell’albero' });
    await page.keyboard.press('Control+f');
    assert.ok(await focused(treeSearch));
    await treeSearch.fill('SRC/main');
    await counted('shop · 1 file').waitFor();
    await treeRow('main.ts').waitFor();
    assert.equal(await treeRow('README.md').count(), 0);
    await treeSearch.fill('niente');
    await counted('shop · 0 file').waitFor();
    await main.getByText('Nessun risultato.', { exact: true }).waitFor();
    await main.getByRole('button', { name: 'Azzera ricerca', exact: true }).click();
    await counted('shop · 3 file').waitFor();
    assert.ok(await focused(treeSearch));
    // By directory or by unit: the arrows move, Enter chooses.
    const kindOfTree = main.getByRole('group', { name: 'Tipo di albero' });
    const directories = kindOfTree.getByRole('button', { name: /^Directory/ }), units = kindOfTree.getByRole('button', { name: /^Unità tecniche/ });
    const pressed = button => button.and(page.locator('[aria-pressed="true"]')).waitFor();
    await pressed(directories);
    await directories.press('ArrowRight');
    await units.and(page.locator(':focus')).waitFor();
    await units.press('Enter');
    await pressed(units);
    await main.getByRole('tree', { name: 'Albero delle unità tecniche' }).waitFor();
    await counted('Unità da manifest').waitFor();
    await treeRow('web').filter({ hasText: 'npm · Confermata' }).waitFor();
    await treeRow('package.json').waitFor();
    await treeSearch.fill('server');  // the root of a unit
    await treeRow('package.json').waitFor({ state: 'detached' });
    await treeRow('api').filter({ hasText: 'npm · Inferita' }).click();
    await unitDetails.getByRole('heading', { name: 'api', exact: true }).waitFor();
    assert.match(await unitDetails.innerText(), /Tipo\s*npm[\s\S]*Stato\s*Inferita[\s\S]*Radice\s*server[\s\S]*Dipendenze registrate\s*0/);
    // The mode, the search, the open branches and the choice are kept.
    await page.reload();
    await unitDetails.getByRole('heading', { name: 'api', exact: true }).waitFor();
    await chosen('api').waitFor();
    await pressed(units);
    assert.equal(await treeSearch.inputValue(), 'server');
    await unitDetails.getByRole('button', { name: 'Chiudi', exact: true }).click();
    await unitDetails.waitFor({ state: 'hidden' });
    await treeSearch.fill('');
    await directories.click();
    await treeRow('util.ts').waitFor();
    // What the pre-map leads to.
    await page.getByRole('button', { name: 'Segui l’analisi', exact: true }).click();
    await panel('Analisi').waitFor();
    await onContent();
    await stage('Pre-mappa').click();
    assert.ok(await focused(stage('Pre-mappa')));  // a row that stays keeps it
    await facts.getByRole('button', { name: 'Cambia repository o branch', exact: true }).click();
    await panel('Repository').waitFor();
    await facts.getByRole('button', { name: 'Torna alla pre-mappa' }).click();
    await panel('Pre-mappa').waitFor();
    // The screens are places: by a press, by the arrows and Enter, by their commands.
    await tab('Grafo').click();
    await screen('Grafo');
    assert.deepEqual([await tab('Grafo').getAttribute('aria-current'), await tab('Analisi').getAttribute('aria-current')], ['page', null]);
    assert.equal((await tab('Motore').boundingBox()).x, beside);  // nor does the choice of one
    assert.ok(await focused(tab('Grafo')));  // a tab keeps the focus; a command takes it to the content
    await tab('Grafo').press('ArrowLeft');
    await page.waitForFunction(() => document.activeElement?.textContent === 'Analisi');
    await page.keyboard.press('Enter');
    await screen('Analisi');
    for (const [command, name] of [['Vai a Motore e domande', 'Motore e domande'], ['Vai al Grafo', 'Grafo'], ['Vai ad Analisi', 'Analisi']]) {
      await choose(command);
      await screen(name);
      await palette.waitFor({ state: 'detached' });
      await onContent();
    }
    await panel('Pre-mappa').waitFor();  // the stage is where it was left
    // Ctrl+F on a stage with no search says so; F6 and Shift+F6 go from a region to the next; the skip link goes to the content.
    await stage('Repository').click();
    await page.keyboard.press('Control+f');
    await page.getByText('Questa vista non ha una ricerca.').waitFor();
    await tab('Analisi').focus();
    await page.keyboard.press('F6');
    assert.ok(await inMain());
    await page.keyboard.press('Shift+F6');
    assert.ok(await tab('Analisi').evaluate(el => el.closest('header').contains(document.activeElement)));
    await page.getByRole('link', { name: 'Vai al contenuto' }).press('Enter');
    await onContent();
    // A server that cannot be reached is said on every screen, until it answers.
    const unreachable = wrong('Server non raggiungibile.');
    await page.evaluate(() => window.failServer('il run non si legge'));
    await unreachable.waitFor();
    assert.match(await unreachable.innerText(), /Errore[\s\S]*Server non raggiungibile\.[\s\S]*il run non si legge/);
    assert.ok(await selectable(unreachable.getByText('il run non si legge')));
    await line('Server non raggiungibile').waitFor();
    assert.match(await foot.innerText(), /Server non raggiungibile · Motore: claude/);
    for (const name of ['Motore e domande', 'Grafo', 'Analisi']) {
      await tab(name).click();
      await screen(name);
      await unreachable.waitFor();
    }
    await serve({});
    await unreachable.waitFor({ state: 'detached' });
    await line('Pipeline completata').waitFor();
    // Where the person was looking is kept.
    await stage('Repository').click();
    await tab('Motore').click();
    await page.reload();
    await screen('Motore e domande');
    await tab('Analisi').click();
    await panel('Repository').waitFor();
    assert.equal(await address.inputValue(), 'https://github.com/demo/shop');
    // A narrow window: the screens are at the foot, and the stages or the one chosen, one at a time.
    await page.setViewportSize({ width: 700, height: 820 });
    const views = page.getByRole('toolbar', { name: 'Viste', exact: true });  // under the bar, then at the foot
    await views.getByRole('button', { name: /^Analisi/ }).waitFor();
    assert.deepEqual([await tab('Analisi').count(), await stage('Repository').isVisible(), await fits()], [0, true, true]);
    await page.setViewportSize({ width: 390, height: 820 });
    await views.getByRole('button', { name: /^Motore/ }).click();
    await screen('Motore e domande');
    assert.equal(await tab('Analisi').count(), 0);
    assert.ok(await fits());
    await views.getByRole('button', { name: /^Analisi/ }).click();
    await panel('Repository').waitFor();
    await path.waitFor({ state: 'hidden' });
    assert.ok(await fits());
    // What had the focus goes with its pane: the content takes it. Ctrl+F brings the pane of its field into sight.
    const toPath = main.getByRole('button', { name: 'Percorso', exact: true });
    await toPath.click();
    await path.waitFor();
    await onContent();
    await stage('Pre-mappa').click();
    await panel('Pre-mappa').waitFor();
    await path.waitFor({ state: 'hidden' });
    await onContent();
    assert.ok(await fits());
    await toPath.click();
    await path.waitFor();
    await page.keyboard.press('Control+f');
    await path.waitFor({ state: 'hidden' });
    assert.ok(await focused(treeSearch));
    await toPath.click();
    await stage('Repository').click();
    await panel('Repository').waitFor();
    await toPath.click();
    await page.keyboard.press('Control+f');  // a stage with no search says so, its list in sight or not
    await page.getByText('Questa vista non ha una ricerca.').waitFor();
    await stage('Pre-mappa').click();
    await page.setViewportSize({ width: 1280, height: 850 });
    await path.waitFor();
    await stage('Pre-mappa').focus();
    await page.setViewportSize({ width: 390, height: 820 });  // as a zoom does
    await path.waitFor({ state: 'hidden' });
    await onContent();
    await page.setViewportSize({ width: 1280, height: 850 });
    await path.waitFor();
  }

  // ticket 21: the run and the synthesis
  {
    const tab = name => page.getByRole('toolbar', { name: 'Daodan', exact: true }).getByRole('button', { name: new RegExp(`^${name}`) });
    const stage = name => main.getByRole('list', { name: 'Percorso di analisi', exact: true }).getByRole('button', { name: new RegExp(`^${name}`) });
    const screen = name => page.getByRole('main', { name, exact: true }).waitFor();
    const run = main.getByRole('region', { name: 'Analisi', exact: true }), synthesis = main.getByRole('region', { name: 'Sintesi', exact: true });
    const button = (where, name) => where.getByRole('button', { name, exact: true });
    const alertIn = (where, text) => where.getByRole('alert').filter({ hasText: text });
    const says = (where, text) => where.getByText(text, { exact: typeof text === 'string' }).waitFor();  // a note's title follows its tone's word: a pattern
    const detail = name => page.getByRole('complementary', { name, exact: true });
    const group = detail('Dettaglio del gruppo'), groupIs = name => group.getByRole('heading', { name, exact: true }).waitFor();
    const notices = page.getByRole('status', { name: 'Avvisi', exact: true });
    const serve = patch => page.evaluate(state => window.setServerState(state), patch);
    const map = mapped => page.evaluate(state => window.setMapState(state), mapped);
    const send = events => page.evaluate(list => window.sendEvents(list), events);
    const closeNotice = async text => {
      await page.getByRole('button', { name: `Chiudi l'avviso: ${text}`, exact: true }).click();
      await notices.getByText(text, { exact: true }).waitFor({ state: 'detached' });
    };
    const linesOf = text => text.split('\n').map(part => part.trim()).filter(Boolean);
    const at = '2026-11-24T10:00:00Z';
    await tab('Analisi').click();
    await stage('Analisi').click();
    await run.waitFor();
    // A run that is over: its phase, its state and its steps in words. What it leads to is in the action bar.
    await says(run, 'Pipeline completata');
    await says(run, 'Completata');
    await says(run, 'Pipeline conclusa: sintesi e grafo sono pronti da leggere.');
    await says(run, 'Repository: demo/shop · main · intero progetto');
    assert.match(await run.innerText(), /Analisi del commit 1{12}\.[\s\S]*Avanzamento ed eventi sono quelli del run demo\./);
    const steps = run.getByRole('list', { name: 'Passi della pipeline', exact: true }).getByRole('listitem');
    const stepNotes = async () => (await steps.allInnerTexts()).map(text => linesOf(text).at(-1));
    assert.deepEqual(await stepNotes(), Array(6).fill('Non eseguita'));
    await says(run, 'Nessun evento ancora.');
    assert.equal(await page.getByRole('link', { name: 'Apri l’esploratore', exact: true }).getAttribute('href'), '/?token=test&run=demo');
    await button(page, 'Leggi sintesi').waitFor();
    // A run under way: the progress of a step, the cause of one that failed, the percent, the events to read and copy.
    await serve({ run: { pass: { state: 'running' }, progress: { step: 'analyze', analyzer: 'pyright', done: 1, total: 4 } } });
    await send([
      { kind: 'step.started', step: 'parse', message: '', at }, { kind: 'step.finished', step: 'parse', message: '', at },
      { kind: 'step.started', step: 'stack', message: '', at }, { kind: 'log', level: 'error', step: 'stack', message: 'x', data: { cause: 'manifest illeggibile' }, at },
      { kind: 'step.started', step: 'analyze', message: '', data: { inputs: ['modules.json'] }, at },
    ]);
    await steps.filter({ hasText: 'In corso · 1/4' }).waitFor();
    assert.deepEqual(await stepNotes(), ['Completata', 'In attesa', 'Non riuscita · manifest illeggibile', 'In corso · 1/4', 'In attesa', 'In attesa']);
    assert.match(await run.locator('[aria-current="step"]').innerText(), /4\. Analyze · analyzer per linguaggio/);
    assert.ok(await selectable(steps.getByText('Non riuscita · manifest illeggibile', { exact: true })));
    const bar = run.getByRole('progressbar', { name: 'Passi completati della pipeline', exact: true });
    assert.equal(await bar.getAttribute('aria-valuetext'), '21%');  // one of six, and a quarter
    assert.ok(await selectable(run.getByText('Ultimo avanzamento: Analyze · pyright · 1/4', { exact: true })));
    for (const text of ['1 di 6 passi completati', '21%', 'Analyze · analyzer per linguaggio', 'In esecuzione', 'Ultimo avanzamento: Analyze · pyright · 1/4']) await says(run, text);
    await busyNow(button(page, 'Analisi in corso'));
    const log = run.getByRole('list', { name: 'Ultimi eventi', exact: true }).getByRole('listitem');
    assert.equal(await log.count(), 5);
    assert.match(await log.first().innerText(), /Analyze · avviato[\s\S]*Legge: modules\.json/);  // the newest first
    assert.match(await log.filter({ hasText: 'Stack · nota' }).innerText(), /Errore/);
    assert.ok(await selectable(log.first().getByText('Legge: modules.json', { exact: true })));
    await send(Array.from({ length: 5 }, (_, n) => ({ kind: 'log', step: 'analyze', level: 'info', message: `nota ${n}`, at })));
    await says(run, '10 eventi');
    assert.equal(await log.count(), 8);
    assert.match(await log.first().innerText(), /nota 4/);
    await button(run, 'Altri 2 eventi').click();
    const others = run.getByRole('list', { name: 'Altri 2 eventi', exact: true }).getByRole('listitem');
    await others.first().waitFor();
    assert.deepEqual((await others.allInnerTexts()).map(text => linesOf(text)[0]), ['Parse · completato', 'Parse · avviato']);
    // The run is over with a step that failed; a pass that could not go says why, and one that failed is tried again.
    await send([{ kind: 'step.finished', step: 'analyze', message: '', at }]);
    await serve({ run: { pass: { state: 'unavailable', reason: 'nessun container' } } });
    await alertIn(run, 'Lacuna: il passaggio che rifinisce il grafo delle chiamate non è disponibile.').filter({ hasText: 'nessun container' }).waitFor();
    const unreached = 'Non eseguita · nessun container';
    assert.deepEqual(await stepNotes(), ['Completata', unreached, 'Non riuscita · manifest illeggibile', 'Completata', unreached, unreached]);
    assert.equal(await bar.getAttribute('aria-valuetext'), 'Non riuscito · 33%');
    await serve({ run: { pass: { state: 'failed', reason: 'memoria' } } });
    const pass = alertIn(run, 'Il passaggio che rifinisce il grafo delle chiamate non è riuscito.');
    assert.match(await pass.innerText(), /Errore[\s\S]*memoria/);
    await button(pass, 'Riprova il passaggio').click();
    await notices.getByText('il server ha risposto 404', { exact: true }).waitFor();  // the fixture has no answer to it
    await closeNotice('il server ha risposto 404');
    await page.reload();
    await run.waitFor();
    // The graph as it takes shape: the canvas lays it out; a thing chosen is in the details, and goes to the graph.
    const canvas = run.getByRole('group', { name: 'Costruzione del grafo', exact: true });
    const thing = name => canvas.getByRole('button', { name: new RegExp(`^${name},`) });
    await button(canvas, 'Client, 1 file · confermato').waitFor();
    await button(canvas, 'Server, 6 file · confermato').waitFor();
    assert.equal(await canvas.getByRole('button', { name: /^Apri / }).count(), 0);  // nothing opens in the preview
    assert.match(await run.getByRole('list', { name: 'Tipi di linea', exact: true }).innerText(),
      /Relazioni\s*1[\s\S]*Osservata in esecuzione\s*1[\s\S]*Campionata dal profiler\s*1[\s\S]*Prova insufficiente\s*1/);
    for (const text of ['Codice', '2 directory · 4 relazioni · 2 file', 'Costruzione conclusa']) await says(run, text);
    await thing('Client').click();
    await groupIs('Client');
    assert.match(await group.innerText(), /Directory del grafo di questo run\.[\s\S]*Responsabilità non descritta nel grafo\.[\s\S]*1 file · confermato · commit 1{12}[\s\S]*Apri nel grafo/);
    await thing('Client').and(page.locator('[aria-current="true"]')).waitFor();
    await page.keyboard.press('Escape');
    await group.waitFor({ state: 'hidden' });
    await canvas.locator('[aria-current]').waitFor({ state: 'detached' });
    await thing('Client').focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label')?.startsWith('Server,'));
    await page.keyboard.press('Enter');
    await groupIs('Server');
    await button(group, 'Apri nel grafo').click();
    await screen('Grafo');
    await onContent();
    await groupIs('Server');  // on the graph, the details of the group it was pressed for
    assert.equal(await button(group, 'Apri nel grafo').count(), 0);
    await tab('Analisi').click();
    await group.waitFor({ state: 'hidden' });
    await thing('Client').waitFor();
    // The links: a refusal is a notice that stays; the search is busy, and a note whose tone changes does not take the focus.
    const find = button(run, 'Trova i legami');
    await says(run, /^Non ancora cercati/);
    mode.linkStatus = 500;
    await find.click();
    const refused = notices.getByText('collegamento non riuscito', { exact: true });
    await refused.waitFor();
    assert.match(await notices.innerText(), /Errore/);
    await page.waitForTimeout(6500);
    assert.equal(await refused.count(), 1);
    await closeNotice('collegamento non riuscito');
    mode.linkStatus = 200;
    await find.focus();
    await serve({ links: { state: 'running' } });
    await busyNow(find);
    await serve({ links: { state: 'failed', cause: 'nessuna regola' } });
    await alertIn(run, 'Legami tra i moduli').filter({ hasText: 'Non trovati. nessuna regola' }).waitFor();
    assert.ok(await focused(find));
    await serve({ engine: { engine: null, engines: ['claude'] } });
    await says(run, /Scegli e salva prima un motore\.$/);
    assert.ok(await find.isDisabled());
    await button(run, 'Scegli il motore').click();
    await screen('Motore e domande');
    await onContent();
    await tab('Analisi').click();
    await serve({});
    // New links are a new graph: one that cannot be read says why, and is asked again.
    mode.graphStatus = 500;
    await serve({ links: { state: 'done', routes: { called: 1, offered: 2, linked: 1 }, gaps: 0 } });
    await says(run, /1 richiesta, 2 rotte, 1 legame, 0 lacune\.$/);
    const unread = alertIn(run, 'Grafo non disponibile.');
    assert.match(await unread.innerText(), /grafo non letto/);
    assert.equal(await canvas.count(), 0);
    mode.graphStatus = 200;
    await button(unread, 'Riprova').click();
    await thing('Client').waitFor();
    assert.ok(await inMain());
    // The map of the system: a note whose tone changes is drawn anew, so it is announced.
    const partialMap = { state: 'incomplete', cause: 'the recorded map still has stale or incomplete records',
      needs_review: { nodes: { count: 2, ids: ['a', 'b'] }, flows: { count: 1, ids: ['c'] }, refused_proposals: { count: 1, ids: ['request:d'] } } };
    await map(partialMap);
    const partial = alertIn(run, 'Mappa del sistema parziale');
    assert.match(await partial.innerText(), /2 nodi, 1 flusso, 1 proposta rifiutata[\s\S]*revisione precedente/);
    await partial.evaluate(el => { window.partialNote = el; });
    await map({ state: 'failed', cause: 'motore fermo' });
    await alertIn(run, 'Mappatura del sistema interrotta').filter({ hasText: 'motore fermo' }).waitFor();
    assert.equal(await page.evaluate(() => window.partialNote.isConnected), false);
    await map({ state: 'done' });
    await says(run, /Mappa del sistema registrata/);
    assert.equal(await run.getByRole('alert').count(), 0);
    // The synthesis: the paths by entry, a page at a time, and the writes without an entry.
    await button(page, 'Leggi sintesi').click();
    await synthesis.waitFor();
    await onContent();
    const paths = synthesis.getByRole('region', { name: 'Percorsi per ingresso', exact: true });
    await says(paths, 'Nessun ingresso classificato per questo snapshot.');
    pathsClassified = true;
    await map({ state: 'done', discovery: { count: 2, effect_coverage: { without_entry: 2 } } });
    await says(paths, '2 scritture senza un percorso provato da un ingresso.');
    await says(paths, 'Ingressi 1–1 di 2');
    await paths.getByRole('button', { name: /^Salva ordine/ }).click();
    await says(paths, 'store:ordini');
    await says(paths, 'Effetto');
    assert.ok(await focused(paths));  // what was pressed has gone with its page
    assert.match(await paths.innerText(), /Evento\s+onClick · azione\s+Gestore\s+ui\.ts::save\s+Ingresso\s+ui\.ts:4/);
    await button(paths, 'Passaggi successivi').click();
    await says(paths, 'Destinazione campionata');
    assert.ok(await focused(paths));
    assert.match(await paths.innerText(), /Passaggio 2[\s\S]*Lacuna[\s\S]*campionata dal profiler/);
    await button(paths, 'Passaggi precedenti').click();
    await says(paths, 'store:ordini');
    await button(paths, 'Torna agli ingressi').click();
    await button(paths, 'Ingressi successivi').click();
    await paths.getByRole('button', { name: /^Annulla ordine/ }).waitFor();
    await button(paths, 'Ingressi precedenti').click();
    await paths.getByRole('button', { name: /^Salva ordine/ }).waitFor();
    await button(paths, 'Scritture senza ingresso').click();
    await says(paths, 'store:registro');
    assert.match(await paths.innerText(), /2 di 3 scritture[\s\S]*Le prove si fermano in ui\.ts:8\./);
    mode.pathsBroken = true;  // a page that cannot be read says why, and is asked again
    await button(paths, 'Scritture successive').click();
    await alertIn(paths, 'Percorsi non disponibili.').filter({ hasText: 'percorsi non letti' }).waitFor();
    mode.pathsBroken = false;
    await button(paths, 'Riprova').click();
    await says(paths, 'store:audit');
    assert.ok(await focused(paths));
    await button(paths, 'Torna agli ingressi').click();
    await paths.getByRole('button', { name: /^Salva ordine/ }).waitFor();
    // What the graph counts, the inventory, what is missing, and where to start.
    await says(synthesis, '1 osservata in esecuzione · 1 campionata dal profiler · 1 in conflitto');
    assert.ok(await selectable(synthesis.getByText('1 osservata in esecuzione · 1 campionata dal profiler · 1 in conflitto', { exact: true })));
    await says(synthesis, '1 voce con versione risolta nel modello di build.');
    await says(synthesis, 'Nessuna lacuna registrata dal run.');
    await map(partialMap);
    await alertIn(synthesis, 'Mappa del sistema parziale').waitFor();
    await map({ state: 'done' });
    await says(synthesis, /Mappa del sistema registrata/);
    assert.equal(await page.getByText('Mappa del sistema parziale').count(), 0);
    await button(synthesis, 'Provenienza e lacune').click();
    const provenance = detail('Provenienza e lacune del grafo');
    await provenance.waitFor();
    assert.match(await provenance.innerText(), /Repository\s+demo\/shop[\s\S]*Directory \/ relazioni\s+2 \/ 4[\s\S]*Passaggio del grafo\s+completato[\s\S]*Limiti dichiarati/);
    await page.keyboard.press('Escape');
    await provenance.waitFor({ state: 'hidden' });
    const largest = synthesis.getByRole('list', { name: 'Responsabilità da esplorare', exact: true }).getByRole('button');
    assert.match((await largest.allInnerTexts()).join('\n'), /Server[\s\S]*6 file · confermato[\s\S]*Client/);
    await largest.first().click();
    await screen('Grafo');
    await groupIs('Server');
    await onContent();
    await tab('Analisi').click();
    await synthesis.waitFor();
    await button(page, 'Esplora il grafo completo').click();
    await screen('Grafo');
    await onContent();
    await tab('Analisi').click();
    // A narrow window holds both. Then what was kept of where the person looked goes: what follows starts as a first opening.
    await page.setViewportSize({ width: 390, height: 820 });
    await synthesis.waitFor();
    assert.ok(await fits());
    await button(main, 'Percorso').click();
    await stage('Analisi').click();
    await thing('Client').waitFor();
    assert.ok(await fits());
    await page.setViewportSize({ width: 1280, height: 850 });
    await page.evaluate(() => localStorage.removeItem('daodan-app-v2'));
    await page.reload();
    await stage('Repository').waitFor();
  }
  // ticket 22: the graph
  {
    const tab = name => page.getByRole('toolbar', { name: 'Daodan', exact: true }).getByRole('button', { name: new RegExp(`^${name}`) });
    const panel = main.getByRole('region', { name: 'Grafo del codice', exact: true });
    const canvas = panel.getByRole('group', { name: 'Grafo interattivo', exact: true });
    const thing = name => canvas.getByRole('button', { name: new RegExp(`^${name},`) });
    const button = (where, name) => where.getByRole('button', { name, exact: true });
    const says = (where, text) => where.getByText(text, { exact: true }).waitFor();
    const detail = name => page.getByRole('complementary', { name, exact: true });
    const group = detail('Dettaglio del gruppo'), groupIs = name => group.getByRole('heading', { name, exact: true }).waitFor();
    const marked = name => thing(name).and(page.locator('[aria-current="true"]')).waitFor();
    const focusOn = start => page.waitForFunction(text => document.activeElement?.getAttribute('aria-label')?.startsWith(text), start);
    const onCanvas = () => page.waitForFunction(() => document.activeElement?.closest('[aria-roledescription="grafo"]'));
    const serve = patch => page.evaluate(state => window.setServerState(state), patch);
    const search = panel.getByRole('searchbox', { name: 'Cerca un gruppo o un file', exact: true });
    const filter = name => panel.getByRole('combobox', { name, exact: true });
    const pick = async (name, option) => {
      await filter(name).click();
      await page.getByRole('option', { name: option, exact: true }).click();
    };
    const clear = button(panel, 'Azzera filtri').first();  // over the canvas: where nothing is found there is another one
    // A graph that cannot be read says why, with Riprova; its filters wait in their place.
    mode.graphStatus = 500;
    await tab('Grafo').click();
    const unread = panel.getByRole('alert').filter({ hasText: 'Grafo non disponibile.' });
    assert.match(await unread.innerText(), /Errore[\s\S]*grafo non letto[\s\S]*Riprova/);
    for (const control of [search, filter('Direzione'), filter('Profondità'), filter('Relazioni'), clear]) assert.ok(await control.isDisabled());
    await page.keyboard.press('Control+f');
    await page.getByText('Questa vista non ha una ricerca.').last().waitFor();
    mode.graphStatus = 200;
    await button(unread, 'Riprova').click();
    await button(canvas, 'Client, 1 file · confermato').waitFor();
    await button(canvas, 'Server, 6 file · confermato').waitFor();
    assert.ok(await inMain());
    // It opens whole, with the details of the group it is read from, as tall as the panel leaves.
    await groupIs('Server');
    await marked('Server');
    await says(panel, 'Codice · 2 / 2 nodi');
    assert.ok((await canvas.boundingBox()).height >= 300);
    assert.equal(await canvas.getAttribute('aria-roledescription'), 'grafo');
    assert.equal(await page.getByRole('link', { name: 'Apri l’esploratore', exact: true }).getAttribute('href'), '/?token=test&run=demo');
    // The lines are said by their words, to screen readers always, and by their key, with how many are in view.
    const heard = await thing('Client').evaluate(el => el.getAttribute('aria-describedby').split(' ').map(id => document.getElementById(id)?.textContent).join(' '));
    for (const text of ['1 chiamata · osservata in esecuzione, verso Server', 'campionata dal profiler', 'destinazioni in conflitto', 'Alt e una freccia lo spostano']) {
      assert.ok(heard.includes(text), text);
    }
    const lineKinds = panel.getByRole('list', { name: 'Tipi di linea', exact: true });
    assert.match(await lineKinds.innerText(),
      /Relazioni\s*1[\s\S]*Osservata in esecuzione\s*1[\s\S]*Campionata dal profiler\s*1[\s\S]*Prova insufficiente\s*1/);
    await says(panel, '4 relazioni visibili');
    // The filters: the kind of relation, the neighbourhood of the group it is read from, the search. One button clears them.
    assert.ok(await clear.isDisabled());
    await pick('Relazioni', 'Import');
    await says(panel, '0 relazioni visibili');
    await lineKinds.waitFor({ state: 'detached' });
    await clear.click();
    await says(panel, '4 relazioni visibili');
    await page.getByText('Filtri azzerati: tutti i gruppi del grafo sono visibili.', { exact: true }).waitFor();
    assert.deepEqual([await focused(search), await clear.isDisabled()], [true, true]);
    await pick('Profondità', '1 livello');
    await pick('Direzione', 'Dipendenze →');  // nothing leaves the server
    await says(panel, 'Codice · 1 / 2 nodi');
    await thing('Client').waitFor({ state: 'detached' });
    await clear.click();
    await says(panel, 'Codice · 2 / 2 nodi');
    await tab('Grafo').focus();
    await page.keyboard.press('Control+f');
    assert.ok(await focused(search));
    await search.fill('server/file5');
    await thing('Client').waitFor({ state: 'detached' });
    await thing('Server').waitFor();
    await search.fill('niente');
    await says(panel, 'Nessun gruppo trovato');
    await button(panel, 'Azzera filtri').last().click();
    await thing('Client').waitFor();
    assert.deepEqual([await focused(search), await search.inputValue()], [true, '']);
    await tab('Grafo').focus();
    await page.keyboard.press('F6');
    assert.ok(await inMain());
    // A logo that does not come leaves the icon of the kind, in its place.
    await thing('Client').locator('img').waitFor({ state: 'detached' });
    assert.equal(await thing('Client').locator('svg').count(), 1);
    assert.ok(markRequests.includes('?id=react&token=test'));
    // A group chosen: what it is, its stack, its relations with what proves them, and its files, each with what is recorded in it.
    await thing('Client').click();
    await groupIs('Client');
    await marked('Client');
    assert.match(await group.innerText(), /Directory selezionata\s*confermato[\s\S]*Responsabilità non descritta nel grafo\.[\s\S]*File assegnati\s*1\s*Relazioni nel grafo\s*4\s*Provenienza\s*Directory del checkout/);
    assert.match(await group.getByRole('list', { name: 'Stack', exact: true }).innerText(), /React\s*framework\s*package\.json:12/);
    for (const text of ['Altre dipendenze dichiarate: 3', 'Nessuna evidenza dichiarata.']) await says(group, text);
    await button(group, 'Relazioni del gruppo (4)').click();
    const relations = group.getByRole('list', { name: 'Relazioni del gruppo (4)', exact: true }).getByRole('listitem');
    await relations.first().waitFor();
    assert.equal(await relations.count(), 4);
    assert.match(await relations.first().innerText(), /→ Server\s*1 chiamata/);
    await button(group, 'Prove delle chiamate (3)').click();
    const proofs = group.getByRole('list', { name: 'Prove delle chiamate (3)', exact: true });
    for (const text of ['Client → Server · osservata in esecuzione', 'Client → Server · campionata dal profiler',
      'Client → Server · osservata in esecuzione · destinazioni in conflitto']) await says(proofs, text);
    await button(group, 'Client/file0.ts').click();
    await says(group, 'chiama · save · osservata in esecuzione · riga 3 · Server/file1.ts');
    assert.ok(await selectable(proofs.getByText('Client → Server · campionata dal profiler', { exact: true })));
    // By keyboard the arrows follow the lines and Enter chooses; the details follow the choice, with every file in place.
    await thing('Client').focus();
    await page.keyboard.press('ArrowRight');
    await focusOn('Server,');
    await page.keyboard.press('Enter');
    await groupIs('Server');
    await button(group, 'Tutti i 6 file').click();
    const files = group.getByRole('list', { name: 'Tutti i 6 file', exact: true }).getByRole('listitem');
    await files.first().waitFor();
    assert.equal(await files.count(), 6);
    assert.equal(await group.getByRole('list', { name: 'Stack', exact: true }).count(), 0);
    await thing('Client').click();
    await groupIs('Client');
    assert.equal(await button(group, 'Tutti i 6 file').count(), 0);
    await button(group, 'Chiudi').click();
    await group.waitFor({ state: 'hidden' });
    await canvas.locator('[aria-current]').waitFor({ state: 'detached' });
    await button(panel, 'Provenienza e lacune').click();
    const provenance = detail('Provenienza e lacune del grafo');
    await provenance.waitFor();
    await page.keyboard.press('Escape');
    await provenance.waitFor({ state: 'hidden' });
    // A group opens in place: a frame around what it holds, with the rest in sight, and its details; its button closes it. The focus
    // stays on it.
    const frame = canvas.getByRole('group', { name: 'Client, aperto, contiene un elemento', exact: true });
    await button(canvas, 'Apri Client').click();
    await frame.waitFor();
    await thing('main.ts').waitFor();
    await thing('Server').waitFor();
    await groupIs('Client');
    assert.match(await group.innerText(), /aperto sul posto[\s\S]*Elementi dentro\s*1\s*Relazioni nel grafo\s*4/);
    await onCanvas();
    await button(canvas, 'Chiudi Client').click();
    await frame.waitFor({ state: 'detached' });
    await button(canvas, 'Apri Client').waitFor();
    assert.equal(await thing('main.ts').count(), 0);
    await groupIs('Client');
    await onCanvas();
    // From the details too: one button opens and closes it, and keeps the focus.
    await button(group, 'Apri sul posto').click();
    await frame.waitFor();
    await button(group, 'Chiudi il gruppo').and(page.locator(':focus')).waitFor();
    await button(canvas, 'Client').click();  // the title of the frame
    await groupIs('Client');
    // A file: its symbols are read; those that cannot be read say why, and are asked again.
    const symbolsRoute = url => url.pathname === '/api/app/symbols';
    await context.route(symbolsRoute, route => route.fulfill({ status: 500, json: { error: 'simboli non letti' } }));
    await thing('main.ts').click();
    await groupIs('main.ts');
    const symbols = group.getByRole('region', { name: 'Simboli e chiamate', exact: true });
    const noSymbols = symbols.getByRole('alert').filter({ hasText: 'Simboli non disponibili.' });
    await noSymbols.filter({ hasText: 'simboli non letti' }).waitFor();
    await context.unroute(symbolsRoute);
    await button(noSymbols, 'Riprova').click();
    await says(symbols, 'save');
    assert.match(await symbols.innerText(), /save\s*righe 1–5[\s\S]*Nessuna chiamata risolta da o verso i suoi simboli\./);
    assert.ok(await focused(symbols));
    // What was open and what was chosen are kept. A logo that comes takes the place of the icon.
    mode.marks = true;
    await page.reload();
    await frame.waitFor();
    await groupIs('main.ts');
    await marked('main.ts');
    await button(canvas, 'Chiudi Client').click();
    await frame.waitFor({ state: 'detached' });
    await thing('Client').waitFor();
    await thing('Client').locator('svg').waitFor({ state: 'detached' });
    assert.ok(await thing('Client').locator('img').evaluate(img => img.naturalWidth > 0));
    mode.marks = false;
    // The things move, by the keys too, and one button puts them back.
    await thing('Server').focus();
    await page.keyboard.press('Alt+ArrowDown');
    await button(canvas, 'Riordina').click();
    await button(canvas, 'Riordina').waitFor({ state: 'detached' });
    // Another screen takes the details away, and they are there again with the graph; on a narrow window they cover the end of it.
    await tab('Analisi').click();
    await group.waitFor({ state: 'hidden' });
    await tab('Grafo').click();
    await group.waitFor();
    await page.setViewportSize({ width: 900, height: 820 });
    const sheet = page.getByRole('dialog', { name: 'Dettaglio del gruppo' });
    await sheet.waitFor();
    await button(sheet, 'Chiudi').click();
    await sheet.waitFor({ state: 'detached' });
    await thing('Client').waitFor();
    assert.ok(await fits());
    await page.setViewportSize({ width: 390, height: 820 });
    await thing('Client').waitFor();
    assert.deepEqual([(await canvas.boundingBox()).height >= 200, await fits()], [true, true]);
    await page.setViewportSize({ width: 1280, height: 850 });
    // Without a repository there is no graph. Then what was kept of where the person looked goes: what follows starts as a first opening.
    await serve({ context: null, job: { state: 'idle' } });
    await says(panel, 'Nessun grafo');
    await button(panel, 'Vai al repository').click();
    await main.getByRole('region', { name: 'Repository', exact: true }).waitFor();
    await onContent();
    await page.evaluate(() => localStorage.removeItem('daodan-app-v2'));
    await page.reload();
    await main.getByRole('region', { name: 'Repository', exact: true }).waitFor();
  }
  // ticket 23: the engine and the questions
  {
    const serve = patch => page.evaluate(state => window.setServerState(state), patch);
    const wrong = text => main.getByRole('alert').filter({ hasText: text });
    const said = text => main.getByRole('status').filter({ hasText: text });  // what came of the form, when nothing is wrong
    const button = name => main.getByRole('button', { name, exact: true });
    const field = label => main.getByLabel(label, { exact: true });
    const focusOn = text => page.waitForFunction(wanted => document.activeElement?.textContent.trim() === wanted, text);
    const answered = async (path, reply) => {  // what a route answers, until it is left to the fixture again
      const here = url => url.pathname === path;
      await context.route(here, reply);
      return () => context.unroute(here);
    };
    const question = main.getByRole('textbox', { name: 'Domanda', exact: true });
    const ask = page.getByRole('button', { name: 'Chiedi', exact: true });
    const answer = main.getByRole('region', { name: 'Risposta', exact: true });
    await choose('Vai a Motore e domande');
    await main.getByRole('region', { name: 'Motore e domande', exact: true }).waitFor();
    await page.keyboard.press('Control+f');
    await page.getByText('Questa vista non ha una ricerca.').last().waitFor();
    // Without a repository, or an engine, nothing can be asked, and why is beside the button.
    await serve({ context: null, job: { state: 'idle' } });
    await page.getByText('Seleziona prima una repository.', { exact: true }).waitFor();
    assert.deepEqual([await question.isDisabled(), await ask.isDisabled()], [true, true]);
    await serve({ engine: { engine: null, engines: ['claude'] } });
    const choice = page.getByText('Scegli e salva prima un motore.', { exact: true });
    await choice.waitFor();
    assert.deepEqual([await question.isEnabled(), await ask.isDisabled()], [true, true]);
    await serve({});
    await choice.waitFor({ state: 'detached' });
    await main.getByText('Il motore usa il run demo di demo/shop.', { exact: true }).waitFor();
    await answer.getByText('Nessuna domanda', { exact: true }).waitFor();
    // The question and its answer, with the tools used.
    await question.fill('Dove si firma il token?');
    await ask.click();
    const text = answer.getByText('Lo firma auth.ts', { exact: true });
    await text.waitFor();
    assert.match(await answer.innerText(), /conclusa[\s\S]*Operazioni di Daodan usate[\s\S]*cerca\s+token[\s\S]*Lo firma auth\.ts/);
    assert.ok(await selectable(text));
    assert.equal(await answer.locator('[aria-live="polite"]').filter({ hasText: 'Lo firma auth.ts' }).count(), 1);
    assert.notEqual(await ask.getAttribute('aria-busy'), 'true');
    // A busy button ignores the pointer, not the keyboard: Enter on it must not send the question a second time.
    assert.equal(askRequests.length, 1);
    const working = page.getByText('Il motore sta rispondendo.', { exact: true });
    await serve({ asked: { state: 'running', question: 'Dove si firma il token?' } });
    await busyNow(ask);
    await working.waitFor();
    await ask.focus();
    await page.keyboard.press('Enter');
    await page.keyboard.press('Space');
    await page.waitForTimeout(300);
    assert.equal(askRequests.length, 1);
    await serve({ asked: { state: 'done', question: 'Dove si firma il token?' } });
    await working.waitFor({ state: 'detached' });
    // An engine at work, then one that failed: the state in words, and the cause.
    let leave = await answered('/api/app/answer', route => route.fulfill({ json: { events: [], next: 0, state: 'running', text: '', cause: null } }));
    await ask.click();
    await answer.getByText('in corso', { exact: true }).waitFor();
    await answer.getByRole('progressbar', { name: 'In attesa del motore…' }).waitFor();
    await busyNow(ask);
    const leaveWorking = leave;
    leave = await answered('/api/app/answer', route => route.fulfill({ json: { events: [], next: 0, state: 'failed', text: '', cause: 'il motore si è fermato' } }));
    await wrong('Domanda non riuscita.').filter({ hasText: 'il motore si è fermato' }).waitFor();
    assert.match(await answer.innerText(), /non riuscita/);
    assert.equal(askRequests.length, 2);
    await leave();
    await leaveWorking();
    // The engine: an endpoint has an address, a model and a key; a command line has none.
    await serve({ engine: { engine: 'openai', engines: ['claude', 'openai'], api_key: 'set', base_url: 'https://api.test/v1', model: 'm' } });
    const engine = main.getByRole('combobox', { name: 'Motore', exact: true });
    assert.match(await engine.innerText(), /Claude Code \(riga di comando\)/);
    assert.deepEqual([await field('Modello').count(), await field('Chiave').count()], [0, 0]);
    await engine.click();
    await page.getByRole('option', { name: 'Endpoint compatibile OpenAI' }).click();
    for (const label of ['Indirizzo dell’endpoint', 'Modello', 'Chiave', 'Domanda']) await field(label).waitFor();
    await main.getByText('Chiave impostata: lasciare vuoto per tenerla.', { exact: true }).waitFor();
    assert.equal(await field('Chiave').getAttribute('type'), 'password');
    // The key's removal is confirmed, from «Annulla»: Escape and it leave the key, and the focus goes back.
    const forget = button('Rimuovi la chiave');
    const sure = page.getByRole('dialog', { name: 'Rimuovere la chiave?' });
    for (const cancel of [() => page.keyboard.press('Escape'), () => sure.getByRole('button', { name: 'Annulla', exact: true }).click()]) {
      await forget.click();
      await sure.waitFor();
      await focusOn('Annulla');
      assert.match(await sure.innerText(), /deposito delle credenziali[\s\S]*non si può recuperare/);
      await cancel();
      await sure.waitFor({ state: 'detached' });
      await focusOn('Rimuovi la chiave');
    }
    assert.equal(engineRequests.length, 0);
    await forget.click();
    await sure.getByRole('button', { name: 'Rimuovi la chiave', exact: true }).click();
    await said('Chiave rimossa.').waitFor();
    assert.deepEqual(engineRequests, [{ api_key: '' }]);
    await forget.waitFor({ state: 'detached' });  // the button is gone: the focus is in the key's field
    await page.waitForFunction(() => document.activeElement?.getAttribute('type') === 'password');
    await main.getByText('Va nel deposito delle credenziali del sistema.', { exact: true }).waitFor();
    // The engine is tried: the button is busy, and what came of it is said.
    const probe = button('Prova il motore');
    leave = await answered('/api/app/probe', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({ json: { engine: 'openai', reachable: true, tools: true } });
    });
    await probe.click();
    await busyNow(probe);
    await said('Prova in corso…').waitFor();
    await said('openai: risponde, chiama gli strumenti.').waitFor();
    await leave();
    leave = await answered('/api/app/probe', route => route.fulfill({ json: { engine: 'openai', reachable: false, tools: null, detail: 'rifiutato' } }));
    await probe.click();
    await wrong('openai: non risponde. rifiutato').waitFor();
    await leave();
    // The form is saved, and the key is not kept in the page.
    await field('Indirizzo dell’endpoint').fill('https://api.test/v1');
    await field('Modello').fill('m');
    await field('Chiave').fill('segreta');
    await field('Chiave').press('Enter');
    await said('Motore salvato.').waitFor();
    assert.deepEqual(engineRequests.slice(1), [{ engine: 'openai', base_url: 'https://api.test/v1', model: 'm', api_key: 'segreta' }]);
    assert.equal(await field('Chiave').inputValue(), '');
    await page.setViewportSize({ width: 390, height: 820 });
    assert.deepEqual([await ask.isVisible(), await fits()], [true, true]);
    await page.setViewportSize({ width: 1280, height: 850 });
  }

  // The Codebase Map.
  const nav = page.getByRole('navigation', { name: 'Mappa' });
  const row = name => nav.getByRole('button', { name });
  const elements = nav.getByRole('list', { name: 'Elementi visibili', exact: true });
  const whole = row('Tutta la mappa');
  const info = page.getByRole('complementary', { name: 'Informazioni sul progetto' });
  const details = page.getByRole('complementary', { name: 'Dettaglio' });
  const flowPanel = page.getByRole('complementary', { name: 'Flusso', exact: true });
  const infoButton = main.getByRole('button', { name: 'Informazioni sul progetto' });
  const openOther = main.getByRole('button', { name: 'Apri altro export' });
  const up = main.getByRole('button', { name: 'Su', exact: true });
  const search = main.getByLabel('Cerca per nome');
  const place = path => main.getByText(new RegExp(`^${path} · \\d+ nod`));  // the line beside the panel's title
  const closeIn = region => region.getByRole('button', { name: 'Chiudi', exact: true }).click();
  // The canvas is a group named by the page; a node is a button named by its name, its step, «esterno», what it contains and its kind.
  const canvas = main.getByRole('group', { name: 'Naviga il grafo', exact: true });
  const thing = name => canvas.getByRole('button', { name: new RegExp(`^${name},`) });
  // A group: the arrow that opens it in place, the one that closes it, its frame once open, and the › that goes into it.
  const onGroup = action => name => canvas.getByRole('button', { name: `${action} ${name}`, exact: true });
  const [opens, closes, enters] = ['Apri', 'Chiudi', 'Entra in'].map(onGroup);
  const frame = name => canvas.getByRole('group', { name: new RegExp(`^${name}, aperto, contiene`) });
  const kinds = main.getByRole('list', { name: 'Tipi di linea', exact: true });
  const kindOfLine = text => kinds.getByRole('listitem').filter({ hasText: text });
  const busy = main.locator('[aria-busy="true"]');
  const focusOn = start => page.waitForFunction(text => document.activeElement?.getAttribute('aria-label')?.startsWith(text), start);
  const frames = count => page.evaluate(left => new Promise(done => {
    const next = () => { left -= 1; if (left < 0) done(); else requestAnimationFrame(next); };
    next();
  }), count);
  const until = async (holds, what) => {
    for (const end = Date.now() + 8000; !await holds(); await frames(1)) assert.ok(Date.now() < end, what);
  };
  // What is on the canvas, and nothing on it moving (the view and the things glide for a fifth of a second).
  const rest = async () => {
    let last = '';
    await until(async () => {
      const now = JSON.stringify(await canvas.getByRole('button').evaluateAll(all => all.map(el => { const { x, y, width } = el.getBoundingClientRect(); return [x, y, width].map(Math.round); })));
      const same = now === last;
      last = now;
      if (!same) await frames(15);
      return same;
    }, 'the canvas at rest');
  };
  const inSight = async name => {
    const [box, node] = await Promise.all([canvas.boundingBox(), thing(name).boundingBox({ timeout: 200 }).catch(() => null)]);  // out of the view a node is not drawn
    return !!node && node.x >= box.x && node.x + node.width <= box.x + box.width && node.y >= box.y && node.y + node.height <= box.y + box.height;
  };
  const comes = (name, wanted = true) => until(async () => await inSight(name) === wanted, `${name} ${wanted ? 'in' : 'out of'} sight`);
  // Where a node is in the canvas and how large: the view.
  const viewAt = async name => {
    const [box, node] = await Promise.all([canvas.boundingBox(), thing(name).boundingBox()]);
    return [node.x - box.x, node.y - box.y, node.width].map(Math.round);
  };
  const fitAll = async () => {
    await canvas.getByRole('button', { name: 'Inquadra tutto', exact: true }).click();
    await rest();
  };
  // Everything out of sight, by the ground of the canvas: a drag on a thing would move the thing.
  const panAway = async () => {
    await fitAll();
    await canvas.scrollIntoViewIfNeeded();
    const { x, y, width, height } = await canvas.boundingBox();
    for (let drags = 0; drags < 2; drags += 1) {
      await page.mouse.move(x + 8, y + 8);
      await page.mouse.down();
      await page.mouse.move(x + width / 2, y + height / 2, { steps: 4 });
      await page.mouse.move(x + width - 12, y + height - 12, { steps: 4 });
      await page.mouse.up();
    }
  };
  const logoIn = async where => await where.locator('img').count() === 1 && where.locator('img').evaluate(img => img.complete && img.naturalWidth > 0);
  // The layout can be held, so that a test sees what the page does while it waits for one.
  await page.addInitScript(() => {
    const post = Worker.prototype.postMessage;
    Worker.prototype.postMessage = function (...message) {
      if (window.holdLayout) window.heldLayout = () => post.apply(this, message);
      else post.apply(this, message);
    };
  });
  await page.setViewportSize({ width: 1280, height: 850 });
  mode.exportBroken = true;  // an export that cannot be read: the page waits, then says what failed, with Riprova
  mode.exportBusy = 1;       // and before that a busy project, which is asked again
  mode.exportDelay = 1000;
  await page.goto('http://daodan.test/');
  assert.equal(await page.title(), 'Daodan · Mappa');
  await main.getByRole('progressbar', { name: "Carico l'export…" }).waitFor();
  await line("Carico l'export…").waitFor();
  await nav.getByText("In attesa dell'export.").waitFor();
  assert.equal(await busy.count(), 1);
  const unreadable = main.getByRole('alert');
  await page.getByText('Daodan è occupato, riprovo', { exact: true }).waitFor();
  assert.equal(await unreadable.count(), 0);
  await unreadable.waitFor();
  assert.equal(mode.exportBusy, 0);
  assert.match(await unreadable.innerText(), /Errore[\s\S]*Export non leggibile[\s\S]*Riprova/);
  await line('Export non leggibile').waitFor();
  assert.ok(await selectable(unreadable.getByText('non dice il suo schema')));
  await nav.getByText("Nessuna mappa: l'export non si legge.").waitFor();
  assert.equal(await nav.getByText("In attesa dell'export.").count(), 0);
  for (const control of [search, up, infoButton, openOther]) assert.ok(await control.isDisabled());  // in their place, with nothing to do
  assert.equal(await busy.count(), 0);
  mode.exportBroken = false;
  mode.exportDelay = 0;
  mode.layoutLost = true;  // a layout that does not come: the canvas waits, then says what failed, with Riprova
  await unreadable.getByRole('button', { name: 'Riprova' }).click();
  await line('shop · run fixture').waitFor();
  await main.getByRole('progressbar', { name: 'Dispongo il grafo…' }).waitFor();
  await main.getByText('Sistema · Dispongo il grafo…', { exact: true }).waitFor();
  await line('Dispongo il grafo…').waitFor();  // said as it is waited for
  assert.deepEqual([await unreadable.count(), await busy.count(), await canvas.count()], [0, 1, 0]);
  await unreadable.waitFor();
  assert.match(await unreadable.innerText(), /Errore[\s\S]*Impossibile disporre il grafo[\s\S]*5000 ms[\s\S]*Riprova/);
  mode.layoutLost = false;
  await unreadable.getByRole('button', { name: 'Riprova' }).click();
  await thing('web').waitFor({ timeout: 15000 });
  assert.deepEqual([await unreadable.count(), await busy.count()], [0, 0]);
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
  // The canvas, as tall as the panel leaves, with its view's buttons and the key of its lines.
  assert.ok((await canvas.boundingBox()).height >= 320);
  assert.equal(await canvas.getAttribute('aria-roledescription'), 'grafo');
  for (const name of ['Ingrandisci', 'Riduci', 'Inquadra tutto']) await canvas.getByRole('button', { name, exact: true }).waitFor();
  await canvas.getByRole('button', { name: 'web, contiene 3 elementi, componente', exact: true }).waitFor();
  assert.match(await kinds.innerText(), /Relazioni\s*6[\s\S]*Collegamenti di dati\s*3/);
  // The logo of a service is on its node and on its row; one that does not load leaves the icon.
  await until(() => logoIn(thing('card payment provider')), 'the logo on its node');
  await until(() => logoIn(row(/^card payment provider/)), 'the logo on its row');
  // So is that of the one framework a group of code declares.
  await until(() => logoIn(thing('web')), 'the logo of its framework on the node of a group');
  await until(() => logoIn(row(/^web/)), 'the logo of its framework on the row of a group');
  for (const where of [thing('API gateway'), row(/^API gateway/)]) {
    await until(async () => await where.locator('img').count() === 0 && await where.locator('svg').count() > 0, 'the icon of what has no logo');
  }
  assert.deepEqual([...new Set(marksAsked)].sort(), ['?id=gone', '?id=react', '?id=stripe']);
  // A node pressed is in the details; Escape on it, or a press beside the nodes, leaves it.
  await thing('web').click();
  await details.getByRole('heading', { name: 'web', exact: true }).waitFor();
  await thing('web').and(page.locator('[aria-current="true"]')).waitFor();
  assert.equal(await canvas.locator('[aria-current]').count(), 1);
  await thing('web').focus();
  await page.keyboard.press('Escape');
  await details.waitFor({ state: 'hidden' });
  await canvas.locator('[aria-current]').waitFor({ state: 'detached' });
  await thing('server').click();
  await details.getByRole('heading', { name: 'server', exact: true }).waitFor();
  await canvas.click({ position: { x: 8, y: 8 } });
  await details.waitFor({ state: 'hidden' });
  // By keyboard: the arrows follow the lines, Enter chooses; after a group are the arrow that opens it in place and the › that enters it.
  await thing('web').focus();
  for (const [key, name] of [['ArrowRight', 'server,'], ['ArrowLeft', 'web,'], ['ArrowRight', 'server,']]) {
    await page.keyboard.press(key);
    await focusOn(name);
  }
  await page.keyboard.press('Enter');
  await details.getByRole('heading', { name: 'server', exact: true }).waitFor();
  await until(() => opens('server').evaluate(el => el.tabIndex === 0), 'the arrow of the chosen group on the way of Tab');
  await page.keyboard.press('Tab');
  await focusOn('Apri server');
  await page.keyboard.press('Tab');
  await focusOn('Entra in server');
  await page.keyboard.press('Enter');
  await place('Sistema / server').waitFor();
  await details.waitFor({ state: 'hidden' });
  await thing('money.ts').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await enters('web').click();  // by its ›
  await place('Sistema / web').waitFor();
  await enters('checkout.tsx').click();
  await place('Sistema / web / checkout.tsx').waitFor();
  await thing('pay').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await thing('web').waitFor();
  await rest();
  assert.equal(await details.count(), 0);
  await thing('web').dblclick();  // a double press enters, also the first: the details its first press opens narrow the canvas, and move nothing on it
  await place('Sistema / web').waitFor();
  await thing('api.ts').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await thing('web').click();  // and with the details open
  await details.waitFor();
  await thing('web').dblclick();
  await place('Sistema / web').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  // A group opens in place by its arrow: what it holds is in its frame, and the rest is there as it was.
  await opens('web').click();
  await frame('web').waitFor();
  await rest();
  for (const name of ['checkout.tsx', 'api.ts', 'money.ts', 'server', 'card payment provider', 'Cliente']) await thing(name).waitFor();
  await panel.getByText(/^Sistema · 11 nodi · /).waitFor();
  assert.deepEqual([await up.isDisabled(), await details.count()], [true, 0]);  // the place is the same, and nothing is chosen
  const inFrame = async (name, group) => {
    const [a, b] = await Promise.all([frame(group).boundingBox(), thing(name).boundingBox()]);
    return b.x >= a.x && b.y > a.y && b.x + b.width <= a.x + a.width + 1 && b.y + b.height <= a.y + a.height + 1;
  };
  assert.deepEqual([await inFrame('checkout.tsx', 'web'), await inFrame('money.ts', 'web'), await inFrame('server', 'web')], [true, true, false]);
  assert.equal(await elements.getByText('file · in web', { exact: true }).count(), 3);
  await opens('checkout.tsx').click();  // a group in a group
  await frame('checkout.tsx').waitFor();
  await rest();
  assert.ok(await inFrame('pay', 'checkout.tsx') && await inFrame('api.ts', 'web'));
  await thing('pay').click();
  await details.getByRole('heading', { name: 'pay', exact: true }).waitFor();
  await fitAll();
  await closes('checkout.tsx').click();  // what stands for the chosen thing is chosen
  await frame('checkout.tsx').waitFor({ state: 'detached' });
  await thing('checkout.tsx').and(page.locator('[aria-current="true"]')).waitFor();
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
  // A search that finds nothing but a thing in it keeps its frame.
  await search.fill('checkout');
  await thing('server').waitFor({ state: 'detached' });
  assert.ok(await frame('web').isVisible() && await thing('checkout.tsx').isVisible());
  await search.fill('');
  await thing('server').waitFor();
  // It closes by its arrow, and by keyboard opens and closes with the focus on it.
  await closes('web').click();
  await frame('web').waitFor({ state: 'detached' });
  await thing('checkout.tsx').waitFor({ state: 'detached' });
  await panel.getByText('Sistema · 8 nodi · 6 relazioni visibili', { exact: true }).waitFor();
  await thing('web').focus();
  for (const [action, start] of [['Apri web', 'attached'], ['Chiudi web', 'detached']]) {
    await until(() => canvas.getByRole('button', { name: action, exact: true }).evaluate(el => el.tabIndex === 0), `${action} on the way of Tab`);
    await page.keyboard.press('Tab');
    await focusOn(action);
    await page.keyboard.press('Enter');
    await frame('web').waitFor({ state: start });
    await focusOn('web,');
  }
  // An open group is entered by the row and by the command, and the way back is the same.
  await opens('web').click();
  await frame('web').waitFor();
  await row('Entra in web').click();
  await place('Sistema / web').waitFor();
  await up.click();
  await place('Sistema').waitFor();
  await details.getByRole('heading', { name: 'web', exact: true }).waitFor();
  await comes('web');
  await choose("Entra nell'elemento scelto");
  await place('Sistema / web').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  // A thing moves, here from the keyboard, and the layout is put back.
  await thing('Cliente').waitFor();
  await rest();
  const reset = canvas.getByRole('button', { name: 'Riordina', exact: true });
  const start = await viewAt('Cliente');
  assert.equal(await reset.count(), 0);
  await thing('Cliente').focus();
  await page.keyboard.press('Alt+ArrowDown');
  await line(/^Cliente spostato a /).waitFor();
  await reset.waitFor();
  await until(async () => (await viewAt('Cliente'))[1] > start[1], 'a moved thing');
  await reset.click();
  await reset.waitFor({ state: 'detached' });
  await rest();
  assert.deepEqual(await viewAt('Cliente'), start);
  // What a press moves glides, and with the system's reduced motion it jumps.
  await page.evaluate(label => document.addEventListener('transitionrun', event => {
    if (event.propertyName === 'transform' && event.target.closest(`[aria-label="${label}"]`)) window.glided = true;
  }, true), 'Naviga il grafo');
  for (const reducedMotion of ['reduce', 'no-preference']) {
    await page.emulateMedia({ reducedMotion });
    await page.evaluate(() => { window.glided = false; });
    await opens('web').click();
    await frame('web').waitFor();
    await rest();
    assert.equal(await page.evaluate(() => window.glided), reducedMotion !== 'reduce', reducedMotion);
    await closes('web').click();
    await frame('web').waitFor({ state: 'detached' });
    await rest();
  }
  // The skip link goes to the content.
  await page.getByRole('link', { name: 'Vai al contenuto' }).press('Enter');
  await page.waitForFunction(() => document.activeElement?.tagName === 'MAIN');
  // The views are places of the bar.
  const view = name => page.getByRole('button', { name: new RegExp(`^${name}`) });
  assert.equal(await view('Logica').getAttribute('aria-current'), 'page');
  await view('Fisica').click();
  await page.getByRole('main', { name: 'Mappa fisica' }).waitFor();
  await thing('shop').waitFor();
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
  await until(() => logoIn(info.getByRole('term').filter({ hasText: 'React' })), 'the logo of a technology');
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
  await page.evaluate(() => { window.holdLayout = true; });
  await pay.click();
  // Its layout is waited for: that is said, and the last one stays, with no number of the flow just chosen.
  await line('Dispongo il grafo…').waitFor();
  assert.deepEqual([await thing('web').count(), await canvas.getByRole('button', { name: /, pass[oi] \d/ }).count(), await busy.count()], [1, 0, 1]);
  await page.evaluate(() => { window.holdLayout = false; window.heldLayout(); });
  await line('Dispongo il grafo…').waitFor({ state: 'detached' });
  await flowPanel.getByRole('heading', { name: 'pay', exact: true }).waitFor();
  assert.deepEqual([await current(pay), await pay.getAttribute('aria-pressed'), await current(whole)], ['page', null, null]);
  const steps = flowPanel.getByRole('list', { name: 'Passi del flusso', exact: true }).getByRole('listitem');
  assert.equal(await steps.count(), 8);
  assert.match(await steps.first().innerText(), /1\. pay chiama apiPost[\s\S]*web\/checkout\.tsx:12 · diretto/);
  assert.ok(await selectable(steps.first().getByText('web/checkout.tsx:12', { exact: false })));
  await page.keyboard.press('Escape');  // closing leaves the flow chosen, and its place shows its steps again
  await flowPanel.waitFor({ state: 'hidden' });
  assert.equal(await current(pay), 'page');
  // On the canvas its nodes have the numbers of its steps, and its lines are a kind of their own.
  await thing('web, passi 1 e 2').waitFor();  // every step a node has a part in
  await thing('server, passi 2, 3, 4, 5, 6, 7 e 8').waitFor();
  await thing('card payment provider, passo 5').waitFor();
  await kindOfLine('Linee del flusso').waitFor();
  assert.match(await kindOfLine('Linee del flusso').innerText(), /Linee del flusso\s*4/);
  // Asked for again, what it goes through comes back into the view it was moved out of.
  await panAway();
  await comes('web, passi 1 e 2', false);
  await pay.click();
  await flowPanel.waitFor();
  await comes('web, passi 1 e 2');
  await comes('card payment provider, passo 5');
  // With a group open its steps are on what it holds.
  await opens('web').click();
  await frame('web').waitFor();
  await thing('checkout.tsx, passo 1').waitFor();
  await thing('api.ts, passi 1 e 2').waitFor();
  await closes('web').click();
  await thing('web, passi 1 e 2').waitFor();
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
  await thing('web, contiene 3 elementi').waitFor();
  await kindOfLine('Linee del flusso').waitFor({ state: 'detached' });
  // What is chosen in the list is brought into the view of the canvas; where it is in it already, the view stays.
  await panAway();
  await comes('card payment provider', false);
  await row(/^card payment provider/).click();
  await details.getByRole('heading', { name: 'card payment provider', exact: true }).waitFor();
  await canvas.getByRole('button', { name: 'card payment provider, esterno, servizio o API', exact: true }).waitFor();
  await comes('card payment provider');
  await rest();
  await canvas.getByRole('button', { name: 'Riduci', exact: true }).click();
  await rest();
  assert.ok(await inSight('card payment provider'));
  const seen = await viewAt('card payment provider');
  await row(/^card payment provider/).click();
  await frames(20);
  await rest();
  assert.deepEqual(await viewAt('card payment provider'), seen);
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
  // A group is entered by the inspector's action, by its row's own control, or by a double press; «Su» goes back.
  const still = async () => {  // once nothing slides
    const places = async () => [(await view('Logica').boundingBox()).x, (await up.boundingBox()).x, (await infoButton.boundingBox()).x];
    let last = [];
    await until(async () => {
      const now = await places(), same = now.join() === last.join();
      last = now;
      if (!same) await frames(15);
      return same;
    }, 'the controls at rest');
    return last;
  };
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
  await details.getByRole('heading', { name: 'checkout.tsx', exact: true }).waitFor();  // what was left is chosen, and in sight
  await comes('checkout.tsx');
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
  assert.equal(await canvas.count(), 0);
  assert.ok(await main.getByRole('button', { name: 'Azzera filtri (8 nascosti)' }).isEnabled());
  await main.getByRole('button', { name: 'Azzera filtri', exact: true }).click();
  await main.getByText('Nessun elemento visibile.').waitFor({ state: 'detached' });
  await thing('web').waitFor();
  assert.equal(await search.inputValue(), '');
  // The type: its choices are those of the view, whatever the search hides, and the chosen one stays said.
  const kind = main.getByRole('combobox', { name: 'Tipo di entità' });
  await kind.click();
  await page.getByRole('option', { name: 'componente', exact: true }).click();
  await place('Sistema').filter({ hasText: '2 nodi' }).waitFor();
  await thing('Cliente').waitFor({ state: 'detached' });
  await thing('server').waitFor();
  await search.fill('zzzz');
  await main.getByText('Nessun elemento visibile.').waitFor();
  assert.match(await kind.innerText(), /componente/);
  await kind.click();
  await page.getByRole('option', { name: 'dato', exact: true }).waitFor();
  assert.deepEqual((await page.getByRole('option').allInnerTexts()).map(text => text.trim()), ['Tutti i tipi', 'componente', 'esterno', 'dato']);
  await page.waitForFunction(() => document.activeElement?.closest('[role="listbox"]'));  // the list has the keys once it is open
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
  // Its button is at the head, with the name of the list and its count, and the choice is kept.
  const head = nav.getByText(/^Mappa\s*8/);
  const smaller = page.getByRole('button', { name: 'Riduci la barra laterale' });
  assert.ok((await smaller.boundingBox()).y < (await whole.boundingBox()).y);
  await head.waitFor();
  await smaller.click();
  await page.getByRole('button', { name: 'Espandi la barra laterale' }).waitFor();
  await page.waitForFunction(() => document.querySelector('nav[aria-label="Mappa"]').getBoundingClientRect().width < 100);
  assert.equal(await page.evaluate(() => localStorage.getItem('daodan.sidebar')), 'collapsed');
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
  // The ranks go down where the sidebar is the rail, and along where it is whole.
  const ranks = async () => {
    const [from, to] = await Promise.all(['Terminale POS', 'server'].map(name => thing(name).boundingBox()));
    return to.y > from.y + from.height ? 'down' : to.x > from.x + from.width ? 'right' : '';
  };
  await thing('Terminale POS').waitFor();
  await until(async () => await ranks() === 'down', 'the ranks down');
  await page.setViewportSize({ width: 900, height: 820 });  // the inspector covers the end of the content, not modal
  await until(async () => await ranks() === 'right', 'the ranks along');
  await infoButton.click();
  const overlay = page.getByRole('dialog', { name: 'Informazioni sul progetto' });
  await overlay.waitFor();
  await closeIn(overlay);
  await overlay.waitFor({ state: 'detached' });
  const sheet = page.getByRole('dialog', { name: 'Dettaglio' });
  await thing('web').waitFor();
  await busy.waitFor({ state: 'detached' });
  await thing('web').click();
  await sheet.waitFor();
  await closeIn(sheet);
  await sheet.waitFor({ state: 'detached' });
  await page.setViewportSize({ width: 390, height: 820 });  // the sidebar is a drawer, and the views are at the foot
  const drawer = page.getByRole('dialog', { name: 'Mappa' });
  await page.getByRole('button', { name: 'Apri il menu' }).click();
  await drawer.getByRole('button', { name: /^web/ }).waitFor();
  await page.keyboard.press('Escape');
  await drawer.waitFor({ state: 'detached' });
  await page.getByRole('button', { name: 'Apri il menu' }).click();  // an element chosen there closes it and shows its details
  await drawer.getByRole('button', { name: /^web/ }).click();
  await drawer.waitFor({ state: 'detached' });
  await sheet.waitFor();
  await closeIn(sheet);
  await sheet.waitFor({ state: 'detached' });
  assert.ok((await canvas.boundingBox()).height >= 200);
  const footViews = page.getByRole('toolbar', { name: 'Viste', exact: true });
  assert.equal(await view('Logica').count(), 1);
  await footViews.getByRole('button', { name: 'Fisica' }).click();
  await page.getByRole('main', { name: 'Mappa fisica' }).waitFor();
  await footViews.getByRole('button', { name: 'Logica' }).click();
  await page.getByRole('main', { name: 'Mappa logica' }).waitFor();
  assert.ok(await fits());
  await page.setViewportSize({ width: 1280, height: 850 });

  // Another export, chosen or dropped, takes the place of the map; a file that holds none says why, and the map stays.
  const opener = page.getByRole('dialog', { name: 'Apri altro export' });
  const zone = opener.getByRole('button', { name: 'Trascina qui un export, o scegli il file' });
  const problem = text => opener.getByRole('alert').filter({ hasText: text });
  const exported = id => JSON.stringify({ ...envelope, meta: { ...envelope.meta, run_id: id } });
  const give = async (name, mimeType, text) => {
    const [chooser] = await Promise.all([page.waitForEvent('filechooser'), zone.click()]);
    await chooser.setFiles({ name, mimeType, buffer: Buffer.from(text) });
  };
  await openOther.click();
  await opener.waitFor();
  await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label')?.startsWith('Trascina qui'));
  await give('mappa.png', 'image/png', 'x');
  await problem('Serve un file JSON.').waitFor();
  await give('altro.json', 'application/json', '{"schema":"altro"}');
  await problem('altro.json non è un export leggibile: schema sconosciuto: altro').waitFor();
  await give('rotto.json', 'application/json', 'not json');
  await problem('rotto.json non è un export leggibile: non è JSON').waitFor();
  await page.keyboard.press('Escape');
  await opener.waitFor({ state: 'detached' });
  await line('shop · run fixture').waitFor();
  await openOther.click();
  await opener.waitFor();
  assert.equal(await opener.getByRole('alert').count(), 0);
  await give('scelto.json', 'application/json', exported('scelto'));
  await opener.waitFor({ state: 'detached' });
  await line('shop · run scelto · dal file scelto.json').waitFor();
  await thing('web').waitFor();
  await page.waitForFunction(() => document.activeElement?.textContent === 'Apri altro export');  // the focus goes back
  await openOther.click();
  await opener.waitFor();
  const dropped = await page.evaluateHandle(text => {
    const data = new DataTransfer();
    data.items.add(new File([text], 'lasciato.json', { type: 'application/json' }));
    return data;
  }, exported('lasciato'));
  await zone.dispatchEvent('drop', { dataTransfer: dropped });
  await opener.waitFor({ state: 'detached' });
  await line('shop · run lasciato').waitFor();

  let runsBusy = 1;  // a busy project has runs all the same: its page does not fall back on a static export
  await context.route('**/api/runs', route => {
    runsBusy -= 1;
    return route.fulfill(runsBusy < 0 ? { json: { runs: [] } } : { status: 503, json: { error: 'project lock is held by another helper' } });
  });
  const asks = { refused: 'progetto occupato', held: null };
  await context.route('**/api/requests', async route => {
    if (asks.held) await asks.held.promise;
    return route.fulfill(asks.refused ? { status: 500, json: { error: asks.refused } } : { json: { requests: [] } });
  });
  let findingsBusy = 1;
  await context.route('**/api/findings', route => {
    findingsBusy -= 1;
    return route.fulfill(findingsBusy < 0 ? { json: { findings: [], gaps: [] } } : { status: 503, json: { error: 'project lock is held by another helper' } });
  });
  await page.reload();
  const noRuns = main.getByText('Creane uno qui sotto, o avvia una mappa nella sessione.');
  await page.getByText('Daodan è occupato, riprovo', { exact: true }).waitFor();
  await main.getByRole('progressbar', { name: "Carico l'export…" }).waitFor();
  await noRuns.waitFor();
  await line('Nessun run').waitFor();
  await nav.getByText('Nessuna mappa: non ci sono run.').waitFor();
  await page.keyboard.press('Control+f');  // no map, no search
  await page.getByText('Questa vista non ha una ricerca.').waitFor();
  // With no run the session is in sight under the words that say so, and its form makes the first run.
  const session = main.getByRole('region', { name: 'Sessione e review', exact: true });
  // Each list is asked by itself: one that is not read says so and can be asked again, beside one that is.
  await session.getByRole('progressbar', { name: 'Carico i finding…' }).waitFor();  // a busy one is no failure
  await session.getByText('Nessun finding: compaiono quando la sessione chiude una review.').waitFor();
  const listOf = name => session.getByRole('region', { name: new RegExp(`^${name}\\b`) });
  const unread = name => listOf(name).getByRole('alert');
  await unread('Richieste').waitFor();
  assert.match(await unread('Richieste').innerText(), /Errore[\s\S]*Richieste non lette[\s\S]*progetto occupato[\s\S]*Riprova/);
  Object.assign(asks, { refused: '', held: Promise.withResolvers() });
  await unread('Richieste').getByRole('button', { name: 'Riprova' }).click();
  await listOf('Richieste').getByRole('progressbar', { name: 'Carico le richieste…' }).waitFor();
  asks.held.resolve();
  await session.getByText('Nessuna richiesta.').waitFor();
  assert.ok((await session.boundingBox()).y > (await noRuns.boundingBox()).y);
  assert.ok(await openOther.isDisabled());
  // Where the controls are, in the header and, on a tighter window, with the filters: nothing moves when the choice of the run comes.
  const controls = async () => {
    const places = [];
    for (const width of [1100, 1280]) {
      await page.setViewportSize({ width, height: 850 });
      await infoButton.filter({ hasText: width < 1200 ? /^Informazioni$/ : /progetto$/ }).waitFor();
      for (const control of [openOther, up]) { const { x, y } = await control.boundingBox(); places.push(Math.round(x), Math.round(y)); }
    }
    return places;
  };
  const withNoRun = await controls();
  const server = { runs: [], posted: [], refuses: 'run già presente', held: Promise.withResolvers() };
  await context.route('**/api/runs', async route => {
    if (route.request().method() === 'GET') return route.fulfill({ json: { runs: server.runs } });
    server.posted.push(route.request().postDataJSON());
    await server.held.promise;
    return route.fulfill(server.refuses ? { status: 400, json: { error: server.refuses } } : { json: {} });
  });
  const said = text => session.getByRole('alert').filter({ hasText: text });  // what a form says is wrong, or the server refuses
  const runName = session.getByRole('textbox', { name: 'Nome del run' });
  const create = session.getByRole('button', { name: 'Crea il run', exact: true });
  await create.click();  // a name is needed, as the server takes it
  await said('Scrivi il nome del run.').waitFor();
  assert.ok(await focused(runName));
  await runName.fill('Primo Run');
  await said('Scrivi il nome del run.').waitFor({ state: 'detached' });
  await create.click();
  await said('Solo minuscole, cifre e trattini').waitFor();
  assert.deepEqual(server.posted, []);
  await runName.fill('primo-run');
  await create.click();
  await create.and(page.locator('[aria-busy="true"]')).waitFor();
  await runName.press('Enter');  // a form that is sending is not sent again
  server.held.resolve();
  await said('Richiesta non riuscita').waitFor();
  assert.match(await said('Richiesta non riuscita').innerText(), /Errore[\s\S]*Richiesta non riuscita[\s\S]*run già presente/);
  assert.deepEqual([server.posted, await runName.inputValue()], [[{ target: '.', run_id: 'primo-run' }], 'primo-run']);
  Object.assign(server, { refuses: '', runs: [{ run_id: 'primo-run', readable: true }] });
  await create.click();
  await line('shop · run fixture').waitFor();
  assert.match(await main.getByRole('combobox', { name: 'Run' }).innerText(), /Run primo-run/);
  assert.deepEqual(await controls(), withNoRun);
  assert.equal(await session.count(), 0);  // over a map it is behind its row
  await context.route('**/api/runs', route => route.fulfill({ json: { runs: [{ run_id: 'prima', readable: true }, { run_id: 'rotto', readable: false }, { run_id: 'demo', readable: true }] } }));
  await context.route('**/api/events?*', route => route.fulfill({ json: { events: [{ cursor: 1, timestamp: '10:00', event: 'phase_completed', message: 'fatto', phase: 2 }], next_cursor: 1, has_more: false } }));
  mode.exportBroken = true;  // a run in progress has no readable export yet: its live event line shows all the same
  await page.reload();
  await main.getByRole('alert').waitFor();
  await line('10:00 · Fase completata · fase 2 · fatto').waitFor();
  mode.exportBroken = false;
  const results = { refused: 'risultati occupati', held: Promise.withResolvers() };
  await context.route('**/api/findings', async route => {
    await results.held.promise;
    return route.fulfill(results.refused ? { status: 500, json: { error: results.refused } } : { json: {
      findings: [{ file: 'web/checkout.tsx', line: 12, severity: 'High', title: 'Premessa', request: 1 }, { severity: 'Low', title: 'Senza file', request: 1 }],
      gaps: ['lacuna della sessione'],
    } });
  });
  await page.reload();
  await line('10:00 · Fase completata · fase 2 · fatto').waitFor();
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
  // An export opened there stays until a run is chosen, also the one it took the place of: a phase that ends, here at every poll,
  // does not take it away, and what happens in the run is not said beside it.
  await line('Fase completata').waitFor();
  await openOther.click();
  await opener.waitFor();
  await give('aperto.json', 'application/json', exported('aperto'));
  await opener.waitFor({ state: 'detached' });
  await line('shop · run aperto · dal file aperto.json').waitFor();
  assert.match(await runPicker.innerText(), /File aperto/);
  await page.waitForTimeout(2500);
  assert.deepEqual([await line('shop · run aperto · dal file aperto.json').count(), await line('Fase completata').count()], [1, 0]);
  await runPicker.click();
  await page.getByRole('option', { name: 'Run prima', exact: true }).click();
  await line('Fase completata').waitFor();
  await line('shop · run fixture').waitFor();
  assert.equal(await line('dal file').count(), 0);
  assert.match(await runPicker.innerText(), /Run prima/);

  // The session and its review, behind their row: drawn, and asked of the server, only while it is open.
  const requests = [];
  let polls = 0;
  page.on('request', request => { if (new URL(request.url()).pathname === '/api/findings') polls += 1; });
  await context.route('**/api/requests', route => {
    if (route.request().method() === 'GET') return route.fulfill({ json: { requests } });
    if (server.refuses) return route.fulfill({ status: 400, json: { error: server.refuses } });
    requests.push({ id: requests.length + 1, state: 'pending', ...route.request().postDataJSON() });
    return route.fulfill({ json: {} });
  });
  const sessionRow = main.getByRole('button', { name: 'Sessione e review', exact: true });
  await page.waitForTimeout(2500);
  assert.deepEqual([await sessionRow.getAttribute('aria-expanded'), await session.count(), polls], ['false', 0, 0]);
  await sessionRow.press('Enter');
  await session.getByText('Nessuna richiesta.').waitFor();
  assert.equal(await sessionRow.getAttribute('aria-expanded'), 'true');
  // A route that has not answered yet is not asked again; one that fails at first says so, and the next poll reads it.
  await listOf('Finding').getByRole('progressbar', { name: 'Carico i finding…' }).waitFor();
  await page.waitForTimeout(2500);
  assert.equal(polls, 1);
  results.held.resolve();
  await unread('Finding').waitFor();
  assert.match(await unread('Finding').innerText(), /Finding non letti[\s\S]*risultati occupati/);
  results.refused = '';
  await session.getByRole('heading', { name: 'Finding · 2', exact: true }).waitFor();
  // A request: what it asks, the text a feature needs, what the server refuses, and its state as the session moves it.
  const scope = session.getByRole('combobox', { name: 'Perimetro' });
  const send = session.getByRole('button', { name: 'Invia', exact: true });
  assert.match(await session.getByRole('combobox', { name: 'Cosa' }).innerText(), /Review/);
  assert.match(await scope.innerText(), /Changeset/);
  await session.getByRole('textbox', { name: 'Indicazioni' }).waitFor();
  await scope.click();
  await page.getByRole('option', { name: 'Funzionalità', exact: true }).click();
  const feature = session.getByRole('textbox', { name: 'Funzionalità' });
  await send.click();
  await said('Scrivi il nome della funzionalità.').waitFor();
  assert.deepEqual([requests, await focused(feature)], [[], true]);
  await feature.fill('Pagamenti');
  server.refuses = 'troppe richieste aperte';
  await send.click();
  await said('troppe richieste aperte').waitFor();
  assert.equal(await feature.inputValue(), 'Pagamenti');
  server.refuses = '';
  await send.click();
  await session.getByRole('heading', { name: 'Richieste · 1', exact: true }).waitFor();
  assert.deepEqual(requests, [{ id: 1, state: 'pending', kind: 'review', scope: 'feature', text: 'Pagamenti' }]);
  assert.equal(await feature.inputValue(), '');
  const request = session.getByRole('list', { name: 'Richieste', exact: true }).getByRole('listitem');
  assert.match(await request.innerText(), /#1 Review · Funzionalità[\s\S]*in attesa della sessione[\s\S]*Pagamenti/);
  Object.assign(requests[0], { state: 'done', message: 'Un finding' });
  await request.filter({ hasText: 'Un finding' }).filter({ hasText: 'conclusa' }).waitFor();
  assert.deepEqual([await request.getByRole('button').count(), await selectable(request.getByText('Pagamenti'))], [0, true]);  // to read and copy
  // The session's gaps are a note that is not announced; a finding says its severity and selects its file.
  await session.getByText('Lacune · 1').waitFor();
  await session.getByText('lacuna della sessione').waitFor();
  assert.equal(await main.getByRole('alert').count(), 0);
  const findings = session.getByRole('list', { name: 'Finding', exact: true });
  const unplaced = findings.getByRole('listitem').filter({ hasText: 'Senza file' });  // it goes nowhere: to read and copy
  assert.match(await unplaced.innerText(), /file non indicato[\s\S]*gravità bassa[\s\S]*Senza file/);
  assert.deepEqual([await unplaced.getByRole('button').count(), await selectable(unplaced.getByText('Senza file'))], [0, true]);
  const finding = findings.getByRole('button', { name: /gravità alta/ });
  assert.match(await finding.innerText(), /web\/checkout\.tsx:12[\s\S]*Premessa[\s\S]*gravità alta/);
  // Wherever the view is, the node that stands for the file is brought into it.
  const zoomIn = () => canvas.getByRole('button', { name: 'Ingrandisci', exact: true }).click();
  await row(/^card payment provider/).click();
  await details.getByRole('heading', { name: 'card payment provider', exact: true }).waitFor();
  await panAway();
  await comes('web', false);
  await finding.click();
  await details.getByRole('heading', { name: 'checkout.tsx', exact: true }).waitFor();
  await comes('web');
  await thing('web').and(page.locator('[aria-current="true"]')).waitFor();
  // One solid button in the whole page, the forms of the session in sight: the «Entra» of the details.
  const enter = details.getByRole('button', { name: 'Entra in checkout.tsx', exact: true });
  const fill = await enter.evaluate(el => getComputedStyle(el).backgroundColor);
  const solid = (buttons, color) => buttons.filter(el => getComputedStyle(el).backgroundColor === color).map(el => el.getAttribute('aria-label') ?? el.textContent);
  assert.deepEqual(await page.getByRole('button').evaluateAll(solid, fill), ['Entra in checkout.tsx']);
  // Where the canvas draws no node of the file, the file is chosen and the view stays as the person left it.
  await row('Entra in server').click();
  await place('Sistema / server').waitFor();
  await row(/^routes\.ts/).click();
  await details.getByRole('heading', { name: 'routes.ts', exact: true }).waitFor();
  await comes('routes.ts');
  await rest();  // the canvas has its width beside the details
  await zoomIn();
  await rest();
  const left = await viewAt('routes.ts');
  await finding.click();
  await details.getByRole('heading', { name: 'checkout.tsx', exact: true }).waitFor();
  await frames(20);
  await rest();
  assert.deepEqual(await viewAt('routes.ts'), left);
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await sessionRow.press('Enter');
  await session.waitFor({ state: 'detached' });
  const pollsAtClose = polls;
  await page.waitForTimeout(2500);
  assert.equal(polls, pollsAtClose);

  // The theme the person picks on one page is followed live by the other one (the storage event).
  await choose('Tema chiaro');
  await schemeIs(page, 'light');
  const tab = await context.newPage(), app = await context.newPage();
  const withToken = tab.waitForRequest(request => request.url().endsWith('/api/mark?id=stripe&token=prova'));  // a logo is asked for with the page's token
  await tab.goto('http://daodan.test/?token=prova');
  await withToken;
  await schemeIs(tab, 'light');
  await app.goto('http://daodan.test/app/?token=test');
  await schemeIs(app, 'light');
  await page.bringToFront();
  await choose('Tema scuro');
  await schemeIs(tab, 'dark');
  await schemeIs(app, 'dark');
  await app.bringToFront();
  await app.keyboard.press('Control+k');
  await app.getByRole('dialog', { name: 'Cerca un comando' }).getByRole('option', { name: 'Tema chiaro' }).click();
  await schemeIs(page, 'light');
  await tab.close();
  await app.close();
  // In a browser the map opens in a tab of its own, with no way back; in a window the two pages take each other's place.
  const says = "Torna all'analisi";
  await page.goto('http://daodan.test/app/?token=test');
  await page.getByRole('toolbar', { name: 'Daodan', exact: true }).getByRole('button', { name: /^Grafo/ }).click();
  const [popup] = await Promise.all([page.waitForEvent('popup'), page.getByRole('link', { name: 'Apri l’esploratore', exact: true }).click()]);
  await popup.getByRole('main', { name: 'Mappa logica' }).waitFor();
  assert.deepEqual([new URL(page.url()).pathname, popup.url(), await popup.getByRole('button', { name: says }).count()], ['/app/', 'http://daodan.test/?token=test&run=demo', 0]);
  await popup.close();
  // The window of Tauri as the page finds it: it answers every call, and writes it down.
  const fakeWindow = () => {
    window.calls = [];
    window.__TAURI_INTERNALS__ = {
      metadata: { currentWindow: { label: 'main' }, currentWebview: { label: 'main', windowLabel: 'main' } },
      transformCallback: () => 1, unregisterCallback: () => {},
      invoke: async (command, args) => {
        window.calls.push([command, args]);
        return command === 'plugin:window|is_maximized' ? false : command === 'plugin:event|listen' ? 1 : null;
      },
    };
    window.__TAURI_EVENT_PLUGIN_INTERNALS__ = { unregisterListener: () => {} };
  };
  Object.assign(mode, { graphStatus: 200, premapStatus: 200, premapDelay: 0, exportBroken: false, exportDelay: 0, exportBusy: 0, layoutLost: false, pathsBroken: false, marks: true });
  // A page of its own, with the choices it starts from.
  const opened = async ({ width, scheme = 'dark', own = false }) => {
    const other = await browser.newContext({ viewport: { width, height: 850 }, colorScheme: 'light' });
    await other.route('http://daodan.test/**', respond);
    await other.route('**/api/runs', route => route.fulfill({ json: { runs: [{ run_id: 'demo', readable: true }] } }));
    await other.route('**/api/events?*', route => route.fulfill({ json: { events: [{ cursor: 1, timestamp: '10:00', event: 'phase_completed', message: '', phase: 2 }], next_cursor: 1, has_more: false } }));
    const tabPage = await other.newPage();
    tabPage.setDefaultTimeout(8000);
    tabPage.on('pageerror', error => { errors.push(error.message); console.error(error); });
    await tabPage.addInitScript(stream, fresh);
    await tabPage.addInitScript(choice => { if (!localStorage.getItem('daodan.theme')) localStorage.setItem('daodan.theme', choice); }, scheme);
    if (own) await tabPage.addInitScript(fakeWindow);
    return tabPage;
  };
  {
    const win = await opened({ width: 1280, own: true });
    const told = () => win.evaluate(() => window.calls.filter(([command]) => command === 'plugin:imago-shell|chrome').map(([, args]) => args.title));
    const until = async (holds, what) => { for (const end = Date.now() + 8000; !await holds(); await win.waitForTimeout(50)) assert.ok(Date.now() < end, what); };
    const buttons = () => win.locator('[data-slot="window-controls"]').getByRole('button').evaluateAll(all => all.map(el => el.getAttribute('aria-label')));
    const bar = win.getByRole('toolbar', { name: 'Daodan', exact: true });
    const toMap = async () => {
      const link = win.getByRole('link', { name: 'Apri l’esploratore', exact: true });
      assert.equal(await link.getAttribute('target'), null);
      await link.click();
      await win.getByRole('main', { name: 'Mappa logica' }).waitFor();
      assert.equal(win.url(), 'http://daodan.test/?token=test&run=demo');
    };
    const onGraph = async () => {
      await win.waitForURL('http://daodan.test/app/?token=test');
      await win.getByRole('main', { name: 'Grafo', exact: true }).waitFor();  // the screen it was left on
    };
    await win.goto('http://daodan.test/app/?token=test');
    await bar.getByRole('button', { name: /^Analisi/ }).waitFor();
    assert.deepEqual(await buttons(), ['Riduci a icona', 'Ingrandisci', 'Chiudi']);
    await until(async () => (await told()).at(-1) === 'Daodan · Analisi', 'the title of the App');
    await bar.getByRole('button', { name: /^Grafo/ }).click();
    await toMap();
    assert.deepEqual(await buttons(), ['Riduci a icona', 'Ingrandisci', 'Chiudi']);
    await until(async () => (await told()).at(-1) === 'Daodan · Mappa', 'the title of the map');
    await bar.getByRole('button', { name: says, exact: true }).click();
    await onGraph();
    await toMap();
    await win.keyboard.press('Control+k');
    await win.getByRole('dialog', { name: 'Cerca un comando' }).getByRole('option', { name: says }).click();
    await onGraph();
    // The run has the link too.
    await win.evaluate(() => localStorage.setItem('daodan-app-v2', JSON.stringify({ ...JSON.parse(localStorage.getItem('daodan-app-v2')), screen: 'analysis', analysisStage: 'analysis' })));
    await win.reload();
    await win.getByRole('region', { name: 'Analisi', exact: true }).waitFor();
    await toMap();
    assert.equal(win.context().pages().length, 1);
    await win.context().close();
  }

  {
    // Both pages at the widths where the frame changes and in both schemes: nothing sticks out sideways, the views are where the width
    // puts them, and the bar is the same from one screen to the next. A photograph of each, for who looks at them.
    const shots = new URL('./shots/', import.meta.url);
    await rm(shots, { recursive: true, force: true });
    await mkdir(shots, { recursive: true });
    const still = async where => {
      await where.evaluate(() => Promise.race([
        Promise.all(document.getAnimations().map(({ finished }) => finished.catch(() => {}))), new Promise(done => setTimeout(done, 1000)),
      ]).then(() => {}));
      await where.waitForTimeout(300);  // the frame and the canvas take their width
    };
    const sticksOut = where => where.evaluate(() => {
      const out = [];
      if (document.documentElement.scrollWidth > innerWidth) out.push(`the page is ${document.documentElement.scrollWidth} wide in ${innerWidth}`);
      for (const slot of ['title-bar', 'app-shell-tabs', 'app-shell-status', 'sidebar', 'app-shell-content', 'app-shell-actions', 'app-shell-footer', 'app-shell-bottom', 'panel-header', 'panel-tools', 'panel-body', 'inspector-body', 'inspector-footer']) {
        for (const region of document.querySelectorAll(`[data-slot="${slot}"]`)) {
          if (region.clientWidth > 1 && region.scrollWidth > region.clientWidth) out.push(`${slot} is ${region.scrollWidth} wide in ${region.clientWidth}`);
        }
      }
      for (const slot of ['app-shell-status', 'app-shell-footer', 'title-bar']) {
        const tall = document.querySelector(`[data-slot="${slot}"]`)?.clientHeight ?? 0;
        if (tall > 48) out.push(`${slot} is ${tall} tall: more than a line`);
      }
      return out;
    });
    const barOf = async where => {
      const box = async locator => { const found = await locator.boundingBox(); return found && [found.x, found.width].map(Math.round); };
      return { brand: await box(where.locator('[data-slot="toolbar-brand"]')), commands: await box(where.locator('[data-slot="title-bar"]').getByRole('button', { name: /^Comandi/ })) };
    };
    const WIDTHS = [340, 390, 620, 860, 1440], SHOT = [390, 620, 1440];
    const from = { screen: 'analysis', runId: 'demo', repositoryUrl: 'https://github.com/demo/shop' };
    const SCREENS = [
      ['analisi-1-repository', { ...from, analysisStage: 'repository' }, 'Repository'],
      ['analisi-2-premappa', { ...from, analysisStage: 'premap', treeSelected: 'README.md' }, 'Pre-mappa'],
      ['analisi-3-run', { ...from, analysisStage: 'analysis' }, 'Analisi'],
      ['analisi-4-sintesi', { ...from, analysisStage: 'synthesis' }, 'Sintesi'],
      ['grafo', { ...from, screen: 'graph' }, 'Grafo del codice'],
      ['motore', { ...from, screen: 'engine' }, 'Motore e domande'],
    ];
    const MAPS = [
      ['mappa-logica', 'Vista logica', null], ['mappa-fisica', 'Vista fisica', null],
      ['mappa-logica-progetto', 'Vista logica', 'Informazioni sul progetto'],
    ];
    const wrong = [];
    for (const own of [false, true]) {
      for (const scheme of ['dark', 'light']) {
        const bars = {};
        const look = async (where, name) => {
          for (const width of own ? [620, 1440] : WIDTHS) {
            await where.setViewportSize({ width, height: 850 });
            await still(where);
            const label = `${own ? 'finestra-' : ''}${name}-${scheme}-${width}`;
            if (SHOT.includes(width)) await where.screenshot({ path: new URL(`${label}.png`, shots).pathname });
            const out = await sticksOut(where);
            if (out.length) wrong.push(`${label}: ${out.join('; ')}`);
            const form = width >= 860 ? 'title-bar' : width < 620 && !own ? 'app-shell-bottom' : 'app-shell-tabs';
            if (await where.locator(`[data-slot="${form}"] [data-slot="toolbar-tabs"]`).count() !== 1) wrong.push(`${label}: the views are not in ${form}`);
            if (await where.evaluate(() => document.documentElement.dataset.scheme) !== scheme) wrong.push(`${label}: not ${scheme}`);
            // Under 620 the map has the button of its drawer before the brand.
            const now = await barOf(where);
            if (width < 620) delete now.brand;
            bars[width] ??= JSON.stringify(now);
            if (JSON.stringify(now) !== bars[width]) wrong.push(`${label}: the bar is ${JSON.stringify(now)}, and was ${bars[width]}`);
          }
        };
        const shown = await opened({ width: 1440, scheme, own });
        for (const [name, state, title] of SCREENS) {
          await shown.setViewportSize({ width: 1440, height: 850 });
          await shown.goto('http://daodan.test/app/?token=test');
          await shown.evaluate(left => localStorage.setItem('daodan-app-v2', JSON.stringify(left)), state);
          await shown.reload();
          await shown.getByRole('region', { name: title, exact: true }).waitFor();
          await shown.waitForFunction(() => !document.querySelector('main [aria-busy="true"]'));
          await look(shown, name);
        }
        await shown.setViewportSize({ width: 1440, height: 850 });
        await shown.goto('http://daodan.test/?token=test');
        for (const [name, command, then] of MAPS) {
          await shown.setViewportSize({ width: 1440, height: 850 });
          for (const each of [command, then].filter(Boolean)) {
            await shown.keyboard.press('Control+k');
            await shown.getByRole('dialog', { name: 'Cerca un comando' }).getByRole('option', { name: each }).click();
          }
          await shown.getByRole('group', { name: 'Naviga il grafo', exact: true }).waitFor();
          await shown.waitForFunction(() => !document.querySelector('main [aria-busy="true"]'));
          await look(shown, name);
        }
        await shown.setViewportSize({ width: 1440, height: 850 });
        await shown.keyboard.press('Control+k');
        await still(shown);
        if (!own) await shown.screenshot({ path: new URL(`palette-${scheme}-1440.png`, shots).pathname });
        await shown.context().close();
      }
    }
    assert.deepEqual(wrong, []);
  }
  assert.deepEqual(errors, []);
  console.log('Passed the App (frame, palette, stages, repository, graph, server, theme) and the map (frame, palette, canvas, groups in place, moves, motion, logos, places and things, details, filters, runs, theme).');
} finally { await browser.close(); }
