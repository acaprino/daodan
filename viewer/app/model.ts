// The App's model: its state, what it asks the server and what it keeps in the browser. It draws nothing: the page reads
// `snapshot()`, which is one object until something changes, and calls the functions below.
import type { Notify } from '@acaprino/imago';
import { causeOf, whenFree } from '../src/http.ts';
import { markAddress } from '../src/marks.ts';
import { FAILURE } from '../src/words.ts';
import { confirmBody, confirmedWords, draftOf, isReady, removeBody, removedWords, setBody, setWords, workOf } from './commands.ts';
import type { CommandDraft } from './commands.ts';
import { groupKey, pendingGroup, repliedWords, replyBody } from './egress.ts';
import type { Reply } from './egress.ts';
import { isAsking } from './engine.ts';
import { endName, graphKey, openWithout, rootOf, shownOpen } from './graph.ts';
import type { Graph } from './graph.ts';
import { firstStep, onPath, REPOSITORY, SHOWS_PREMAP } from './path.ts';
import { accessible, preferredBranch, repositorySlug, urlError } from './repository.ts';
import { editBody, pathError } from './project.ts';
import type { Conflict, Field, Keep, Project, Revision } from './project.ts';
import { createServer } from './server.ts';
import type { AppState, Checked, Command, CommandKind, Cursors, Engine, EventsFrame, Host, RunEvent } from './server.ts';
import { ctx, ORPHAN_WRITES, slug, viewingPaths } from './snapshot.ts';
import type { Asked, EngineDraft, EngineWork, PathPage, PathResult, PremapFound, Snapshot, Symbols } from './snapshot.ts';
import { readKept, STORAGE } from './storage.ts';
import type { Kept, Place, Stage } from './storage.ts';

