// The App's model: its state, what it asks the server and what it keeps in the browser. It draws nothing: the page reads
// `snapshot()`, which is one object until something changes, and calls the functions below.
import { graphKey, openWithout, rootOf, shownOpen } from './graph.ts';
import type { Graph } from './graph.ts';
import { accessible, preferredBranch, repositorySlug, urlError } from './repository.ts';
import { isAsking } from './run.ts';
import { causeOf, createServer, isBusy } from './server.ts';
import type { AppState, Checked, Cursors, Engine, EventsFrame, Host, RunEvent } from './server.ts';
import { complete, ctx, ORPHAN_WRITES, slug, viewingPaths } from './snapshot.ts';
import type { Asked, EngineDraft, PathPage, PathResult, PremapFound, Snapshot, Symbols } from './snapshot.ts';
import { readKept, STORAGE } from './storage.ts';
import type { Kept, Place, Stage } from './storage.ts';

const RETRY_MS = 2000;      // a busy server is asked again after this
const RECONNECT_MS = 4000;  // and a stream that said nothing is opened again after this
const ANSWER_MS = 700;

type Answer = { events: { kind: string; name?: string; arguments?: unknown }[]; next: number; state: string; text: string; cause: string | null };
export type Model = ReturnType<typeof createModel>;

export function createModel(host: Host) {
  const { get, post, stream } = createServer(host);
  const stored = readKept(host.storage);
  let storageAvailable = stored.available;
  let now: Snapshot = {
    kept: stored.kept, server: null, serverError: '',
    checked: null, checkedUrl: '', branch: '', checking: false, checkError: '', selecting: false, selectError: '',
    premap: null, premapError: '', graph: null, graphError: '', graphLoading: false, pathPage: null, symbols: null, events: [],
    engineDraft: null, engineSaid: '', engineTone: '', question: '', asked: null, notices: [],
  };
  const listeners = new Set<() => void>();
  // What no screen draws: which run and groups the last answers are of, the check in course, and where the stream arrived.
  let premapRun = '', graphRun = '', generation = 0, noticeId = 0;
  let eventsRun = '', cursors: Cursors = { after: 0, pipeline_after: 0, pulse_after: 0 };

  function save() { try { host.storage().setItem(STORAGE, JSON.stringify(now.kept)); } catch { storageAvailable = false; } }
  function set(patch: Partial<Snapshot>) {
    now = { ...now, ...patch };
    if (patch.kept) save();
    for (const listener of [...listeners]) listener();
  }
  const keep = (patch: Partial<Kept>) => set({ kept: { ...now.kept, ...patch } });

  // A result is a notice, which goes by itself; an error stays until it is dismissed.
  function say(text: string, kind?: 'error') {
    noticeId += 1;  // not crypto.randomUUID, which a page served over plain http does not have
    set({ notices: [...now.notices, { id: String(noticeId), text, ...(kind && { kind }) }] });
  }
  const dismiss = (id: string) => set({ notices: now.notices.filter(notice => notice.id !== id) });
  const busy = (error: unknown) => { if (!isBusy(error)) return false; say(causeOf(error) + ', riprovo'); return true; };

  // -- the server --------------------------------------------------------------------------------------------------

  // The page observes `/api/stream`: the app's state (`app`) first and whenever it changes, the run's events (`snapshot`,
  // `update`) as they are written. A stream lasts a minute and opens again from the cursors; nothing asks on a timer.
  function observe() {
    const source = stream(eventsRun, cursors);
    let heard = false;
    source.addEventListener('app', message => { heard = true; applyState(JSON.parse(message.data)); });
    for (const name of ['snapshot', 'update']) source.addEventListener(name, message => { heard = true; applyEvents(JSON.parse(message.data)); });
    source.addEventListener('failure', message => { heard = false; set({ serverError: JSON.parse(message.data).error }); });
    source.onerror = () => {  // the stream ended, or the server did not answer it: after a frame again at once
      source.close();
      if (!heard) set({ serverError: now.serverError || 'lo stream del server non risponde' });
      setTimeout(observe, heard ? 0 : RECONNECT_MS);
    };
  }

  function applyState(found: AppState) {
    const before = now.server, c = ctx({ server: found });
    const linked = before !== null && before.links?.state !== 'done' && found.links?.state === 'done';  // new links: a new graph
    const mappingChanged = before !== null && found.mapped?.state !== 'running' && JSON.stringify(before.mapped) !== JSON.stringify(found.mapped);
    const patch: { -readonly [K in keyof Snapshot]?: Snapshot[K] } = { server: found, serverError: '' };
    let kept = now.kept, ready = false;
    if (now.engineDraft === null) patch.engineDraft = { ...found.engine, api_key: '' };
    if (c && kept.runId !== c.run_id) {  // what the browser kept belongs to another run
      kept = { ...kept, analysisStage: kept.runId && kept.analysisStage !== 'repository' ? 'premap' : kept.analysisStage,
        runId: c.run_id, treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '', graphOpen: [] };
      patch.premap = patch.graph = null;
    }
    if (!c && kept.runId) kept = { ...kept, runId: '' };
    if (now.selecting && found.job?.state !== 'preparing') {
      patch.selecting = false;
      if (c && found.job?.state === 'ready') { ready = true; kept = { ...kept, analysisStage: 'premap' }; }
    }
    if (linked || mappingChanged || now.pathPage?.run !== c?.run_id) patch.pathPage = null;
    if (kept !== now.kept) patch.kept = kept;
    set(patch);
    if (ready && c) say(`Contesto pronto: ${slug(c)} · ${c.branch}`);
    if (linked && c) loadGraph();
    loadViews();
    settle();
  }

  function applyEvents(found: EventsFrame) {
    const run = found.run_events;
    const past: readonly RunEvent[] = eventsRun === run.run_id ? now.events : [];
    eventsRun = run.run_id;
    cursors = { after: run.next_cursor, pipeline_after: run.pipeline.next_cursor, pulse_after: found.pulse.next_cursor };
    const grown = run.pipeline.events.some(e => e.kind === 'step.finished' || e.kind === 'graph.ready') && ctx(now)?.run_id === run.run_id;
    set({ events: [...past, ...run.events.map(e => ({ ...e, run: true })), ...run.pipeline.events], ...(grown && { pathPage: null }) });
    if (grown) {
      loadViews();
      if (drawsGraph()) loadGraph();
    }
    settle();
  }

  const drawsGraph = () => now.kept.analysisStage !== 'repository' || now.kept.screen === 'graph';

  function loadViews() {  // what the stage on screen draws, read once a run
    const c = ctx(now);
    if (c && graphRun !== graphKey(c.run_id, now.kept) && drawsGraph()) loadGraph();
    if (viewingPaths(now) && !now.pathPage) loadPathPage();
    if (c && premapRun !== c.run_id && ['premap', 'synthesis'].includes(now.kept.analysisStage)) loadPremap();
  }

  // What the analysis can show: without a context the repository alone, and the synthesis once the pipeline is over.
  function settle() {
    if (!now.server || now.kept.screen !== 'analysis') return;
    const stage = now.kept.analysisStage;
    const shown: Stage = !ctx(now) ? 'repository' : stage === 'synthesis' && !complete(now) ? 'analysis' : stage;
    if (shown !== stage) keep({ analysisStage: shown });
  }

  async function loadPremap(): Promise<void> {
    const run = ctx(now)?.run_id;
    if (!run || premapRun === run) return;
    premapRun = run;
    set({ premapError: '', premap: null });
    try {
      const found = await get<PremapFound>('/api/app/premap');
      if (ctx(now)?.run_id !== run) return;
      set({ premap: { ...found, dependencies: found.units.flatMap(u => u.dependencies.map(d => ({ ...d, unit: u.name }))) } });
    } catch (error) {
      premapRun = '';
      if (busy(error)) { setTimeout(loadPremap, RETRY_MS); return; }
      set({ premapError: causeOf(error) });
    }
  }

  async function loadGraph(): Promise<void> {
    const run = ctx(now)?.run_id, open = shownOpen(now.kept), key = graphKey(run, now.kept);
    if (!run || now.graphLoading) return;
    set({ graphLoading: true, ...(now.graph?.open.length && !open.length ? { graph: null } : {}) });  // the first grouping is never drawn from an opened graph
    try {
      const found = await get<Graph>('/api/app/graph' + (open.length ? `?${new URLSearchParams({ open: JSON.stringify(open) })}` : ''));
      if (ctx(now)?.run_id !== run) return;
      graphRun = key;
      const graphRoot = rootOf(found, now.kept.graphRoot);  // a group just opened keeps the focus inside it
      set({ graph: found, graphError: '', symbols: null, ...(graphRoot !== now.kept.graphRoot && { kept: { ...now.kept, graphRoot } }) });
    } catch (error) {
      if (busy(error)) { setTimeout(loadGraph, RETRY_MS); return; }  // what is drawn stays
      const cause = causeOf(error);
      const refused = open.length > 0 && /to open: (".*")$/.exec(cause);  // a group the run no longer shows: dropped, the others stay
      if (refused) {
        graphRun = '';
        keep({ graphOpen: openWithout(now.kept.graphOpen, now.graph, JSON.parse(refused[1])) });
        say(cause, 'error');
      } else { graphRun = key; set({ graphError: cause }); }
    } finally {
      set({ graphLoading: false });
    }
    if (ctx(now)?.run_id === run && graphRun !== graphKey(run, now.kept)) return loadGraph();  // the groups wanted changed meanwhile
  }

  // -- the repository ----------------------------------------------------------------------------------------------

  function setRepositoryUrl(repositoryUrl: string) {
    generation += 1;  // the answer of a check in course is of another address
    set({ kept: { ...now.kept, repositoryUrl }, checked: null, checking: false, checkError: '', selectError: '' });
  }

  async function verifyRepositoryUrl(): Promise<void> {
    if (now.checking) return;
    const url = now.kept.repositoryUrl.trim();
    if (!repositorySlug(url)) { set({ checkError: urlError(url) }); return; }
    const mine = ++generation;
    set({ checking: true, checkError: '', checked: null, selectError: '' });
    try {
      const found = await post<Checked>('/api/app/check', { url });
      if (mine !== generation) return;
      set({ checking: false, checked: found, checkedUrl: url, ...(found.state === 'accessible' && { branch: preferredBranch(found.branches, found.default) }) });
      if (found.state === 'accessible') say(`${found.repository.owner}/${found.repository.name}: ${found.branches.length} branch letti da GitHub.`);
    } catch (error) {
      if (mine === generation) set({ checking: false, checkError: causeOf(error) });
    }
  }

  async function selectRepository(): Promise<void> {
    if (!accessible(now) || now.selecting) return;
    set({ selectError: '' });
    try {
      const server = await post<AppState>('/api/app/select', { url: now.checkedUrl, branch: now.branch });
      premapRun = graphRun = '';
      set({ server, selecting: true, premap: null, graph: null });
    } catch (error) {
      set({ selectError: causeOf(error) });
    }
    settle();
  }

  // -- the synthesis: the paths, page by page ------------------------------------------------------------------------

  async function loadPathPage(id: PathPage['id'] = null, offset = 0, previous: PathPage | null = null): Promise<void> {
    const run = ctx(now)?.run_id;
    if (!run) return;
    const page: PathPage = { run, id, offset, previous };
    set({ pathPage: page });
    const query = new URLSearchParams({ offset: String(offset) });
    if (id === ORPHAN_WRITES) query.set('effects', '1');
    else if (typeof id === 'string') query.set('id', id);
    try {
      const result = await get<PathResult>(`/api/app/paths?${query}`);
      if (result.run_id && result.run_id !== page.run) throw new Error('Il run attivo è cambiato.');
      const rows = id === ORPHAN_WRITES ? result.effects : id ? result.steps : result.cards;
      if (!Array.isArray(rows)) throw new Error(result.reason || 'La pagina dei percorsi non è disponibile.');
      page.result = result;
    } catch (error) { page.error = causeOf(error); }
    // A page left while it was read keeps what came: the pages after it go back to it.
    if (now.pathPage === page) set({ pathPage: { ...page } });
  }
  const openPaths = (id: PathPage['id']) => loadPathPage(id, 0, now.pathPage);
  function nextPaths() {
    const page = now.pathPage, next = page?.result?.next_offset;
    if (page && typeof next === 'number') loadPathPage(page.id, next, page);
  }
  const previousPaths = () => set({ pathPage: now.pathPage?.previous ?? null });
  const retryPaths = () => { const page = now.pathPage; if (page) loadPathPage(page.id, page.offset, page.previous); };
  function listPaths() {  // back to the entries, read again when the page left had failed
    const failed = Boolean(now.pathPage?.error);
    let page = now.pathPage;
    while (page?.id) page = page.previous;
    if (!page || failed) loadPathPage();
    else set({ pathPage: page });
  }

  // -- where the person looks, and the graph ---------------------------------------------------------------------------

  function navigate(screen: Place) {
    keep({ screen });
    loadViews();  // the graph screen draws its level, the analysis the first one
    settle();
  }
  function selectStage(analysisStage: Stage) {
    keep({ screen: 'analysis', analysisStage });
    loadViews();
    settle();
  }
  function openGroup(id: string) {
    keep({ graphOpen: [...new Set([...now.kept.graphOpen, id])], graphRoot: id });
    loadGraph();
  }
  function closeGroup(id: string) {  // the group closed is chosen again
    keep({ graphOpen: openWithout(now.kept.graphOpen, now.graph, id), graphRoot: id });
    loadGraph();
  }
  function showNode(graphRoot: string) {  // from another screen: the node and what is next to it
    keep({ graphRoot, graphOpen: [], graphDepth: '1', graphSearch: '' });
    navigate('graph');
  }
  function showFullGraph() {
    keep({ graphDepth: 'all', graphSearch: '', graphOpen: [] });
    navigate('graph');
  }
  function clearGraphFilters() {
    keep({ graphSearch: '', graphDepth: 'all', graphDirection: 'both', graphKind: 'all' });
    say('Filtri azzerati: tutti i gruppi del grafo sono visibili.');
  }

  async function askSymbols(file: string): Promise<void> {
    const mine = () => now.symbols?.file === file;
    set({ symbols: { file, loading: true } });
    try {
      const found = await get<Symbols>(`/api/app/symbols?${new URLSearchParams({ file })}`);
      if (mine()) set({ symbols: found });
    } catch (error) {
      if (isBusy(error)) { setTimeout(() => { if (mine()) askSymbols(file); }, RETRY_MS); return; }
      if (mine()) set({ symbols: { file, error: causeOf(error) } });
    }
  }
  // The symbols of a file, once for each time it is chosen.
  const loadSymbols = (file: string) => { if (now.symbols?.file !== file) askSymbols(file); };

  // -- the engine and the questions ----------------------------------------------------------------------------------

  // The setting in the form: a key left empty is left out, and the server keeps the one it has.
  function engineBody() {
    const draft: EngineDraft = now.engineDraft ?? { api_key: '' }, key = draft.api_key.trim();
    return { engine: draft.engine || null, base_url: (draft.base_url ?? '').trim(), model: (draft.model ?? '').trim(), ...(key && { api_key: key }) };
  }
  const editEngine = (patch: Partial<EngineDraft>) => set({ engineDraft: { ...(now.engineDraft ?? { api_key: '' }), ...patch } });
  const withEngine = (engine: Engine) => ({ server: { ...now.server, engine } });

  async function saveEngine(): Promise<void> {
    try {
      const described = await post<Engine>('/api/app/engine', engineBody());
      set({ ...withEngine(described), engineDraft: { ...described, api_key: '' }, engineSaid: 'Motore salvato.', engineTone: 'good' });
    } catch (error) { set({ engineSaid: causeOf(error), engineTone: 'bad' }); }
  }
  async function forgetKey(): Promise<void> {
    try {
      const described = await post<Engine>('/api/app/engine', { api_key: '' });
      set({ ...withEngine(described), engineTone: 'good',
        engineSaid: described.api_key === 'set' ? 'Chiave rimossa: resta quella dell’ambiente.' : 'Chiave rimossa.' });
    } catch (error) { set({ engineSaid: causeOf(error), engineTone: 'bad' }); }
  }
  async function probeEngine(): Promise<void> {
    set({ engineSaid: 'Prova in corso…', engineTone: '' });
    try {
      const found = await post<{ engine: string; reachable: boolean; tools: boolean | null; detail?: string }>('/api/app/probe', engineBody());
      const tools = found.tools === null ? 'strumenti tramite MCP' : found.tools ? 'chiama gli strumenti' : 'non ha chiamato lo strumento';
      set({ engineSaid: found.reachable ? `${found.engine}: risponde, ${tools}.` : `${found.engine}: non risponde. ${found.detail || ''}`,
        engineTone: found.reachable && found.tools !== false ? 'good' : 'bad' });
    } catch (error) { set({ engineSaid: causeOf(error), engineTone: 'bad' }); }
  }

  async function ask(): Promise<void> {
    if (isAsking(now)) return;  // a busy button's submit, from the keyboard, does nothing
    let asked: Asked = { state: 'running', text: '', tools: [], cause: null };
    const show = (patch: Partial<Asked>) => { asked = { ...asked, ...patch }; set({ asked }); };
    show({});
    try {
      await post('/api/app/ask', { question: now.question });
      for (let after = 0; ;) {
        const found = await get<Answer>(`/api/app/answer?after=${after}`);
        after = found.next;
        const tools = found.events.filter(e => e.kind === 'tool').map(e => `${e.name} ${typeof e.arguments === 'string' ? e.arguments : JSON.stringify(e.arguments ?? '')}`);
        show({ state: found.state, text: found.text, cause: found.cause, tools: [...asked.tools, ...tools] });
        if (found.state !== 'running') break;
        await new Promise(resolve => setTimeout(resolve, ANSWER_MS));
      }
    } catch (error) { show({ state: 'failed', cause: causeOf(error) }); }
  }

  // The server's answer to these is its new state.
  const act = (path: string) => post<AppState>(path, {}).then(applyState).catch(error => say(causeOf(error), 'error'));

  return {
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    snapshot: () => now,
    // Once, when the page opens: what is kept is written (a storage that refuses it is said), and the server is observed.
    start() {
      save();
      if (!storageAvailable) say('Archiviazione del browser non disponibile: le scelte durano questa apertura.');
      observe();
    },
    say, dismiss, keep, navigate, selectStage,
    explorerUrl: () => `/?${new URLSearchParams({ token: host.token, run: ctx(now)?.run_id ?? '' })}`,
    setRepositoryUrl, verifyRepositoryUrl, selectRepository, setBranch: (branch: string) => set({ branch }),
    retryPremap() { premapRun = ''; loadPremap(); },
    retryGraph() { graphRun = ''; set({ graphError: '' }); loadGraph(); },
    selectNode: (graphRoot: string) => keep({ graphRoot }), openGroup, closeGroup, showNode, showFullGraph, clearGraphFilters,
    loadSymbols, retrySymbols: askSymbols,
    openPaths, nextPaths, previousPaths, listPaths, retryPaths,
    retryPass: () => act('/api/app/retry'), findLinks: () => act('/api/app/link'),
    editEngine, saveEngine, probeEngine, forgetKey, setQuestion: (question: string) => set({ question }), ask,
  };
}
