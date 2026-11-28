import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import type { Notify } from '@acaprino/imago';
import { createModel } from '../app/model.ts';
import type { Command } from '../app/server.ts';
import { ORPHAN_WRITES } from '../app/snapshot.ts';
import { DEFAULTS, readKept, STORAGE } from '../app/storage.ts';

// A stream as the browser gives it: the test sends its frames.
class FakeSource {
  address: string;
  listeners: Record<string, ((message: { data: string }) => void)[]> = {};
  onerror: (() => void) | null = null;
  closed = false;
  constructor(address: string) { this.address = address; }
  addEventListener(name: string, listener: (message: { data: string }) => void) { (this.listeners[name] ||= []).push(listener); }
  close() { this.closed = true; }
  send(name: string, frame: unknown) { for (const listener of this.listeners[name] ?? []) listener({ data: JSON.stringify(frame) }); }
}

type Call = { path: string; query: URLSearchParams; init?: RequestInit; body: any };
const fails = (status: number, error?: string) => ({ status, ok: false, json: async () => (error ? { error } : {}) });
const turn = () => new Promise(resolve => setImmediate(resolve));  // every promise already answered has gone on
const queryOf = (address: string) => Object.fromEntries(new URL(address, 'http://daodan.test').searchParams);

// The shell's stack of notices: one takes the place of the one with its id.
function stack() {
  const notices: { text: string; id?: string; kind?: 'error' }[] = [];
  const notify: Notify = (text, options) => {
    const at = notices.findIndex(({ id }) => id !== undefined && id === options?.id);
    if (at >= 0) notices.splice(at, 1);
    notices.push({ text, ...options });
  };
  return { notices, notify };
}

function setup(routes: Record<string, (call: Call) => unknown> = {}, kept?: unknown) {
  const store: Record<string, string> = kept === undefined ? {} : { [STORAGE]: JSON.stringify(kept) };
  const calls: Call[] = [], sources: FakeSource[] = [];
  const { notices, notify } = stack();
  const made = createModel({
    token: 'segreto',
    fetch: async (address, init) => {
      const url = new URL(address, 'http://daodan.test');
      const call = { path: url.pathname, query: url.searchParams, init, body: init?.body && JSON.parse(String(init.body)) };
      calls.push(call);
      const found = await (routes[url.pathname] ?? (() => fails(404)))(call) as any;
      return (typeof found?.json === 'function' ? found : { status: 200, ok: true, json: async () => found }) as Response;
    },
    stream: address => { const source = new FakeSource(address); sources.push(source); return source as never; },
    storage: () => ({ getItem: key => store[key] ?? null, setItem: (key, value) => { store[key] = value; } }),
  });
  const model = { ...made, start: () => made.start(notify) };
  return {
    model, notices, calls, sources, now: () => model.snapshot(), keptNow: () => JSON.parse(store[STORAGE]),
    asked: (path: string) => calls.filter(call => call.path === path), said: () => notices.map(notice => notice.text),
  };
}

const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
// The plan of a run that is over, in the server's form: its steps are the path.
const PLAN = JSON.parse(readFileSync(new URL('./plan.json', import.meta.url), 'utf8'));
const DONE = { ...PLAN, steps: PLAN.steps.map((step: object) => ({ ...step, state: 'done' })) };
const ready = { context, job: { state: 'ready' }, run: { pass: { state: 'fresh' }, plan: DONE }, engine: { engine: 'claude', engines: ['claude'] }, links: { state: 'idle' } };
const none = { context: null, job: { state: 'idle' }, engine: { engine: null, engines: ['claude'] } };
const node = (id: string, more = {}) => ({ id, name: id, kind: 'directory', files: [`${id}/a.ts`], location: 'internal', group: null, ...more });
const graph = (more = {}) => ({
  grouping: 'directories', nodes: [node('a'), node('b')], open: [], edges: [], files: 2, levels: ['codice'], gaps: [], meta: {}, unassigned: { count: 0 }, ...more,
});
const premap = {
  files: ['src/a.ts'], languages: [], technologies: [],
  units: [{ id: 'u', name: 'web', kind: 'npm', root: '.', status: 'confirmed', dependencies: [{ name: 'left-pad' }] }],
};
const events = (run_id: string, pipeline: unknown[], own: unknown[] = []) => ({
  run_events: { run_id, next_cursor: 3, events: own, pipeline: { next_cursor: 5, events: pipeline } }, pulse: { next_cursor: 7 },
});

test('the stream is asked with the token and the cursors, and a frame of the state is the state', () => {
  const { model, sources, now } = setup();
  model.start();
  assert.ok(sources[0].address.startsWith('/api/stream?'));
  assert.deepEqual(queryOf(sources[0].address), { token: 'segreto', max_seconds: '60', run: '', after: '0', pipeline_after: '0', pulse_after: '0' });
  const before = now();
  assert.equal(now(), before);  // one object, until something changes
  let told = 0;
  const leave = model.subscribe(() => { told += 1; });
  sources[0].send('app', none);
  assert.notEqual(now(), before);
  assert.deepEqual([now().server, now().engineDraft, told > 0], [none, { engine: null, engines: ['claude'], api_key: '' }, true]);
  leave();
  told = 0;
  sources[0].send('app', none);
  assert.equal(told, 0);
});

