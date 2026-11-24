// The App's model: its state, what it asks the server and what it keeps in the browser. It draws nothing: the page reads
// `snapshot()`, which is one object until something changes, and calls the functions below.
import { graphKey, openWithout, rootOf, shownOpen } from './graph.ts';
import type { Graph } from './graph.ts';
import { accessible, preferredBranch, repositorySlug, urlError } from './repository.ts';
import { isAsking } from './run.ts';
import { causeOf, createServer, isBusy } from './server.ts';
import type { AppState, Checked, Cursors, Engine, EventsFrame, Host, RunEvent } from './server.ts';
import { complete, ctx, ORPHAN_WRITES, slug, viewingPaths } from './snapshot.ts';
import type { Asked, EngineDraft, EngineWork, PathPage, PathResult, PremapFound, Snapshot, Symbols } from './snapshot.ts';
import { readKept, STORAGE } from './storage.ts';
import type { Kept, Place, Stage } from './storage.ts';

const RETRY_MS = 2000;      // a busy server is asked again after this
const RECONNECT_MS = 4000;  // and a stream that said nothing is opened again after this
const ANSWER_MS = 700;
const BUSY = 'server.busy';  // the key of its notice

type Answer = { events: { kind: string; name?: string; arguments?: unknown }[]; next: number; state: string; text: string; cause: string | null };
export type Model = ReturnType<typeof createModel>;