const RECONNECT_MS = 4000;  // a stream that said nothing is opened again after this
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
    premap: null, premapError: '', graph: null, graphError: '', graphLoading: false, groupWanted: stored.kept.screen === 'graph',
    engineFromStep: false, pathPage: null, symbols: null, events: [],
    engineDraft: null, engineSaid: '', engineTone: '', engineBusy: [], question: '', asked: null,
    hostsHidden: [], hostsReplying: '', project: null, projectError: '', projectBusy: '', commandDraft: null, commandBusy: '',
  };
  const listeners = new Set<() => void>();
  // What no screen draws: which run and groups the last answers are of, the question whose answer is awaited, the check and the
  // choice in course, and where the stream arrived.
  let premapRun = '', graphRun = '', premapAsked = 0, graphAsked = 0;
  let generation = 0, choosing = false;
  let eventsRun = '', cursors: Cursors = { after: 0, pipeline_after: 0, pulse_after: 0 };

  function save() { try { host.storage().setItem(STORAGE, JSON.stringify(now.kept)); } catch { storageAvailable = false; } }
  function set(patch: Partial<Snapshot>) {
    now = { ...now, ...patch };
    if (patch.kept) save();
    for (const listener of [...listeners]) listener();
  }
  const keep = (patch: Partial<Kept>) => set({ kept: { ...now.kept, ...patch } });

  let notify: Notify = () => undefined;  // the shell's, from `start` on
  // A result takes the place of the same one still there; an error stays until it is closed.
  const say = (text: string, kind?: 'error') => notify(text, kind ? { kind } : { id: text });
  const sayBusy = () => say(FAILURE.retried);

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
    // A step of the plan of the same run is done, or up to date, now: what it wrote is read again.
    const was = new Map((before?.run?.plan?.steps ?? []).map(step => [step.id, step.state] as const));
    const grown = before !== null && c !== null && ctx({ server: before })?.run_id === c.run_id && (found.run?.plan?.steps ?? []).some(step =>
      (step.state === 'done' || step.state === 'skipped') && was.get(step.id) !== step.state);
    const patch: { -readonly [K in keyof Snapshot]?: Snapshot[K] } = { server: found, serverError: '' };
    let kept = now.kept, ready = false;
    if (now.engineDraft === null) patch.engineDraft = { ...found.engine, api_key: '' };
    if (kept.runId !== (c?.run_id ?? '')) Object.assign(patch, dropRun());
    const first = firstStep({ server: found });  // the first step of the plan, once the state has one
    if (c && kept.runId !== c.run_id) {  // what the browser kept belongs to another run
      kept = { ...kept, analysisStage: kept.runId && kept.analysisStage !== REPOSITORY ? first ?? REPOSITORY : kept.analysisStage,
        runId: c.run_id, treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '', graphOpen: [] };
    }
    if (!c && kept.runId) kept = { ...kept, runId: '' };
    if (now.selecting && !choosing && found.job?.state !== 'preparing') {  // until the choice is answered, a frame is of what was before it
      patch.selecting = false;
      if (c && found.job?.state === 'ready') {
        ready = true;
        if (now.checked && first) kept = { ...kept, analysisStage: first };  // not while another address is being written
      }
    }
    if (linked || grown || mappingChanged || now.pathPage?.run !== c?.run_id) patch.pathPage = null;
    const recorded = before !== null && found.project?.state === 'done' && found.project.rev !== before.project?.rev;  // a new analysis
    if (kept !== now.kept) patch.kept = kept;
    set(patch);
    if (ready && c) say(`Contesto pronto: ${slug(c)} · ${c.branch}`);
    if (recorded && c) reread();
    else if (c && (linked || (grown && drawsGraph()))) loadGraph();
    loadViews();
    settle();
  }

  function applyEvents(found: EventsFrame) {
    const run = found.run_events;
    const past: readonly RunEvent[] = eventsRun === run.run_id ? now.events : [];
    eventsRun = run.run_id;
    cursors = { after: run.next_cursor, pipeline_after: run.pipeline.next_cursor, pulse_after: found.pulse.next_cursor };
    // The events are the run's chronicle: the views are read again when the plan says a step is done, not on an event.
    set({ events: [...past, ...run.events.map(e => ({ ...e, run: true })), ...run.pipeline.events] });
    settle();
  }

  const drawsGraph = () => now.kept.analysisStage !== REPOSITORY || now.kept.screen === 'graph';

  function loadViews() {  // what the stage on screen draws, read once a run
    const c = ctx(now);
    if (c && graphRun !== graphKey(c.run_id, now.kept) && drawsGraph()) loadGraph();
    if (viewingPaths(now) && !now.pathPage) loadPathPage();
    if (c && premapRun !== c.run_id && SHOWS_PREMAP.includes(now.kept.analysisStage)) loadPremap();
  }

  // What the analysis can show: without a context the repository alone, and a step only while the plan has it.
  function settle() {
    if (!now.server || now.kept.screen !== 'analysis') return;
    const stage = now.kept.analysisStage;
    const shown: Stage = !ctx(now) || !onPath(now, stage) ? REPOSITORY : stage;
    if (shown !== stage) keep({ analysisStage: shown });
  }

  // Another run is in view, or the same one chosen again: what was read of it goes, and an answer still to come changes nothing.
  function dropRun(): Partial<Snapshot> {
    premapRun = graphRun = '';
    premapAsked += 1;
    graphAsked += 1;
    return { premap: null, premapError: '', graph: null, graphError: '', graphLoading: false, symbols: null, project: null, projectError: '' };
  }

  async function loadPremap(): Promise<void> {
    const run = ctx(now)?.run_id;
    if (!run || premapRun === run) return;
    const mine = ++premapAsked, wanted = () => mine === premapAsked;
    premapRun = run;
    set({ premapError: '', premap: null });
    try {
      const found = await whenFree(() => get<PremapFound>('/api/app/premap'), sayBusy, wanted);
      if (found && wanted()) set({ premap: { ...found, dependencies: found.units.flatMap(u => u.dependencies.map(d => ({ ...d, unit: u.name }))) } });
    } catch (error) {
      if (!wanted()) return;
      premapRun = '';
      set({ premapError: causeOf(error) });
    }
  }

  async function loadGraph(): Promise<void> {
    const run = ctx(now)?.run_id;
    if (!run || now.graphLoading) return;
    const mine = ++graphAsked, wanted = () => mine === graphAsked;
    let open = shownOpen(now.kept), key = graphKey(run, now.kept);
    const ask = () => {  // a busy server is asked again for the groups that are open by then
      open = shownOpen(now.kept);
      key = graphKey(run, now.kept);
      return get<Graph>('/api/app/graph' + (open.length ? `?${new URLSearchParams({ open: JSON.stringify(open) })}` : ''));
    };
    // The first grouping is never drawn from an opened graph; on the graph screen the last group to close stays drawn until the answer.
    const left = now.kept.screen !== 'graph' && !open.length && now.graph !== null && now.graph.open.length > 0;
    set({ graphLoading: true, ...(left && { graph: null }) });
    try {
      const found = await whenFree(ask, sayBusy, wanted);
      if (!found || !wanted()) return;
      graphRun = key;
      const graphRoot = rootOf(found, now.kept.graphRoot);  // a group just opened keeps the focus inside it
      set({ graph: found, graphError: '', symbols: null, ...(graphRoot !== now.kept.graphRoot && { kept: { ...now.kept, graphRoot } }) });
      loadProject();
    } catch (error) {
      if (!wanted()) return;
      const cause = causeOf(error);
      const refused = open.length > 0 && /to open: (".*")$/.exec(cause);  // a group the run no longer shows: dropped, the others stay
      if (refused) {
        const id: string = JSON.parse(refused[1]);
        graphRun = '';
        keep({ graphOpen: openWithout(now.kept.graphOpen, now.graph, id) });
        say(`Il gruppo «${now.graph ? endName(now.graph, id) : id}» non si può più aprire nel grafo di questo run.`, 'error');
      } else { graphRun = key; set({ graphError: cause }); }
    } finally {
      if (wanted()) set({ graphLoading: false });
    }
    if (wanted() && graphRun !== graphKey(run, now.kept)) return loadGraph();  // the groups wanted changed meanwhile
  }

  // -- the project file: its history and conflicts, and what the person changes by hand ---------------------------------

  async function loadProject(): Promise<void> {
    const run = ctx(now)?.run_id, wanted = () => ctx(now)?.run_id === run;
    if (!run) return;
    try {
      const [history, found] = await Promise.all([
        whenFree(() => get<{ head: number; revisions: Revision[] }>('/api/app/project/history'), () => undefined, wanted),
        whenFree(() => get<{ conflicts: Conflict[] }>('/api/app/project/conflicts'), () => undefined, wanted),
      ]);
      if (history && found && wanted()) set({ project: { ...history, conflicts: found.conflicts } satisfies Project, projectError: '' });
    } catch (error) {
      if (wanted()) set({ project: null, projectError: causeOf(error) });
    }
  }
  // The graph and the file read again: a choice made, a conflict settled, a file received or a new analysis. The file is read with
  // the graph (`loadGraph`), once; a graph still to come is of the file before, so it is dropped and asked again.
  function reread() {
    graphRun = '';
    graphAsked += 1;
    set({ graphLoading: false });
    loadGraph();
  }
  // One at a time; what came of it is said, a refusal stays until it is closed. True when the server took it.
  async function projectWork(work: string, path: string, body: unknown, done: string): Promise<boolean> {
    if (now.projectBusy) return false;
    set({ projectBusy: work });
    try {
      await post(path, body);
      say(done);
      return true;
    } catch (error) {
      say(causeOf(error), 'error');
      return false;
    } finally {
      set({ projectBusy: '' });
    }
  }
  async function changeNode(ref: string, field: Field, value: string): Promise<boolean> {
    const ok = await projectWork('edit', '/api/app/project/edit', editBody(now.project, ref, field, value), 'Modifica salvata nel file di progetto.');
    if (ok) reread();
    return ok;
  }
  async function resolveConflict(conflict: number, keep: Keep): Promise<void> {
    if (await projectWork(`resolve ${conflict}`, '/api/app/project/resolve', { conflict_id: conflict, keep }, 'Conflitto risolto.')) reread();
  }
  // A file received from someone: it takes the place of the one of the repository it names, with its history.
  async function openProject(path: string): Promise<boolean> {
    if (pathError(path)) { say(pathError(path), 'error'); return false; }
    const ok = await projectWork('open', '/api/app/project/open', { path: path.trim() }, 'File di progetto aperto: le sue modifiche sono nella cronologia.');
    if (ok) reread();
    return ok;
  }
  async function saveProject(path: string): Promise<boolean> {
    if (pathError(path)) { say(pathError(path), 'error'); return false; }
    return projectWork('save', '/api/app/project/save', { path: path.trim() }, `Copia del file di progetto salvata in ${path.trim()}.`);
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
      const result = await whenFree(() => get<PathResult>(`/api/app/paths?${query}`), sayBusy, () => ctx(now)?.run_id === run);
      if (!result) return;
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
    set({ kept: { ...now.kept, screen }, groupWanted: screen === 'graph', engineFromStep: false });
    loadViews();  // the graph screen draws its level, the analysis the first one
    settle();
  }
  function chooseEngine() {  // from a step that needs it
    navigate('engine');
    set({ engineFromStep: true });
  }
  function selectStage(analysisStage: Stage) {
    set({ kept: { ...now.kept, screen: 'analysis', analysisStage }, groupWanted: false, engineFromStep: false });
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
  const toggleGroup = (id: string) => (now.graph?.open.some(group => group.id === id) ? closeGroup : openGroup)(id);  // by what is drawn
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
      const found = await whenFree(() => get<Symbols>(`/api/app/symbols?${new URLSearchParams({ file })}`), () => undefined, mine);
      if (found && mine()) set({ symbols: found });
    } catch (error) {
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
        const found = (await whenFree(() => get<Answer>(`/api/app/answer?after=${after}`), sayBusy))!;
        after = found.next;
        const tools = found.events.filter(e => e.kind === 'tool').map(e => `${e.name} ${typeof e.arguments === 'string' ? e.arguments : JSON.stringify(e.arguments ?? '')}`);
        show({ state: found.state, text: found.text, cause: found.cause, tools: [...asked.tools, ...tools] });
        if (found.state !== 'running') break;
        await new Promise(resolve => setTimeout(resolve, ANSWER_MS));
      }
    } catch (error) { show({ state: 'failed', cause: causeOf(error) }); }
  }

  // -- the hosts the project's tools asked to reach -------------------------------------------------------------------

  // The person's answer to the group in view, for all its hosts; one at a time. The server's answer is its new state, without the
  // group; a refusal is said and the window stays.
  async function replyHosts(reply: Reply): Promise<void> {
    const group = pendingGroup(now.server?.egress, now.hostsHidden);
    if (!group || now.hostsReplying) return;
    const body = replyBody(group, reply);
    set({ hostsReplying: reply });
    try {
      const found = await post<AppState>('/api/app/egress', body);
      set({ hostsReplying: '' });
      applyState(found);
      say(repliedWords(reply, body.hosts));
    } catch (error) {
      set({ hostsReplying: '' });
      say(causeOf(error), 'error');
    }
  }
  // The window closed without an answer: the group waits, and the palette offers it again (`showHosts`).
  function hideHosts() {
    const group = pendingGroup(now.server?.egress, now.hostsHidden);
    if (group && !now.hostsReplying) set({ hostsHidden: [...now.hostsHidden, groupKey(group)] });
  }
  const showHosts = () => set({ hostsHidden: [] });

  // -- the commands the person states for a folder of the project -----------------------------------------------------

  // The window of the commands, its form on a kind and a folder; it does not close while something is being sent.
  const showCommand = (kind: CommandKind, root: string) => set({ commandDraft: draftOf(kind, root, now.server?.commands) });
  function hideCommand() { if (!now.commandBusy) set({ commandDraft: null }); }
  function editCommand(patch: Partial<CommandDraft>) { if (now.commandDraft) set({ commandDraft: { ...now.commandDraft, ...patch } }); }
  // One at a time. The server's answer is its new state; a refusal is said and the window stays. True when the server took it.
  async function commandWork(work: string, body: unknown, done: string): Promise<boolean> {
    if (now.commandBusy) return false;
    set({ commandBusy: work });
    try {
      const found = await post<AppState>('/api/app/command', body);
      set({ commandBusy: '' });
      applyState(found);
      say(done);
      return true;
    } catch (error) {
      set({ commandBusy: '' });
      say(causeOf(error), 'error');
      return false;
    }
  }
  // The person's command, from the form: the window closes once the server has it.
  async function setCommand(): Promise<void> {
    const draft = now.commandDraft;
    if (!draft || !isReady(draft)) return;
    if (await commandWork('set', setBody(draft, now.server?.commands), setWords(draft))) set({ commandDraft: null });
  }
  const confirmCommand = (command: Command) => commandWork(workOf('confirm', command), confirmBody(command), confirmedWords(command));
  const removeCommand = (command: Command) => commandWork(workOf('remove', command), removeBody(command), removedWords(command));

  // The server's answer to these is its new state.
  const act = (path: string) => post<AppState>(path, {}).then(applyState).catch(error => say(causeOf(error), 'error'));

  return {
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    snapshot: () => now,
    // Once, when the page opens: what is kept is written (a storage that refuses it is said), and the server is observed. `shell`
    // says the notices.
    start(shell: Notify) {
      notify = shell;
      save();
      if (!storageAvailable) say('Archiviazione del browser non disponibile: le scelte durano questa apertura.');
      observe();
    },
    keep: choose, navigate, chooseEngine, selectStage,
    explorerUrl: () => `/?${new URLSearchParams({ token: host.token, run: ctx(now)?.run_id ?? '' })}`,
    markUrl: (mark: string | null | undefined) => markAddress('/api/app/mark', mark, host.token),
    setRepositoryUrl, verifyRepositoryUrl, selectRepository, setBranch: (branch: string) => set({ branch }),
    retryPremap() { premapRun = ''; loadPremap(); },
    retryGraph() { graphRun = ''; set({ graphError: '' }); loadGraph(); },
    selectNode: (id: string) => chosen(id), groupShown: () => set({ groupWanted: false }), openGroup, closeGroup, toggleGroup,
    showNode, showFullGraph, clearGraphFilters,
    loadSymbols, retrySymbols: askSymbols,
    openPaths, nextPaths, previousPaths, listPaths, retryPaths,
    retryPass: () => act('/api/app/retry'), findLinks: () => act('/api/app/link'),
    editEngine, saveEngine, probeEngine, forgetKey, setQuestion: (question: string) => set({ question }), ask,
    replyHosts, hideHosts, showHosts,
    showCommand, hideCommand, editCommand, setCommand, confirmCommand, removeCommand,
    changeNode, resolveConflict, openProject, saveProject,
  };
}