test('the events of a run are added as they come, those of another take their place, and the cursors follow', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const { model, sources, now } = setup();
  model.start();
  sources[0].send('app', none);
  sources[0].send('snapshot', events('r1', [{ kind: 'step.started', step: 'recognize_stack' }], [{ event: 'run_created', message: 'nuovo' }]));
  sources[0].send('update', events('r1', [{ kind: 'log', message: 'letto' }]));
  assert.deepEqual(now().events.map(e => [e.run === true, e.event ?? e.kind]), [[true, 'run_created'], [false, 'step.started'], [false, 'log']]);
  sources[0].onerror!();
  t.mock.timers.tick(1);
  assert.deepEqual(queryOf(sources[1].address), { token: 'segreto', max_seconds: '60', run: 'r1', after: '3', pipeline_after: '5', pulse_after: '7' });
  sources[1].send('snapshot', events('r2', [{ kind: 'log', message: 'altro' }]));
  assert.deepEqual(now().events.map(e => e.message), ['altro']);
});

test('a stream that ended opens again at once; one that said nothing, or a failure, says it and waits', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const { model, sources, now } = setup();
  model.start();
  sources[0].onerror!();  // it never answered
  assert.deepEqual([sources[0].closed, now().serverError], [true, 'lo stream del server non risponde']);
  t.mock.timers.tick(3999);
  assert.equal(sources.length, 1);
  t.mock.timers.tick(1);
  assert.equal(sources.length, 2);
  sources[1].send('app', none);  // it answers again
  assert.equal(now().serverError, '');
  sources[1].onerror!();
  t.mock.timers.tick(1);
  assert.deepEqual([sources.length, now().serverError], [3, '']);
  sources[2].send('app', none);
  sources[2].send('failure', { error: 'il run non si legge' });
  sources[2].onerror!();
  assert.equal(now().serverError, 'il run non si legge');
  t.mock.timers.tick(3999);
  assert.equal(sources.length, 3);
  t.mock.timers.tick(1);
  assert.equal(sources.length, 4);
});

test('what was kept is read in the shape it has, and what does not fit is the default', () => {
  const read = (value: string | null) => readKept(() => ({ getItem: () => value, setItem() {} }));
  assert.deepEqual(read(null), { kept: DEFAULTS, available: true });
  const kept = { screen: 'graph', analysisStage: 'find_modules', repositoryUrl: 'https://github.com/demo/shop', runId: 'r1',
    treeOpen: { 'directory:src': true }, graphOpen: ['a'], graphDepth: '2' };
  assert.deepEqual(read(JSON.stringify(kept)), { kept: { ...DEFAULTS, ...kept }, available: true });
  assert.deepEqual(read(JSON.stringify({ screen: 'altro', analysisStage: 7, graphOpen: [1] })), { kept: DEFAULTS, available: true });
  assert.deepEqual(read('{'), { kept: DEFAULTS, available: false });
  assert.deepEqual(readKept(() => { throw new Error('blocked'); }), { kept: DEFAULTS, available: false });
});

test('what the person looks at is kept, and a storage that refuses it is said once', () => {
  const { model, keptNow, said } = setup();
  model.start();
  assert.deepEqual([keptNow(), said()], [DEFAULTS, []]);
  model.navigate('engine');
  assert.equal(keptNow().screen, 'engine');
  const blocked = createModel({
    token: '', fetch: async () => fails(404) as never, stream: () => new FakeSource('') as never, storage: () => { throw new Error('blocked'); },
  });
  const { notices, notify } = stack();
  blocked.start(notify);
  blocked.navigate('graph');
  assert.deepEqual(notices.map(({ text }) => text), ['Archiviazione del browser non disponibile: le scelte durano questa apertura.']);
  assert.equal(blocked.snapshot().kept.screen, 'graph');
});

test('a result takes the place of the same one, and an error never does', async () => {
  const { model, notices } = setup({ '/api/app/retry': () => fails(500, 'caduto') });
  model.start();
  model.clearGraphFilters();
  model.clearGraphFilters();
  await model.retryPass();
  await model.retryPass();
  const cleared = 'Filtri azzerati: tutti i gruppi del grafo sono visibili.';
  assert.deepEqual(notices, [{ id: cleared, text: cleared }, { kind: 'error', text: 'caduto' }, { kind: 'error', text: 'caduto' }]);
});

const hostGroup = (tool: string, host: string) =>
  ({ tool, project: '/p', requests: [{ host, port: 443, address: '10.0.0.4', network: true, declared_in: ['build.gradle'] }] });

test('the answer to a group of hosts is sent for all its hosts, once, and the new state and a notice follow', async () => {
  const gradle = hostGroup('gradle', 'repo.example.com'), npm = hostGroup('npm', 'npm.example.com');
  let answer: (value: unknown) => void = () => undefined;
  const { model, sources, now, asked, said } = setup({ '/api/app/egress': () => new Promise(resolve => { answer = resolve; }) });
  model.start();
  sources[0].send('app', { ...ready, egress: [gradle, npm] });
  const sent = model.replyHosts('once');
  model.replyHosts('block');  // one answer at a time
  model.hideHosts();  // nor is the window put aside while it is sent
  assert.deepEqual([asked('/api/app/egress').map(call => call.body), now().hostsReplying, now().hostsHidden],
    [[{ hosts: ['repo.example.com'], reply: 'once' }], 'once', []]);
  assert.equal((asked('/api/app/egress')[0].init?.headers as Record<string, string>)['X-Daodan-Token'], 'segreto');  // the server's guard
  answer({ ...ready, egress: [npm] });
  await sent;
  assert.deepEqual([now().server?.egress, now().hostsReplying], [[npm], '']);
  assert.ok(said().includes('Host approvati per questa analisi: repo.example.com.'));
});