export function createModel(host: Host) {
  const { get, post, stream } = createServer(host);
  const stored = readKept(host.storage);
  let storageAvailable = stored.available;
  let now: Snapshot = {
    kept: stored.kept, server: null, serverError: '',
    checked: null, checkedUrl: '', branch: '', checking: false, checkError: '', selecting: false, selectError: '',
    premap: null, premapError: '', graph: null, graphError: '', graphLoading: false, groupWanted: stored.kept.screen === 'graph',
    pathPage: null, symbols: null, events: [],
    engineDraft: null, engineSaid: '', engineTone: '', engineBusy: [], question: '', asked: null, notices: [],
  };
  const listeners = new Set<() => void>();
  // What no screen draws: which run and groups the last answers are of, the question whose answer is awaited, whether a busy server
  // is to be asked again, the check and the choice in course, and where the stream arrived.
  let premapRun = '', graphRun = '', premapAsked = 0, graphAsked = 0, premapWaits = false, graphWaits = false;
  let generation = 0, choosing = false, noticeId = 0;
  let eventsRun = '', cursors: Cursors = { after: 0, pipeline_after: 0, pulse_after: 0 };

  function save() { try { host.storage().setItem(STORAGE, JSON.stringify(now.kept)); } catch { storageAvailable = false; } }
  function set(patch: Partial<Snapshot>) {
    now = { ...now, ...patch };
    if (patch.kept) save();
    for (const listener of [...listeners]) listener();
  }
  const keep = (patch: Partial<Kept>) => set({ kept: { ...now.kept, ...patch } });

  // A result is a notice, which goes by itself and takes the place of the one of its key; an error stays until it is dismissed.
  function say(text: string, kind?: 'error', key = text) {
    noticeId += 1;  // not crypto.randomUUID, which a page served over plain http does not have
    const id = String(noticeId);
    set({ notices: kind ? [...now.notices, { id, text, kind }] : [...now.notices.filter(notice => notice.key !== key), { id, text, key }] });
  }
  const dismiss = (id: string) => set({ notices: now.notices.filter(notice => notice.id !== id) });
  // That the server is busy is said once, whoever found it so: while its notice is there, an attempt says nothing more.
  function busy(error: unknown): boolean {
    if (!isBusy(error)) return false;
    if (!now.notices.some(notice => notice.key === BUSY)) say(causeOf(error) + ', riprovo', undefined, BUSY);
    return true;
  }

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
    if (kept.runId !== (c?.run_id ?? '')) Object.assign(patch, dropRun());
    if (c && kept.runId !== c.run_id) {  // what the browser kept belongs to another run
      kept = { ...kept, analysisStage: kept.runId && kept.analysisStage !== 'repository' ? 'premap' : kept.analysisStage,
        runId: c.run_id, treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '', graphOpen: [] };
    }
    if (!c && kept.runId) kept = { ...kept, runId: '' };
    if (now.selecting && !choosing && found.job?.state !== 'preparing') {  // until the choice is answered, a frame is of what was before it
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

  // Another run is in view, or the same one chosen again: what was read of it goes, and an answer still to come changes nothing.
  function dropRun(): Partial<Snapshot> {
    premapRun = graphRun = '';
    premapAsked += 1;
    graphAsked += 1;
    return { premap: null, premapError: '', graph: null, graphError: '', graphLoading: false, symbols: null };
  }

  async function loadPremap(): Promise<void> {
    const run = ctx(now)?.run_id;
    if (!run || premapRun === run || premapWaits) return;
    const mine = ++premapAsked;
    premapRun = run;
    set({ premapError: '', premap: null });
    try {
      const found = await get<PremapFound>('/api/app/premap');
      if (mine !== premapAsked) return;
      set({ premap: { ...found, dependencies: found.units.flatMap(u => u.dependencies.map(d => ({ ...d, unit: u.name }))) } });
    } catch (error) {
      if (mine !== premapAsked) return;
      premapRun = '';
      if (busy(error)) {
        premapWaits = true;
        setTimeout(() => { premapWaits = false; loadPremap(); }, RETRY_MS);
        return;
      }
      set({ premapError: causeOf(error) });
    }
  }

  async function loadGraph(): Promise<void> {
    const run = ctx(now)?.run_id, open = shownOpen(now.kept), key = graphKey(run, now.kept);
    if (!run || now.graphLoading || graphWaits) return;
    const mine = ++graphAsked;
    set({ graphLoading: true, ...(now.graph?.open.length && !open.length ? { graph: null } : {}) });  // the first grouping is never drawn from an opened graph
    try {
      const found = await get<Graph>('/api/app/graph' + (open.length ? `?${new URLSearchParams({ open: JSON.stringify(open) })}` : ''));
      if (mine !== graphAsked) return;
      graphRun = key;
      const graphRoot = rootOf(found, now.kept.graphRoot);  // a group just opened keeps the focus inside it
      set({ graph: found, graphError: '', symbols: null, ...(graphRoot !== now.kept.graphRoot && { kept: { ...now.kept, graphRoot } }) });
    } catch (error) {
      if (mine !== graphAsked) return;
      if (busy(error)) {  // what is drawn stays
        graphWaits = true;
        setTimeout(() => { graphWaits = false; loadGraph(); }, RETRY_MS);
        return;
      }
      const cause = causeOf(error);
      const refused = open.length > 0 && /to open: (".*")$/.exec(cause);  // a group the run no longer shows: dropped, the others stay
      if (refused) {
        graphRun = '';
        keep({ graphOpen: openWithout(now.kept.graphOpen, now.graph, JSON.parse(refused[1])) });
        say(cause, 'error');
      } else { graphRun = key; set({ graphError: cause }); }
    } finally {
      if (mine === graphAsked) set({ graphLoading: false });
    }
    if (mine === graphAsked && graphRun !== graphKey(run, now.kept)) return loadGraph();  // the groups wanted changed meanwhile
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
    choosing = true;
    set({ selecting: true, selectError: '' });  // before the request: a second press asks nothing
    try {
      const server = await post<AppState>('/api/app/select', { url: now.checkedUrl, branch: now.branch });
      set({ server, ...dropRun() });
    } catch (error) {
      set({ selecting: false, selectError: causeOf(error) });
    }
    choosing = false;
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

  // What the person chose on a screen: other groups open are another graph.
  function choose(patch: Partial<Kept>) {
    keep(patch);
    if (patch.graphOpen) loadViews();
  }
  function navigate(screen: Place) {
    set({ kept: { ...now.kept, screen }, groupWanted: screen === 'graph' });
    loadViews();  // the graph screen draws its level, the analysis the first one
    settle();
  }
  function selectStage(analysisStage: Stage) {
    set({ kept: { ...now.kept, screen: 'analysis', analysisStage }, groupWanted: false });
    loadViews();
    settle();
  }
  // A group chosen on the graph screen, which shows its details.
  const chosen = (graphRoot: string, graphOpen = now.kept.graphOpen) => set({ kept: { ...now.kept, graphRoot, graphOpen }, groupWanted: true });
  function openGroup(id: string) {
    chosen(id, [...new Set([...now.kept.graphOpen, id])]);
    loadGraph();
  }
  function closeGroup(id: string) {  // the group closed is chosen again
    chosen(id, openWithout(now.kept.graphOpen, now.graph, id));
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
    const asked: Symbols = { file, loading: true };
    const mine = () => now.symbols === asked;  // not asked again, nor dropped with the graph it was asked on
    set({ symbols: asked });
    try {
      const found = await get<Symbols>(`/api/app/symbols?${new URLSearchParams({ file })}`);
      if (mine()) set({ symbols: found });
    } catch (error) {
      if (isBusy(error)) { setTimeout(() => { if (mine()) askSymbols(file); }, RETRY_MS); return; }
      if (mine()) set({ symbols: { file, error: causeOf(error) } });
    }
  }
  // The symbols of a file, once for each time it is chosen; a new graph drops them, and the details ask again (`useSymbols`).
  const loadSymbols = (file: string) => { if (now.symbols?.file !== file) askSymbols(file); };

  // -- the engine and the questions ----------------------------------------------------------------------------------

  // The setting in the form: a key left empty is left out, and the server keeps the one it has.
  function engineBody() {
    const draft: EngineDraft = now.engineDraft ?? { api_key: '' }, key = draft.api_key.trim();
    return { engine: draft.engine || null, base_url: (draft.base_url ?? '').trim(), model: (draft.model ?? '').trim(), ...(key && { api_key: key }) };
  }
  const editEngine = (patch: Partial<EngineDraft>) => set({ engineDraft: { ...(now.engineDraft ?? { api_key: '' }), ...patch } });
  // Before the first frame there is no state to put it in: the engine comes with the frame.
  const withEngine = (engine: Engine): Partial<Snapshot> => (now.server ? { server: { ...now.server, engine } } : {});

  // What the form asks, one of each at a time: a busy button's press, from the keyboard, does nothing. What came of it is said.
  async function engineWork(work: EngineWork, run: () => Promise<Partial<Snapshot>>): Promise<void> {
    if (now.engineBusy.includes(work)) return;
    set({ engineBusy: [...now.engineBusy, work] });
    let came: Partial<Snapshot>;
    try { came = await run(); } catch (error) { came = { engineSaid: causeOf(error), engineTone: 'bad' }; }
    set({ ...came, engineBusy: now.engineBusy.filter(other => other !== work) });
  }
  const saveEngine = () => engineWork('save', async () => {
    const described = await post<Engine>('/api/app/engine', engineBody());
    return { ...withEngine(described), engineDraft: { ...described, api_key: '' }, engineSaid: 'Motore salvato.', engineTone: 'good' };
  });
  const forgetKey = () => engineWork('forget', async () => {
    const described = await post<Engine>('/api/app/engine', { api_key: '' });
    return { ...withEngine(described), engineTone: 'good',
      engineSaid: described.api_key === 'set' ? 'Chiave rimossa: resta quella dell’ambiente.' : 'Chiave rimossa.' };
  });
  const probeEngine = () => engineWork('probe', async () => {
    set({ engineSaid: 'Prova in corso…', engineTone: '' });
    const found = await post<{ engine: string; reachable: boolean; tools: boolean | null; detail?: string }>('/api/app/probe', engineBody());
    const tools = found.tools === null ? 'strumenti tramite MCP' : found.tools ? 'chiama gli strumenti' : 'non ha chiamato lo strumento';
    return { engineSaid: found.reachable ? `${found.engine}: risponde, ${tools}.` : `${found.engine}: non risponde. ${found.detail || ''}`,
      engineTone: found.reachable && found.tools !== false ? 'good' : 'bad' };
  });

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
    say, dismiss, keep: choose, navigate, selectStage,
    explorerUrl: () => `/?${new URLSearchParams({ token: host.token, run: ctx(now)?.run_id ?? '' })}`,
    setRepositoryUrl, verifyRepositoryUrl, selectRepository, setBranch: (branch: string) => set({ branch }),
    retryPremap() { premapRun = ''; loadPremap(); },
    retryGraph() { graphRun = ''; set({ graphError: '' }); loadGraph(); },
    selectNode: (id: string) => chosen(id), groupShown: () => set({ groupWanted: false }), openGroup, closeGroup,
    showNode, showFullGraph, clearGraphFilters,
    loadSymbols, retrySymbols: askSymbols,
    openPaths, nextPaths, previousPaths, listPaths, retryPaths,
    retryPass: () => act('/api/app/retry'), findLinks: () => act('/api/app/link'),
    editEngine, saveEngine, probeEngine, forgetKey, setQuestion: (question: string) => set({ question }), ask,
  };
}
