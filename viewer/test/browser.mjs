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
const engineRequests = [], askRequests = [], checkRequests = [], selectRequests = [];
const mode = { graphStatus: 200, premapDelay: 0, linkStatus: 200, checkDelay: 0, selectRefused: '', exportBroken: false, exportDelay: 0, layoutLost: false };
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
    if (mode.layoutLost && path.includes('layout.worker')) return route.fulfill({ body: '', contentType: 'text/javascript' });  // it never answers
    const app = path.startsWith('/app/');
    const part = path.slice(app ? 5 : 1) || 'index.html';
    const mime = { html: 'text/html', css: 'text/css', js: 'text/javascript' }[part.split('.').at(-1)];
    await route.fulfill({ body: await readFile(new URL((app ? 'app/' : 'viewer/') + part, assets)), contentType: mime });
  });
  await page.addInitScript(state => {
    window.EventSource = class extends EventTarget {
      constructor() {
        super();
        const send = (name, frame) => this.dispatchEvent(new MessageEvent(name, { data: JSON.stringify(frame) }));
        const publish = frame => send('app', frame);
        window.setMapState = mapped => publish({ ...state, mapped });
        window.setServerState = patch => publish({ ...state, ...patch });
        window.failServer = error => send('failure', { error });
        setTimeout(() => publish(state), 0);
      }
      close() {}
    };
  }, { context: run, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: { engine: 'claude', engines: ['claude'] }, links: { state: 'idle' } });
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
  const fits = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
  const focused = locator => locator.evaluate(el => el === document.activeElement);
  const main = page.getByRole('main');
  const line = text => page.getByRole('status').filter({ hasText: text });  // the status row, and what it says
  const inMain = () => page.evaluate(() => !!document.activeElement?.closest('main'));
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
    assert.equal(await page.getByRole('navigation').count(), 0);
    await line('Contesto pronto').waitFor();
    const where = line('Pipeline completata').getByText(`demo/shop · main · ${'1'.repeat(12)} · run demo`, { exact: true });
    await where.waitFor();
    assert.ok(await selectable(where));
    const foot = page.getByRole('contentinfo');
    assert.match(await foot.innerText(), /App locale: il codice resta sul tuo disco · Motore: claude/);
    const keys = await foot.getByRole('list', { name: 'Tasti' }).innerText();  // Ctrl+K is on its button
    assert.match(keys, /Ctrl\s*F[\s\S]*Cerca in questa vista[\s\S]*F6[\s\S]*Area successiva/);
    assert.doesNotMatch(keys, /Ctrl\s*K/);
    // The stages say how they are, and one that cannot be opened says why.
    assert.equal(await stage('Repository').getAttribute('aria-current'), 'true');
    for (const name of ['Repository', 'Pre-mappa', 'Analisi', 'Sintesi']) await stageSays(name, 'fatta');
    await serve({ context: null, job: { state: 'idle' } });
    await line('Nessuna repository').waitFor();
    await stageSays('Repository', 'da fare');
    for (const name of ['Pre-mappa', 'Analisi', 'Sintesi']) {
      await stageSays(name, 'Scegli prima una repository e un branch.');
      assert.ok(await stage(name).isDisabled());
    }
    await main.getByText('Nessuna repository selezionata sul server.').waitFor();
    await serve({ run: { pass: { state: 'running' } } });
    await stageSays('Analisi', 'in corso');
    await stageSays('Sintesi', 'La sintesi è pronta quando la pipeline è conclusa.');
    assert.ok(await stage('Sintesi').isDisabled());
    await line('Analisi in corso').filter({ hasText: '0%' }).waitFor();
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
    const first = page.getByText('Verifica prima l’accesso alla repository.', { exact: true });
    await first.waitFor();
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
    assert.equal(await first.count(), 0);
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
    await serve({});  // the context is ready: its pre-map opens, and its graph is read
    await page.getByText('Contesto pronto: demo/shop · main', { exact: true }).waitFor();
    await panel('Pre-mappa').waitFor();
    assert.equal(await stage('Pre-mappa').getAttribute('aria-current'), 'true');
    await tab('Grafo').filter({ hasText: '2 gruppi' }).waitFor();
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
    // The screens are places: by a press, by the arrows and Enter, by their commands.
    await tab('Grafo').click();
    await screen('Grafo');
    assert.deepEqual([await tab('Grafo').getAttribute('aria-current'), await tab('Analisi').getAttribute('aria-current')], ['page', null]);
    await tab('Grafo').press('ArrowLeft');
    await page.waitForFunction(() => document.activeElement?.textContent === 'Analisi');
    await page.keyboard.press('Enter');
    await screen('Analisi');
    await choose('Vai a Motore e domande');
    await screen('Motore e domande');
    await choose('Vai al Grafo');
    await screen('Grafo');
    await choose('Vai ad Analisi');
    await screen('Analisi');
    await panel('Pre-mappa').waitFor();  // the stage is where it was left
    // Ctrl+F on a screen with no search says so; F6 and Shift+F6 go from a region to the next; the skip link goes to the content.
    await page.keyboard.press('Control+f');
    await page.getByText('Questa schermata non ha una ricerca.').waitFor();
    await tab('Analisi').focus();
    await page.keyboard.press('F6');
    assert.ok(await inMain());
    await page.keyboard.press('Shift+F6');
    assert.ok(await tab('Analisi').evaluate(el => el.closest('header').contains(document.activeElement)));
    await page.getByRole('link', { name: 'Vai al contenuto' }).press('Enter');
    await page.waitForFunction(() => document.activeElement?.tagName === 'MAIN');
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
    assert.deepEqual([await tab('Analisi').isVisible(), await stage('Repository').isVisible(), await fits()], [true, true, true]);
    await page.setViewportSize({ width: 390, height: 820 });
    const footScreens = page.getByRole('toolbar', { name: 'Schermate in basso' });
    await footScreens.getByRole('button', { name: /^Motore/ }).click();
    await screen('Motore e domande');
    assert.equal(await tab('Analisi').count(), 0);
    assert.ok(await fits());
    await footScreens.getByRole('button', { name: /^Analisi/ }).click();
    await panel('Repository').waitFor();
    await path.waitFor({ state: 'hidden' });
    assert.ok(await fits());
    await main.getByRole('button', { name: 'Percorso', exact: true }).click();
    await stage('Pre-mappa').click();
    await panel('Pre-mappa').waitFor();
    await path.waitFor({ state: 'hidden' });
    assert.ok(await fits());
    await page.setViewportSize({ width: 1280, height: 850 });
    await path.waitFor();
  }

  // The contract of the screens not yet drawn, in Imago's selectors: each to restore by role and name, then delete from here.
  // ticket 20: the pre-map
  // mode.premapDelay = 1000;
  // await page.locator('#stage-premap').click();
  // await page.locator('[data-im-state-layer="loading"]').waitFor();
  // await page.getByRole('tree').waitFor();
  // mode.premapDelay = 0;
  // assert.ok(await selectable(page.locator('.im-table td strong', { hasText: 'left-pad' })));
  // const directories = page.getByRole('radio', { name: 'Directory', exact: true });
  // const units = page.getByRole('radio', { name: 'Unità tecniche' });
  // await directories.focus();
  // await directories.press('ArrowRight');
  // assert.ok(await units.isChecked());
  // assert.ok(await units.evaluate(el => document.activeElement === el));
  // await units.press('ArrowLeft');
  // assert.ok(await directories.isChecked());
  // assert.equal(await page.locator('.im-metric').count(), 4);
  // const tree = page.getByRole('tree');
  // await tree.getByRole('treeitem', { name: 'main.ts' }).press('Enter');
  // assert.match(await page.locator('#tree-selection').innerText(), /src\/main.ts/);
  // const provenance = page.getByRole('button', { name: 'Provenienza', exact: true });
  // await provenance.click();
  // const detail = page.getByRole('region', { name: 'Provenienza della pre-mappa' });
  // assert.ok(await detail.isVisible());
  // await page.keyboard.press('Escape');
  // assert.ok(await detail.isHidden());
  // assert.equal(await page.evaluate(() => document.activeElement?.textContent?.trim()), 'Provenienza');
  // ticket 21: the run and the synthesis
  // await tabs.getByRole('tab', { name: /^Analisi/ }).click();
  // await page.locator('#stage-analysis').click();
  // await page.locator('#preview-diagram .im-graph-node').first().waitFor();
  // assert.equal(await page.locator('#pipeline-steps li').count(), 6);
  // await page.waitForFunction(() => !document.querySelector('img.im-inline-mark'));  // the mark that does not load is the icon
  // assert.ok(await page.locator('#preview-diagram [data-im-node="Client"] .im-icon').count() > 0);
  // mode.linkStatus = 500;
  // await page.getByRole('button', { name: 'Trova i legami' }).click();
  // const linkError = page.locator('.im-notice', { hasText: 'collegamento non riuscito' });
  // await linkError.waitFor();
  // assert.match(await linkError.innerText(), /Errore/);
  // await page.waitForTimeout(6500);
  // assert.equal(await linkError.count(), 1);
  // await linkError.getByRole('button', { name: 'Chiudi' }).click();
  // assert.equal(await linkError.count(), 0);
  // const partialMap = { state: 'incomplete', cause: 'the recorded map still has stale or incomplete records',
  //   needs_review: { nodes: { count: 2, ids: ['a', 'b'] }, flows: { count: 1, ids: ['c'] },
  //     refused_proposals: { count: 1, ids: ['request:d'] } } };
  // await page.evaluate(mapped => window.setMapState(mapped), partialMap);
  // const notice = page.locator('#map-status .im-note');
  // await notice.getByText('Mappa del sistema parziale').waitFor();
  // assert.match(await notice.innerText(), /2 nodi, 1 flusso, 1 proposta rifiutata/);
  // assert.match(await notice.innerText(), /revisione precedente/);
  // await page.locator('#stage-synthesis').click();
  // const paths = page.getByRole('region', { name: 'Percorsi per ingresso' });
  // await paths.getByText('Nessun ingresso classificato per questo snapshot.').waitFor();
  // pathsClassified = true;
  // await page.evaluate(() => window.setMapState({ state: 'done', discovery: { count: 2 } }));
  // await paths.getByRole('button', { name: /Salva ordine/ }).click();
  // await paths.getByText('store:ordini', { exact: true }).waitFor();
  // await paths.getByText('Effetto', { exact: true }).waitFor();
  // await paths.getByRole('button', { name: 'Passaggi successivi' }).click();
  // await paths.getByText('Destinazione campionata', { exact: true }).waitFor();
  // assert.match(await paths.innerText(), /campionata dal profiler/);
  // await paths.getByRole('button', { name: 'Torna agli ingressi' }).click();
  // await paths.getByRole('button', { name: 'Ingressi successivi' }).click();
  // await paths.getByRole('button', { name: /Annulla ordine/ }).waitFor();
  // await paths.getByRole('button', { name: 'Ingressi precedenti' }).click();
  // await paths.getByRole('button', { name: 'Scritture senza ingresso' }).click();
  // await paths.getByText('store:registro', { exact: true }).waitFor();
  // assert.match(await paths.innerText(), /2 di 3 scritture/);
  // await paths.getByRole('button', { name: 'Scritture successive' }).click();
  // await paths.getByText('store:audit', { exact: true }).waitFor();
  // await paths.getByRole('button', { name: 'Torna agli ingressi' }).click();
  // await paths.getByRole('button', { name: /Salva ordine/ }).waitFor();
  // await page.evaluate(mapped => window.setMapState(mapped), partialMap);
  // await page.getByText('Mappa del sistema parziale').waitFor();
  // await page.getByText('1 osservata in esecuzione · 1 campionata dal profiler · 1 in conflitto').waitFor();
  // await page.evaluate(() => window.setMapState({ state: 'done' }));
  // await page.getByText('Mappa del sistema registrata').waitFor();
  // assert.equal(await page.getByText('Mappa del sistema parziale').count(), 0);
  // await page.locator('#stage-analysis').click();
  // await page.locator('#preview-diagram .im-graph-node').first().click();
  // const preview = page.getByRole('region', { name: 'Client' });
  // await preview.getByRole('button', { name: 'Apri nel grafo' }).waitFor();
  // await page.keyboard.press('Escape');
  // assert.ok(await preview.isHidden());
  // ticket 22: the graph
  // mode.graphStatus = 500;
  // await tabs.getByRole('tab', { name: 'Grafo' }).click();
  // const failed = page.locator('.im-failure');
  // assert.match(await failed.innerText(), /Errore[\s\S]*grafo non letto[\s\S]*Riprova/);
  // mode.graphStatus = 200;
  // await failed.getByRole('button', { name: 'Riprova' }).click();
  // await page.getByRole('region', { name: 'Grafo del codice' }).waitFor();
  // assert.equal(await tabs.getByRole('tab', { name: /^Grafo/ }).locator('.im-count').innerText(), '2');
  // await page.getByLabel('Relazioni', { exact: true }).selectOption('imports');  // the kind filter: no relation of that kind
  // await page.locator('.im-graph-legend').getByText('0 relazioni visibili').waitFor();
  // await page.getByRole('button', { name: 'Azzera filtri' }).click();
  // await page.locator('.im-graph-legend').getByText('4 relazioni visibili').waitFor();
  // const legend = await page.locator('.im-graph-legend').innerText();
  // assert.ok(legend.includes('Osservata in esecuzione') && legend.includes('Incerta') && !legend.includes('■'));
  // await tabs.getByRole('tab', { name: /^Grafo/ }).click();
  // const diagram = page.getByRole('region', { name: 'Grafo del codice' });
  // await page.keyboard.press('Control+f');
  // assert.equal(await page.evaluate(() => document.activeElement?.id), 'graph-search');
  // await tabs.getByRole('tab', { name: /^Grafo/ }).focus();
  // await page.keyboard.press('F6');
  // assert.ok(await inContent());
  // await diagram.locator('[data-im-node="Client"] .im-graph-node').press('ArrowRight');
  // assert.equal(await page.evaluate(() => document.activeElement.closest('[data-im-node]').dataset.imNode), 'Server');
  // await page.keyboard.press('Enter');
  // const group = page.getByRole('region', { name: 'Dettaglio del gruppo' });
  // assert.equal(await group.locator('h2').innerText(), 'Server');
  // const titles = await diagram.locator('.im-graph-edge title').allTextContents();
  // assert.ok(titles.some(label => label.includes('osservata in esecuzione')));
  // assert.ok(titles.some(label => label.includes('campionata dal profiler')));
  // assert.ok(titles.some(label => label.includes('destinazioni in conflitto')));
  // await group.locator('summary', { hasText: 'Prove delle chiamate' }).click();
  // await page.getByText('Client → Server · osservata in esecuzione', { exact: true }).waitFor();
  // await page.getByText('Client → Server · campionata dal profiler', { exact: true }).waitFor();
  // await page.getByText('Client → Server · osservata in esecuzione · destinazioni in conflitto', { exact: true }).waitFor();
  // await group.getByRole('button', { name: /Tutti i 6 file/ }).click();
  // assert.match(await page.locator('.im-inspector .im-panel-title:visible').innerText(), /File di Server/);
  // await page.keyboard.press('Escape');
  // assert.equal(await group.locator('h2').innerText(), 'Server');
  // // A node chosen while a file list is pushed on another group: the new group replaces both, and nothing stale comes back.
  // await group.getByRole('button', { name: /Tutti i 6 file/ }).click();
  // await diagram.locator('[data-im-node="Client"] .im-graph-node').click();
  // assert.equal(await group.locator('h2:visible').innerText(), 'Client');
  // assert.equal(await page.locator('.im-inspector .im-panel-title:visible').innerText(), 'Dettaglio del gruppo');
  // await group.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  // assert.ok(await page.locator('.im-inspector').isHidden());
  // await diagram.getByRole('button', { name: 'Apri Client' }).click();
  // await diagram.getByRole('button', { name: 'Chiudi Client' }).waitFor();
  // await diagram.locator('[data-im-node="child"] .im-graph-node').click();  // a file: its symbols are asked and drawn
  // await group.getByText('Simboli e chiamate').waitFor();
  // await group.locator('code', { hasText: 'save' }).waitFor();
  // assert.equal(await diagram.locator('.im-graph-group').count(), 1);
  // await diagram.getByRole('button', { name: 'Chiudi Client' }).click();
  // await diagram.getByRole('button', { name: 'Apri Client' }).waitFor();
  // await tabs.getByRole('tab', { name: 'Analisi' }).click();
  // assert.ok(await page.locator('.im-inspector').isHidden());
  // await tabs.getByRole('tab', { name: /^Grafo/ }).click();
  // await page.setViewportSize({ width: 900, height: 820 });
  // await group.waitFor();
  // const [content, inspector] = await Promise.all([page.locator('.im-content').boundingBox(), page.locator('.im-inspector').boundingBox()]);
  // assert.ok(inspector.x < content.x + content.width - 100);
  // await group.getByRole('button', { name: 'Chiudi dettaglio' }).click();
  // assert.ok(await page.locator('.im-inspector').isHidden());
  // assert.equal(await page.getByRole('dialog').count(), 0);
  // ticket 23: the engine and the questions
  // await page.locator('#question').waitFor({ state: 'visible' });
  // assert.equal(await page.locator('textarea.im-textarea#question').count(), 1);
  // await page.locator('#question').fill('Dove si firma il token?');  // the question and its answer, with the tools used
  // await page.getByRole('button', { name: 'Chiedi' }).click();
  // await page.locator('#answer-box').getByText('Lo firma auth.ts').waitFor();
  // assert.match(await page.locator('#answer-box').innerText(), /cerca token/);
  // assert.notEqual(await page.getByRole('button', { name: 'Chiedi' }).getAttribute('aria-busy'), 'true');
  // // A busy button ignores the pointer, not the keyboard: Enter on it must not send the question a second time.
  // assert.equal(askRequests.length, 1);
  // await page.evaluate(() => window.setServerState({ asked: { state: 'running', question: 'Dove si firma il token?' } }));
  // await page.locator('#ask-button[aria-busy="true"]').waitFor();
  // await page.locator('#ask-button').focus();
  // await page.keyboard.press('Enter');
  // await page.waitForTimeout(300);
  // assert.equal(askRequests.length, 1);
  // await page.evaluate(() => window.setServerState({ asked: { state: 'done', question: 'Dove si firma il token?' } }));
  // await page.evaluate(() => window.setServerState({ engine: { engine: 'openai', engines: ['claude', 'openai'], api_key: 'set', base_url: 'https://api.test/v1', model: 'm' } }));
  // await page.getByRole('combobox', { name: 'Motore', exact: true }).waitFor();
  // await page.getByRole('combobox', { name: 'Motore', exact: true }).selectOption('openai');
  // for (const label of [/^Indirizzo dell’endpoint/, /^Modello/, /^Chiave/, 'Domanda']) await page.getByLabel(label, { exact: typeof label === 'string' }).waitFor();
  // assert.ok(await page.locator('.im-field-hint', { hasText: 'Chiave impostata' }).isVisible());
  // const forget = page.getByRole('button', { name: 'Rimuovi la chiave' });
  // await forget.click();
  // const sure = page.getByRole('alertdialog', { name: 'Rimuovere la chiave?' });
  // await sure.waitFor();
  // assert.equal(await page.evaluate(() => document.activeElement.textContent.trim()), 'Annulla');
  // assert.match(await sure.innerText(), /deposito delle credenziali[\s\S]*non si può recuperare/);
  // await page.keyboard.press('Escape');
  // await sure.waitFor({ state: 'detached' });
  // assert.equal(engineRequests.length, 0);
  // await forget.click();
  // await sure.getByRole('button', { name: 'Rimuovi la chiave' }).click();
  // await page.waitForFunction(() => document.querySelector('#engine-said')?.textContent.includes('Chiave rimossa'));
  // assert.deepEqual(engineRequests, [{ api_key: '' }]);
  // end of tickets 20 to 23

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
  const opens = name => canvas.getByRole('button', { name: `Apri ${name}`, exact: true });
  const kinds = main.getByRole('list', { name: 'Tipi di linea', exact: true });
  const kindOfLine = text => kinds.getByRole('listitem').filter({ hasText: text });
  const busy = main.locator('[aria-busy="true"]');
  const focusOn = start => page.waitForFunction(text => document.activeElement?.getAttribute('aria-label')?.startsWith(text), start);
  await page.setViewportSize({ width: 1280, height: 850 });
  mode.exportBroken = true;  // an export that cannot be read: the page waits, then says what failed, with Riprova
  mode.exportDelay = 1000;
  await page.goto('http://daodan.test/');
  assert.equal(await page.title(), 'Codebase Map');
  await main.getByRole('progressbar', { name: "Carico l'export…" }).waitFor();
  await line("Carico l'export…").waitFor();
  await nav.getByText("In attesa dell'export.").waitFor();
  assert.equal(await busy.count(), 1);
  const unreadable = main.getByRole('alert');
  await unreadable.waitFor();
  assert.match(await unreadable.innerText(), /Errore[\s\S]*Export non leggibile[\s\S]*Riprova/);
  await line('Export non leggibile').waitFor();
  assert.ok(await selectable(unreadable.getByText('unknown schema: undefined')));
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
  // By keyboard: the arrows follow the lines, Enter chooses, and the › after a node enters it.
  await thing('web').focus();
  for (const [key, name] of [['ArrowRight', 'server,'], ['ArrowLeft', 'web,'], ['ArrowRight', 'server,']]) {
    await page.keyboard.press(key);
    await focusOn(name);
  }
  await page.keyboard.press('Enter');
  await details.getByRole('heading', { name: 'server', exact: true }).waitFor();
  await opens('server').and(page.locator('[tabindex="0"]')).waitFor();
  await page.keyboard.press('Tab');
  await focusOn('Apri server');
  await page.keyboard.press('Enter');
  await place('Sistema / server').waitFor();
  await details.waitFor({ state: 'hidden' });
  await thing('money.ts').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await opens('web').click();  // by its ›
  await place('Sistema / web').waitFor();
  await opens('checkout.tsx').click();
  await place('Sistema / web / checkout.tsx').waitFor();
  await thing('pay').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
  await thing('web').click();  // a double press enters, here with the details open: their opening narrows the canvas
  await details.waitFor();
  await thing('web').dblclick();
  await place('Sistema / web').waitFor();
  await thing('api.ts').waitFor();
  await choose('Torna al sistema');
  await place('Sistema').waitFor();
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
  // On the canvas its nodes have the numbers of its steps, and its lines are a kind of their own.
  await thing('web, passo 1').waitFor();
  await thing('server, passo 2').waitFor();
  await kindOfLine('Linee del flusso').waitFor();
  assert.match(await kindOfLine('Linee del flusso').innerText(), /Linee del flusso\s*4/);
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
  await thing('web, contiene 3 elementi').waitFor();
  await kindOfLine('Linee del flusso').waitFor({ state: 'detached' });
  // What is chosen in the list is brought into the view of the canvas.
  await row(/^card payment provider/).click();
  await details.getByRole('heading', { name: 'card payment provider', exact: true }).waitFor();
  await canvas.getByRole('button', { name: 'card payment provider, esterno, servizio o API', exact: true }).waitFor();
  const inSight = async () => {
    const [box, node] = await Promise.all([canvas.boundingBox(), thing('card payment provider').boundingBox()]);
    return !!node && node.x >= box.x && node.x + node.width <= box.x + box.width && node.y >= box.y && node.y + node.height <= box.y + box.height;
  };
  for (let tries = 0; tries < 30 && !await inSight(); tries += 1) await page.waitForTimeout(100);
  assert.ok(await inSight());
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
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
  const footViews = page.getByRole('toolbar', { name: 'Viste in basso' });
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
  await problem('altro.json non è un export leggibile: unknown schema: altro').waitFor();
  await give('rotto.json', 'application/json', 'not json');
  await problem(/rotto\.json non è un export leggibile: .+JSON/).waitFor();
  await page.keyboard.press('Escape');
  await opener.waitFor({ state: 'detached' });
  await line('shop · run fixture').waitFor();
  await openOther.click();
  await opener.waitFor();
  assert.equal(await opener.getByRole('alert').count(), 0);
  await give('scelto.json', 'application/json', exported('scelto'));
  await opener.waitFor({ state: 'detached' });
  await line('shop · run scelto').waitFor();
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

  await context.route('**/api/runs', route => route.fulfill({ json: { runs: [] } }));
  await context.route('**/api/requests', route => route.fulfill({ json: { requests: [] } }));
  await context.route('**/api/findings', route => route.fulfill({ json: { findings: [], gaps: [] } }));
  await page.reload();
  const noRuns = main.getByText('Creane uno qui sotto, o avvia una mappa nella sessione.');
  await noRuns.waitFor();
  await line('Nessun run').waitFor();
  await nav.getByText('Nessuna mappa: non ci sono run.').waitFor();
  await page.keyboard.press('Control+f');  // no map, no search
  await page.getByText('Questa vista non ha una ricerca.').waitFor();
  // With no run the session is in sight under the words that say so, and its form makes the first run.
  const session = main.getByRole('region', { name: 'Sessione e review', exact: true });
  await session.getByText('Nessuna richiesta.').waitFor();
  await session.getByText('Nessun finding: compaiono quando la sessione chiude una review.').waitFor();
  assert.ok((await session.boundingBox()).y > (await noRuns.boundingBox()).y);
  assert.ok(await openOther.isDisabled());
  const server = { runs: [], posted: [], refuses: 'run già presente', delay: 1000 };
  await context.route('**/api/runs', async route => {
    if (route.request().method() === 'GET') return route.fulfill({ json: { runs: server.runs } });
    server.posted.push(route.request().postDataJSON());
    await new Promise(resolve => setTimeout(resolve, server.delay));
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
  await said('Richiesta non riuscita').waitFor();
  assert.match(await said('Richiesta non riuscita').innerText(), /Errore[\s\S]*Richiesta non riuscita[\s\S]*run già presente/);
  assert.deepEqual([server.posted, await runName.inputValue()], [[{ target: '.', run_id: 'primo-run' }], 'primo-run']);
  Object.assign(server, { refuses: '', delay: 0, runs: [{ run_id: 'primo-run', readable: true }] });
  await create.click();
  await line('shop · run fixture').waitFor();
  assert.match(await main.getByRole('combobox', { name: 'Run' }).innerText(), /Run primo-run/);
  assert.equal(await session.count(), 0);  // over a map it is behind its row
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
  await session.getByRole('heading', { name: 'Finding · 1', exact: true }).waitFor();
  assert.equal(await sessionRow.getAttribute('aria-expanded'), 'true');
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
  assert.match(await request.innerText(), /#1 review · feature[\s\S]*Pagamenti[\s\S]*in attesa della sessione/);
  Object.assign(requests[0], { state: 'done', message: 'Un finding' });
  await request.filter({ hasText: 'Un finding' }).filter({ hasText: 'conclusa' }).waitFor();
  // The session's gaps are a note that is not announced; a finding says its severity and selects its file.
  await session.getByText('Lacune · 1').waitFor();
  await session.getByText('lacuna della sessione').waitFor();
  assert.equal(await main.getByRole('alert').count(), 0);
  const finding = session.getByRole('list', { name: 'Finding', exact: true }).getByRole('button', { name: /High/ });
  assert.match(await finding.innerText(), /web\/checkout\.tsx:12[\s\S]*Premessa[\s\S]*High/);
  await finding.click();
  await details.getByRole('heading', { name: 'checkout.tsx', exact: true }).waitFor();
  await closeIn(details);
  await details.waitFor({ state: 'hidden' });
  await sessionRow.press('Enter');
  await session.waitFor({ state: 'detached' });
  const pollsAtClose = polls;
  await page.waitForTimeout(2500);
  assert.equal(polls, pollsAtClose);

  // The theme the person picks on one page is followed live by the other one (the storage event).
  await choose('Tema chiaro');
  await schemeIs(page, 'light');
  const tab = await context.newPage(), app = await context.newPage();
  await tab.goto('http://daodan.test/');
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
  assert.deepEqual(errors, []);
  console.log('Passed the App (frame, palette, stages, repository, server, theme) and the map (frame, palette, canvas, places and things, details, filters, runs, theme).');
} finally { await browser.close(); }