test('a refused answer is said and the group waits; one put aside is offered again from the palette', async () => {
  const gradle = hostGroup('gradle', 'repo.example.com');
  const { model, sources, now, notices, asked } = setup({ '/api/app/egress': () => fails(400, 'risposta sconosciuta') });
  model.start();
  sources[0].send('app', { ...ready, egress: [gradle] });
  await model.replyHosts('always');
  assert.deepEqual([notices.at(-1), now().hostsReplying, now().server?.egress], [{ kind: 'error', text: 'risposta sconosciuta' }, '', [gradle]]);
  model.hideHosts();
  assert.equal(now().hostsHidden.length, 1);
  await model.replyHosts('no');  // nothing is in view: nothing is sent
  assert.equal(asked('/api/app/egress').length, 1);
  model.showHosts();
  assert.deepEqual(now().hostsHidden, []);
});

test('the person\'s command is sent from the form, once, and the new state and a notice follow; a refusal keeps the window', async () => {
  const proposed: Command = { kind: 'starts', root: 'web', argv: ['pnpm', 'dev'], by: 'assistant', grade: 'proposto', surface: 'web' };
  let answer: (value: unknown) => void = () => undefined;
  const { model, sources, now, asked, said, notices } = setup({ '/api/app/command': call =>
    (call.body.action === 'remove' ? fails(400, 'no single starts command of web is kept') : new Promise(resolve => { answer = resolve; })) });
  model.start();
  sources[0].send('app', { ...ready, commands: [proposed] });
  model.showCommand('starts', 'web');
  assert.deepEqual(now().commandDraft, { kind: 'starts', root: 'web', words: 'pnpm\ndev', port: '' });
  model.editCommand({ words: 'pnpm\nrun\ndev', port: '5173' });
  const sent = model.setCommand();
  model.setCommand();  // one at a time
  model.hideCommand();  // nor does the window close while it is sent
  assert.deepEqual(asked('/api/app/command').map(call => call.body),
    [{ action: 'set', command: { kind: 'starts', root: 'web', argv: ['pnpm', 'run', 'dev'], port: 5173, surface: 'web' } }]);
  assert.equal(now().commandBusy, 'set');
  const mine: Command = { ...proposed, argv: ['pnpm', 'run', 'dev'], port: 5173, by: 'user', grade: 'confermato' };
  answer({ ...ready, commands: [mine] });
  await sent;
  assert.deepEqual([now().server?.commands, now().commandBusy, now().commandDraft], [[mine], '', null]);
  assert.ok(said().includes('Comando impostato: Avvio dell’app in web. Gira alla prossima analisi, nel container.'));
  model.showCommand('starts', 'web');
  assert.equal(await model.removeCommand(mine), false);
  assert.deepEqual(asked('/api/app/command').at(-1)?.body, { action: 'remove', kind: 'starts', root: 'web' });
  assert.deepEqual([notices.at(-1), now().commandDraft?.root], [{ kind: 'error', text: 'no single starts command of web is kept' }, 'web']);
  model.editCommand({ words: '' });
  await model.setCommand();  // a form that is not ready sends nothing
  assert.equal(asked('/api/app/command').length, 2);
  model.hideCommand();
  assert.equal(now().commandDraft, null);
});

test('a run in view again, after none or chosen anew, is read again', async () => {
  const { model, sources, now, asked } = setup({ '/api/app/premap': () => premap, '/api/app/graph': () => graph() },
    { ...DEFAULTS, analysisStage: 'find_modules', runId: 'r1' });
  const times = () => [asked('/api/app/premap').length, asked('/api/app/graph').length];
  model.start();
  sources[0].send('app', ready);
  await turn();
  assert.deepEqual([times(), now().premap !== null, now().graph !== null], [[1, 1], true, true]);
  sources[0].send('app', none);
  assert.deepEqual([now().premap, now().graph], [null, null]);  // the count of the groups goes with its repository
  sources[0].send('app', ready);
  model.selectStage('find_modules');
  await turn();
  assert.deepEqual([times(), now().premap !== null, now().graph !== null], [[2, 2], true, true]);
});

test('an answer for a run no longer in view changes nothing of the one that is', async () => {
  const graphs: ((found: unknown) => void)[] = [], premaps: ((found: unknown) => void)[] = [];
  const { model, sources, now } = setup({
    '/api/app/graph': () => new Promise(resolve => { graphs.push(resolve); }), '/api/app/premap': () => new Promise(resolve => { premaps.push(resolve); }),
  }, { ...DEFAULTS, analysisStage: 'find_modules', runId: 'r1' });
  model.start();
  sources[0].send('app', ready);
  sources[0].send('app', { ...ready, context: { ...context, run_id: 'r2' } });
  assert.deepEqual([graphs.length, premaps.length], [2, 2]);  // the new run does not wait for the answers of the old one
  graphs[0](graph({ files: 1 }));
  premaps[0](fails(500, 'manifest illeggibile'));
  await turn();
  assert.deepEqual([now().graph, now().graphLoading, now().premap, now().premapError], [null, true, null, '']);
  graphs[1](graph({ files: 9 }));
  premaps[1](premap);
  await turn();
  assert.deepEqual([now().graph!.files, now().graphLoading, now().premap!.units.length, graphs.length, premaps.length], [9, false, 1, 2, 2]);
  sources[0].send('app', { ...ready, context: { ...context, run_id: 'r3' } });
  sources[0].send('app', { ...ready, context: { ...context, run_id: 'r4' } });
  graphs[2](fails(500, 'grafo non letto'));  // a failure of the old one is not the new one's either
  premaps[2](premap);
  await turn();
  assert.deepEqual([now().graphError, now().graphLoading, now().premap], ['', true, null]);
});

