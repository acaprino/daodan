// The server of the tests in a browser: the built pages and the layout's worker as they are packaged, and what the routes answer. `mode`
// is what it does next, so that a test can make a route fail or wait.
import { readFile } from 'node:fs/promises';

const assets = new URL('../../daodan/assets/', import.meta.url);
export const envelope = JSON.parse(await readFile(new URL('./fixture.json', import.meta.url)));
// What the fixture lacks for the details: evidence as the server writes it, and lists longer than what is in sight at first.
const parts = Array.from({ length: 9 }, (_, n) => `web/part${n}.tsx`);
envelope.technologies = [{ id: 'react', name: 'React', type: 'framework', category: 'framework', mark: 'react', paths: ['web/checkout.tsx', ...parts] }];
// The logos the server has, and one it has not.
for (const [ref, mark] of [['external:card payment provider', 'stripe'], ['external:api gateway', 'gone']]) envelope.entities.find(entity => entity.ref === ref).mark = mark;
const LOGO = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><circle cx="8" cy="8" r="8" fill="#38a"/></svg>';
export const marksAsked = [];
Object.assign(envelope.entities.find(entity => entity.ref === 'component:web'), { technologies: ['react'], evidence: parts.map((path, n) => ({ path, line: n + 1 })) });
envelope.flows.push({ ...envelope.flows[1], ref: 'flow:lungo', label: 'Flusso lungo', complete: true, gaps: [], steps: Array(43).fill(envelope.flows[1].steps[0]) });
// What the fixture server does next, so that a test can make a route fail or wait.
export const engineRequests = [], askRequests = [], checkRequests = [], selectRequests = [], markRequests = [];
export const mode = { graphStatus: 200, premapStatus: 200, premapDelay: 0, linkStatus: 200, checkDelay: 0, selectRefused: '', exportBroken: false, exportDelay: 0, exportBusy: 0, layoutLost: false, pathsBroken: false, pathsClassified: false, marks: false };
export const run = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'demo' };
export const groups = ['Client', 'Server'].map(name => ({
  id: name, name, mark: null, kind: 'directory', files: Array.from({ length: name === 'Server' ? 6 : 1 }, (_, n) => `${name}/file${n}.ts`), location: 'internal', status: 'confirmed', group: null, evidence: [],
  ...(name === 'Client' && { projects: [{ mark: 'react', name: 'React', category: 'framework', evidence: [{ path: 'package.json', line: 12 }] }], other_dependencies: 3 }),
}));
export const graph = { grouping: 'directories', nodes: groups, open: [], edges: ['confirmed', 'observed', 'sampled'].map(status => ({
    source: 'Client', target: 'Server', counts: { calls: 1 }, status,
    evidence: status === 'observed' ? [{ path: 'Client/file0.ts', line: 3, target: 'Server/file1.ts', kind: 'calls', key: 'save' }] : [],
  })).concat({source: 'Client', target: 'Server', counts: { calls: 1 }, status: 'observed', conflict: true, evidence: []}),
  gaps: [], files: 2, levels: ['codice'], meta: {}, unassigned: { count: 0 } };
export const errors = [];  // what the pages threw

export const respond = async route => {
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
    if (!mode.pathsClassified) return route.fulfill({ json: { cards: [], count: 0, offset, next_offset: null } });
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
    return route.fulfill(mode.marks ? { contentType: 'image/svg+xml', body: LOGO }
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
      branches: [{ name: 'main', commit: '1'.repeat(40) }, { name: 'dev', commit: '2'.repeat(40) }] } }).catch(() => {});  // who asked may have gone
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

// The stream of the App, which a test sends frames on.
export const stream = state => {
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
export const fresh = { context: run, job: { state: 'ready' }, run: { pass: { state: 'fresh' } }, engine: { engine: 'claude', engines: ['claude'] }, links: { state: 'idle' } };

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

// Nothing fails or waits.
export const quiet = () => Object.assign(mode, { graphStatus: 200, premapStatus: 200, premapDelay: 0, exportBroken: false, exportDelay: 0, exportBusy: 0, layoutLost: false, pathsBroken: false, marks: true });

// A page of its own, with the choices it starts from.
export const opened = async (browser, { width, scheme = 'dark', own = false }) => {
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