test('what was kept of another run is dropped; without a context the analysis is the repository alone', () => {
  const { model, sources, now } = setup({}, { ...DEFAULTS, analysisStage: 'assemble_graph', runId: 'r0', treeSearch: 'x', graphOpen: ['a'], graphRoot: 'a' });
  model.start();
  sources[0].send('app', ready);
  const { analysisStage, runId, treeSearch, graphOpen, graphRoot } = now().kept;
  assert.deepEqual([analysisStage, runId, treeSearch, graphOpen, graphRoot], ['list_files', 'r1', '', [], '']);  // the first step of the plan
  sources[0].send('app', none);
  assert.deepEqual([now().kept.analysisStage, now().kept.runId], ['repository', '']);
});

test('a step the plan does not have is no place: the analysis goes back to the repository', () => {
  const { model, sources, now } = setup({}, { ...DEFAULTS, analysisStage: 'run_and_observe', runId: 'r1' });
  model.start();
  assert.equal(now().kept.analysisStage, 'run_and_observe');  // nothing is known yet
  sources[0].send('app', { ...ready, run: { pass: { state: 'running' }, plan: { ...DONE, steps: DONE.steps.filter((step: { id: string }) => step.id !== 'run_and_observe') } } });
  assert.equal(now().kept.analysisStage, 'repository');
  model.selectStage('assemble_graph');
  sources[0].send('app', { ...ready, run: { pass: { state: 'running' }, plan: PLAN } });
  assert.equal(now().kept.analysisStage, 'assemble_graph');  // a step not over is a place all the same
});

test('an address that is not a GitHub repository is refused in words, with no request', async () => {
  const { model, calls, now } = setup();
  await model.verifyRepositoryUrl();
  assert.equal(now().checkError, 'Inserisci l’URL GitHub della repository.');
  model.setRepositoryUrl('https://github.com/demo/shop/tree/main');
  assert.equal(now().checkError, '');
  await model.verifyRepositoryUrl();
  assert.match(now().checkError, /senza percorsi aggiuntivi/);
  assert.equal(calls.length, 0);
});

test('a check is asked once, takes the branch it prefers, and its answer for an address since changed is dropped', async () => {
  let answer: (found: unknown) => void = () => {};
  const { model, now, calls, said } = setup({ '/api/app/check': () => new Promise(resolve => { answer = resolve; }) });
  const found = { state: 'accessible', repository: context.repository, default: 'dev',
    branches: [{ name: 'dev', commit: '2'.repeat(40) }, { name: 'master', commit: '1'.repeat(40) }] };
  model.start();
  model.setRepositoryUrl(' https://github.com/demo/shop ');
  model.verifyRepositoryUrl();
  model.verifyRepositoryUrl();
  await turn();
  assert.deepEqual([calls.length, calls[0].body, now().checking], [1, { url: 'https://github.com/demo/shop' }, true]);
  assert.equal((calls[0].init!.headers as Record<string, string>)['X-Daodan-Token'], 'segreto');
  answer(found);
  await turn();
  assert.deepEqual([now().checking, now().checked, now().branch, now().checkedUrl], [false, found, 'master', 'https://github.com/demo/shop']);
  assert.deepEqual(said(), ['demo/shop: 2 branch letti da GitHub.']);
  model.verifyRepositoryUrl();
  await turn();
  model.setRepositoryUrl('https://github.com/demo/altro');
  answer(found);
  await turn();
  assert.deepEqual([now().checking, now().checked], [false, null]);
});

test('a check that fails says the words of the server, or its status', async () => {
  let failure = fails(400, 'indirizzo rifiutato');
  const { model, now } = setup({ '/api/app/check': () => failure });
  model.setRepositoryUrl('github.com/demo/shop');
  await model.verifyRepositoryUrl();
  assert.deepEqual([now().checkError, now().checking], ['indirizzo rifiutato', false]);
  failure = fails(500);
  await model.verifyRepositoryUrl();
  assert.equal(now().checkError, 'il server ha risposto 500');
  failure = fails(503);
  await model.verifyRepositoryUrl();
  assert.equal(now().checkError, 'Daodan è occupato');
});

test('a branch chosen is prepared, and the pre-map opens when its context is ready', async () => {
  const preparing = { ...none, job: { state: 'preparing', step: 'checkout', detail: 'main' } };
  let refused = true;
  const { model, sources, now, asked, said } = setup({
    '/api/app/check': () => ({ state: 'accessible', repository: context.repository, default: 'main',
      branches: [{ name: 'main', commit: context.commit }, { name: 'dev', commit: context.commit }] }),
    '/api/app/select': () => (refused ? fails(400, 'lavoro in corso') : preparing),
    '/api/app/graph': () => graph(), '/api/app/premap': () => premap,
  });
  model.start();
  sources[0].send('app', none);
  await model.selectRepository();
  assert.equal(asked('/api/app/select').length, 0);  // nothing was checked
  model.setRepositoryUrl('https://github.com/demo/shop');
  await model.verifyRepositoryUrl();
  model.setBranch('dev');
  await model.selectRepository();
  assert.deepEqual([now().selectError, now().selecting], ['lavoro in corso', false]);
  refused = false;
  await model.selectRepository();
  assert.deepEqual([asked('/api/app/select')[1].body, now().selecting, now().selectError], [{ url: 'https://github.com/demo/shop', branch: 'dev' }, true, '']);
  sources[0].send('app', preparing);
  assert.equal(now().kept.analysisStage, 'repository');
  sources[0].send('app', ready);
  assert.deepEqual([now().selecting, now().kept.analysisStage], [false, 'list_files']);
  assert.equal(said().at(-1), 'Contesto pronto: demo/shop · main');
});

test('the process goes on by itself only where nothing is being written', async () => {
  const { model, sources, now, said } = setup({
    '/api/app/check': () => ({ state: 'accessible', repository: context.repository, default: 'main', branches: [{ name: 'main', commit: context.commit }] }),
    '/api/app/select': () => ({ ...none, job: { state: 'preparing' } }), '/api/app/graph': () => graph(), '/api/app/premap': () => premap,
  });
  model.start();
  sources[0].send('app', none);
  model.setRepositoryUrl('https://github.com/demo/shop');
  await model.verifyRepositoryUrl();
  await model.selectRepository();
  model.setRepositoryUrl('https://github.com/demo/al');
  sources[0].send('app', ready);
  assert.deepEqual([now().selecting, now().kept.analysisStage, now().kept.repositoryUrl, said().at(-1)],
    [false, 'repository', 'https://github.com/demo/al', 'Contesto pronto: demo/shop · main']);
});

test('the engine leads back to the step that asked for it, and to none from its tab', () => {
  const { model, sources, now } = setup({}, { ...DEFAULTS, analysisStage: 'link_calls', runId: 'r1' });
  model.start();
  sources[0].send('app', ready);
  model.chooseEngine();
  assert.deepEqual([now().kept.screen, now().engineFromStep], ['engine', true]);
  model.navigate('analysis');
  assert.deepEqual([now().kept.screen, now().kept.analysisStage, now().engineFromStep], ['analysis', 'link_calls', false]);
  model.navigate('engine');
  assert.equal(now().engineFromStep, false);
});

test('a choice is asked once, and a frame that comes before its answer is of what was before it', async () => {
  let answer: (found: unknown) => void = () => {};
  const { model, sources, now, asked, said } = setup({
    '/api/app/check': () => ({ state: 'accessible', repository: context.repository, default: 'main', branches: [{ name: 'main', commit: context.commit }] }),
    '/api/app/select': () => new Promise(resolve => { answer = resolve; }), '/api/app/graph': () => graph(), '/api/app/premap': () => premap,
  });
  model.start();
  sources[0].send('app', ready);
  model.setRepositoryUrl('https://github.com/demo/shop');
  await model.verifyRepositoryUrl();
  model.selectRepository();
  model.selectRepository();
  await turn();
  assert.deepEqual([asked('/api/app/select').length, now().selecting], [1, true]);
  sources[0].send('app', { ...ready, mcp_ready: 'ready' });
  assert.deepEqual([now().selecting, now().kept.analysisStage, said().length], [true, 'repository', 1]);
  answer(fails(400, 'lavoro in corso'));
  await turn();
  assert.deepEqual([now().selecting, now().selectError], [false, 'lavoro in corso']);
  model.selectRepository();
  answer({ ...ready, job: { state: 'preparing' } });
  await turn();
  assert.deepEqual([now().selecting, asked('/api/app/select').length], [true, 2]);
  sources[0].send('app', ready);  // the same run, prepared again
  await turn();
  assert.deepEqual([now().selecting, now().kept.analysisStage, asked('/api/app/premap').length], [false, 'list_files', 1]);  // the first step shows the files the pre-map read
});

test('a busy server is asked again once by each reader, and said once', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let free = false;
  const { model, notices, sources, now, asked, said } = setup({
    '/api/app/premap': () => (free ? premap : fails(503)), '/api/app/graph': () => (free ? graph() : fails(503)),
  }, { ...DEFAULTS, analysisStage: 'find_modules', runId: 'r1' });
  const times = () => [asked('/api/app/premap').length, asked('/api/app/graph').length];
  model.start();
  sources[0].send('app', ready);
  await turn();
  sources[0].send('app', { ...ready });  // a frame that comes meanwhile asks nothing more
  sources[0].send('app', { ...ready });
  await turn();
  assert.deepEqual([times(), said(), now().graphLoading], [[1, 1], ['Daodan è occupato, riprovo'], true]);
  t.mock.timers.tick(2000);
  await turn();
  assert.deepEqual([times(), said()], [[2, 2], ['Daodan è occupato, riprovo']]);
  notices.length = 0;
  t.mock.timers.tick(2000);
  await turn();
  assert.deepEqual([times(), said()], [[3, 3], []]);  // closed, it is not said again
  free = true;
  t.mock.timers.tick(2000);
  await turn();
  assert.deepEqual([times(), now().premap !== null, now().graph !== null], [[4, 4], true, true]);
  t.mock.timers.tick(2000);
  await turn();
  assert.deepEqual(times(), [4, 4]);
});

test('the pre-map is read once a run; a busy server is asked again, and a failure can be tried again', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let answer: unknown = fails(503);
  const { model, sources, now, asked, said } = setup({ '/api/app/premap': () => answer, '/api/app/graph': () => graph() },
    { ...DEFAULTS, analysisStage: 'find_modules', runId: 'r1' });
  model.start();
  sources[0].send('app', ready);
  await turn();
  assert.deepEqual([said(), now().premapError], [['Daodan è occupato, riprovo'], '']);
  answer = fails(500, 'manifest illeggibile');
  t.mock.timers.tick(2000);
  await turn();
  assert.deepEqual([asked('/api/app/premap').length, now().premapError, now().premap], [2, 'manifest illeggibile', null]);
  answer = premap;
  model.retryPremap();
  await turn();
  assert.deepEqual([now().premapError, now().premap!.dependencies], ['', [{ name: 'left-pad', unit: 'web' }]]);
  sources[0].send('app', { ...ready });
  await turn();
  assert.equal(asked('/api/app/premap').length, 3);
});

test('the graph is asked with the groups open on its own screen, and a group the run no longer shows is dropped', async () => {
  const { model, notices, sources, now, asked } = setup({ '/api/app/graph': call => {
    const open = JSON.parse(call.query.get('open') ?? '[]') as string[];
    if (open.includes('gone')) return fails(400, 'the graph shows no group to open: "gone"');
    return open.length ? graph({ open: [{ id: 'a', name: 'a', parent: null }], nodes: [node('a/x', { group: 'a' }), node('b')] }) : graph();
  } }, { ...DEFAULTS, screen: 'graph', runId: 'r1' });
  const openAsked = () => asked('/api/app/graph').at(-1)!.query.get('open');
  model.start();
  sources[0].send('app', ready);
  await turn();
  assert.deepEqual([openAsked(), now().graph!.nodes.map(n => n.id), now().kept.graphRoot], [null, ['a', 'b'], 'a']);
  model.openGroup('a');
  await turn();
  assert.deepEqual([openAsked(), now().kept.graphRoot], ['["a"]', 'a/x']);  // the focus stays inside the group
  model.openGroup('gone');
  await turn();
  assert.deepEqual(notices.at(-1), { text: 'Il gruppo «gone» non si può più aprire nel grafo di questo run.', kind: 'error' });
  assert.deepEqual([now().kept.graphOpen, openAsked()], [['a'], '["a"]']);
  model.selectStage('link_calls');  // elsewhere the first grouping alone
  await turn();
  assert.deepEqual([openAsked(), now().graph!.open], [null, []]);
  model.navigate('graph');
  await turn();
  model.closeGroup('a');
  assert.deepEqual([now().graph!.open.length, now().graphLoading], [1, true]);  // what is drawn stays until the answer
  await turn();
  assert.deepEqual([now().kept.graphOpen, now().kept.graphRoot, now().graphLoading, now().graph!.open], [[], 'a', false, []]);
  model.toggleGroup('a');  // by what is drawn, not by what is asked
  model.toggleGroup('a');
  await turn();
  assert.deepEqual([now().kept.graphOpen, now().graph!.open.length], [['a'], 1]);
  model.toggleGroup('a');
  await turn();
  assert.deepEqual([now().kept.graphOpen, now().graph!.open], [[], []]);
});

test('the groups opened while the graph is read are asked when it is, and so are those a screen keeps', async () => {
  const answers: ((found: unknown) => void)[] = [];
  const { model, sources, now, asked } = setup({ '/api/app/graph': () => new Promise(resolve => { answers.push(resolve); }) },
    { ...DEFAULTS, screen: 'graph', runId: 'r1' });
  const opened = () => asked('/api/app/graph').map(call => call.query.get('open'));
  const holding = (...ids: string[]) => graph({ open: ids.map(id => ({ id, name: id, parent: null })) });
  model.start();
  sources[0].send('app', ready);
  model.openGroup('a');
  model.openGroup('b');
  assert.deepEqual(opened(), [null]);
  answers[0](graph());
  await turn();
  assert.deepEqual([opened(), now().graphLoading], [[null, '["a","b"]'], true]);
  answers[1](holding('a', 'b'));
  await turn();
  assert.deepEqual([opened().length, now().graphLoading, now().graph!.open.length], [2, false, 2]);
  model.keep({ graphOpen: ['b'] });
  assert.deepEqual(opened().at(-1), '["b"]');
  answers[2](holding('b'));
  await turn();
  model.keep({ graphOpen: ['b'], graphSearch: 'x' });  // the same groups: the same graph
  model.keep({ graphKind: 'calls' });
  assert.equal(opened().length, 3);
});

test('the graph screen is to show the details of the group the person came for, chose, opened or closed', () => {
  const { model, now } = setup();
  const wanted = () => now().groupWanted;
  assert.equal(wanted(), false);
  model.showNode('b');
  assert.deepEqual([wanted(), now().kept.graphRoot], [true, 'b']);
  model.groupShown();
  assert.equal(wanted(), false);
  for (const act of [() => model.selectNode('a'), () => model.openGroup('a'), () => model.closeGroup('a'), () => model.navigate('graph')]) {
    act();
    assert.equal(wanted(), true);
    model.groupShown();
  }
  assert.deepEqual([now().kept.graphRoot, now().kept.graphOpen], ['a', []]);
  model.navigate('graph');
  model.navigate('engine');  // anywhere else it is void
  assert.equal(wanted(), false);
  model.showNode('b');
  model.selectStage('link_calls');
  assert.equal(wanted(), false);
  assert.equal(setup({}, { ...DEFAULTS, screen: 'graph' }).now().groupWanted, true);  // the page opens there
});

test('from another screen a node is shown with what is next to it, and the whole graph with no filter', () => {
  const { model, keptNow } = setup();
  model.keep({ graphSearch: 'x', graphOpen: ['a'], graphKind: 'calls' });
  model.showNode('b');
  const shown = keptNow();
  assert.deepEqual([shown.screen, shown.graphRoot, shown.graphOpen, shown.graphDepth, shown.graphSearch], ['graph', 'b', [], '1', '']);
  model.showFullGraph();
  assert.deepEqual([keptNow().graphDepth, keptNow().graphKind], ['all', 'calls']);
  model.clearGraphFilters();
  assert.deepEqual([keptNow().graphKind, keptNow().graphRoot], ['all', 'b']);
});

test('a graph that fails is said and asked again; new links, and a step of the plan that ends, are a new graph', async () => {
  let answer: unknown = fails(500, 'grafo non letto');
  const { model, sources, now, asked } = setup({ '/api/app/graph': () => answer }, { ...DEFAULTS, screen: 'graph', runId: 'r1' });
  const times = () => asked('/api/app/graph').length;
  model.start();
  sources[0].send('app', ready);
  await turn();
  assert.deepEqual([now().graphError, now().graph, now().graphLoading], ['grafo non letto', null, false]);
  sources[0].send('app', { ...ready });  // not asked again by itself
  await turn();
  assert.equal(times(), 1);
  answer = graph();
  model.retryGraph();
  await turn();
  assert.deepEqual([now().graphError, now().graph!.files], ['', 2]);
  sources[0].send('app', { ...ready, links: { state: 'done' } });
  await turn();
  assert.equal(times(), 3);
  sources[0].send('update', events('r1', [{ kind: 'step.finished', step: 'assemble_graph' }]));  // an event is the chronicle alone
  await turn();
  assert.equal(times(), 3);
  const assembling = { ...DONE, steps: DONE.steps.map((step: { id: string }) => (step.id === 'assemble_graph' ? { ...step, state: 'running' } : step)) };
  sources[0].send('app', { ...ready, links: { state: 'done' }, run: { ...ready.run, plan: assembling } });
  await turn();
  assert.equal(times(), 3);
  sources[0].send('app', { ...ready, links: { state: 'done' } });  // the plan says the step is done
  await turn();
  assert.equal(times(), 4);
});

test('the paths are read page by page, and a page left while it was read is there on the way back', async () => {
  let effects: (found: unknown) => void = () => {}, broken = false;
  const { model, sources, now, asked } = setup({ '/api/app/premap': () => premap, '/api/app/graph': () => graph(), '/api/app/paths': call => {
    if (broken) return fails(500, 'prove non lette');
    if (call.query.get('effects')) return new Promise(resolve => { effects = resolve; });
    const offset = Number(call.query.get('offset'));
    return call.query.get('id') ? { card: { card_id: 'c' }, steps: [{ n: 1 }], offset, count: 1, next_offset: null }
      : { cards: [{ card_id: 'c' }], offset, count: 2, next_offset: offset ? null : 1 };
  } }, { ...DEFAULTS, analysisStage: 'assemble_graph', runId: 'r1' });
  const page = () => now().pathPage!;
  model.start();
  sources[0].send('app', ready);
  await turn();
  assert.equal(page().result!.cards!.length, 1);
  model.nextPaths();
  await turn();
  assert.deepEqual([page().offset, page().previous!.offset], [1, 0]);
  model.openPaths(ORPHAN_WRITES);
  await turn();
  assert.deepEqual([page().result, asked('/api/app/paths').at(-1)!.query.get('id')], [undefined, null]);
  model.openPaths('c');
  effects({ effects: [{ n: 1 }], offset: 0, count: 1, next_offset: null });
  await turn();
  assert.equal(page().result!.steps!.length, 1);
  model.previousPaths();
  assert.equal(page().result!.effects!.length, 1);
  model.listPaths();
  assert.deepEqual([page().id, page().offset], [null, 1]);
  broken = true;
  model.openPaths('c');
  await turn();
  assert.equal(page().error, 'prove non lette');
  broken = false;
  model.retryPaths();
  await turn();
  assert.deepEqual([page().error, page().result!.steps!.length], [undefined, 1]);
  sources[0].send('app', { ...ready, mapped: { state: 'done' } });  // another map: the entries are read again
  await turn();
  assert.deepEqual([page().id, page().previous], [null, null]);
});

test('the symbols of a file are asked when it is chosen, once', async () => {
  let answer: unknown = fails(500, 'outline non letto');
  const { model, now, asked } = setup({ '/api/app/symbols': () => answer });
  model.loadSymbols('file:a.ts');
  model.loadSymbols('file:a.ts');
  assert.deepEqual(now().symbols, { file: 'file:a.ts', loading: true });
  await turn();
  assert.deepEqual([now().symbols, asked('/api/app/symbols').length], [{ file: 'file:a.ts', error: 'outline non letto' }, 1]);
  answer = { file: 'file:a.ts', symbols: [], calls: [] };
  model.retrySymbols('file:a.ts');
  await turn();
  assert.deepEqual(now().symbols, answer);
});

test('a busy server is asked again for the symbols, unless the file is left or a new graph drops them', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let answer: unknown = fails(503);
  const { model, sources, now, asked, said } = setup({ '/api/app/symbols': () => answer, '/api/app/graph': () => graph() },
    { ...DEFAULTS, screen: 'graph', runId: 'r1' });
  const times = () => asked('/api/app/symbols').length;
  model.start();
  sources[0].send('app', ready);
  await turn();
  model.loadSymbols('file:a.ts');
  await turn();
  assert.deepEqual([now().symbols, said()], [{ file: 'file:a.ts', loading: true }, []]);
  model.loadSymbols('file:b.ts');  // another file
  await turn();
  t.mock.timers.tick(2000);
  await turn();
  assert.deepEqual([times(), asked('/api/app/symbols').at(-1)!.query.get('file')], [3, 'file:b.ts']);
  model.retryGraph();
  await turn();
  assert.equal(now().symbols, null);
  t.mock.timers.tick(2000);
  await turn();
  assert.equal(times(), 3);
  answer = { file: 'file:b.ts', symbols: [], calls: [] };
  model.loadSymbols('file:b.ts');
  await turn();
  assert.deepEqual([now().symbols, times()], [answer, 4]);
});

test('the setting of the engine is saved without a key left empty; the key is forgotten, the engine tried', async () => {
  const described = { engine: 'openai', engines: ['openai'], api_key: 'unset', base_url: 'https://api.test/v1', model: 'm' };
  let found: unknown = { engine: 'openai', reachable: true, tools: true };
  const { model, sources, now, asked } = setup({ '/api/app/engine': () => described, '/api/app/probe': () => found });
  model.start();
  sources[0].send('app', none);
  model.editEngine({ engine: 'openai', base_url: ' https://api.test/v1 ', model: 'm' });
  await model.saveEngine();
  assert.deepEqual(asked('/api/app/engine')[0].body, { engine: 'openai', base_url: 'https://api.test/v1', model: 'm' });
  assert.deepEqual([now().engineSaid, now().engineTone, now().server!.engine, now().engineDraft!.api_key], ['Motore salvato.', 'good', described, '']);
  model.editEngine({ api_key: 'k' });
  await model.probeEngine();
  assert.deepEqual([asked('/api/app/probe')[0].body.api_key, now().engineSaid, now().engineTone], ['k', 'openai: risponde, chiama gli strumenti.', 'good']);
  found = { engine: 'openai', reachable: false, detail: 'rifiutato' };
  await model.probeEngine();
  assert.deepEqual([now().engineSaid, now().engineTone], ['openai: non risponde. rifiutato', 'bad']);
  await model.forgetKey();
  assert.deepEqual([asked('/api/app/engine')[1].body, now().engineSaid], [{ api_key: '' }, 'Chiave rimossa.']);
});

test('the engine is asked each thing once at a time, and is busy with it until it is answered, well or not', async () => {
  let refuse = (_error: Error) => {};
  const { model, now, asked } = setup({
    '/api/app/probe': () => new Promise((_resolve, reject) => { refuse = reject; }),
    '/api/app/engine': () => ({ engine: 'claude', engines: ['claude'] }),
  });
  const tried = model.probeEngine();
  await model.probeEngine();
  assert.deepEqual([asked('/api/app/probe').length, now().engineBusy, now().engineSaid], [1, ['probe'], 'Prova in corso…']);
  await model.saveEngine();
  assert.deepEqual([now().engineBusy, now().engineSaid, now().server], [['probe'], 'Motore salvato.', null]);  // no frame yet: the state is still to be read
  refuse(new Error('caduto'));
  await tried;
  assert.deepEqual([now().engineBusy, now().engineSaid, now().engineTone], [[], 'caduto', 'bad']);
});

test('a question is asked once and its answer read to the end', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const answers = [{ events: [{ kind: 'tool', name: 'cerca', arguments: 'token' }], next: 1, state: 'running', text: '', cause: null },
    { events: [{ kind: 'tool', name: 'leggi', arguments: { riga: 1 } }], next: 2, state: 'done', text: 'Lo firma auth.ts', cause: null }];
  const { model, sources, now, asked } = setup({ '/api/app/ask': () => ({}), '/api/app/answer': call => answers[Number(call.query.get('after'))] });
  model.setQuestion('Dove si firma il token?');
  model.ask();
  model.ask();
  await turn();
  assert.deepEqual([asked('/api/app/ask').map(call => call.body), now().asked!.state], [[{ question: 'Dove si firma il token?' }], 'running']);
  t.mock.timers.tick(700);
  await turn();
  assert.deepEqual(now().asked, { state: 'done', text: 'Lo firma auth.ts', tools: ['cerca token', 'leggi {"riga":1}'], cause: null });
  model.start();
  sources[0].send('app', { ...none, asked: { state: 'running', question: 'altra' } });  // asked elsewhere: nothing is sent
  await model.ask();
  assert.equal(asked('/api/app/ask').length, 1);
});

test('what is asked of the run is answered by its new state, or said as an error', async () => {
  let answer: unknown = fails(500, 'collegamento non riuscito');
  const { model, notices, sources, now } = setup({ '/api/app/link': () => answer });
  model.start();
  sources[0].send('app', ready);
  await model.findLinks();
  assert.deepEqual(notices, [{ text: 'collegamento non riuscito', kind: 'error' }]);
  answer = { ...ready, links: { state: 'running' } };
  await model.findLinks();
  assert.equal(now().server!.links!.state, 'running');
  assert.equal(model.explorerUrl(), '/?token=segreto&run=r1');
  assert.equal(model.markUrl('next.js & co'), '/api/app/mark?id=next.js+%26+co&token=segreto');
});
