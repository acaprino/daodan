import '@acaprino/imago/css/imago.css';
import { buttonHtml, confirm, createRegistry, fileTree, footerKeys, formatKeys, graphLegendHtml, iconButtonHtml, iconMarkup as icon, inspector, LOADING_DELAY_MS, metric, notify, noteHtml, openMenu, PALETTE_COMMAND, panelStateHtml, renderShellFrame, roving, SEARCH_COMMAND, segmentedControl, setProgress, shellFrameHtml, showAfter, stepList, tabNavigationHtml, textFieldHtml, titlebarHtml } from '@acaprino/imago/ui';
import { graphView } from '@acaprino/imago/graph';
import { applyStored, graphControls, mountPage, storageOrNull } from '../src/page';


const shell = document.querySelector('.im-shell');
const page = () => document.querySelector('#main > .im-panel-body');
applyStored(document.documentElement, storageOrNull());
const registry = createRegistry();
let diagram, diagramHost, diagramKey, previewVersion;

// The app's page: the journey of the mockup (repository, pre-map, analysis, synthesis and graph) over the local server.
// The server's state is the truth; the browser keeps only where the person was looking.
const token = new URLSearchParams(location.search).get('token') ?? '';
const auth = { 'X-Daodan-Token': token };
async function answer(response) {
  const body = await response.json().catch(() => ({}));
  if (response.status === 503) throw Object.assign(new Error('Daodan è occupato'), { busy: true });  // another helper holds the project now
  if (!response.ok) throw new Error(body.error || `il server ha risposto ${response.status}`);
  return body;
}
const get = path => fetch(path, { headers: auth, cache: 'no-store' }).then(answer);
const post = (path, body) => fetch(path, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(answer);

const STORAGE = 'daodan-app-v2';  // v2: the graph opens whole, so what v1 kept of its filters is dropped
const defaults = { screen: 'analysis', analysisStage: 'repository', repositoryUrl: '', runId: '', treeMode: 'directories', treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '', graphOpen: [], graphDirection: 'both', graphDepth: 'all', graphKind: 'all' };
let state = { ...defaults }, storageAvailable = true;
try { const stored = JSON.parse(localStorage.getItem(STORAGE) || 'null'); if (stored && typeof stored === 'object') state = { ...defaults, ...stored }; } catch { storageAvailable = false; }
if (!['analysis', 'graph', 'engine'].includes(state.screen)) state.screen = 'analysis';
if (!['repository', 'premap', 'analysis', 'synthesis'].includes(state.analysisStage)) state.analysisStage = 'repository';
if (!Array.isArray(state.graphOpen) || state.graphOpen.some(id => typeof id !== 'string')) state.graphOpen = [];

// What the server answered: never kept in the browser.
let server = null, serverError = '';
let checked = null, checkedUrl = '', branch = '', checking = false, checkError = '', selectError = '', selecting = false, generation = 0;
let PREMAP = null, premapRun = '', premapError = '';
let GRAPH = null, graphRun = '', graphError = '', graphLoading = false;
let pathPage = null;  // current evidence page; previous pages belong to the same run and rules
const orphanWrites = Symbol('orphan writes');  // separate view, never sent to the server as a card id
let SYMBOLS = null;  // the inspector's file: its symbols and calls, asked when the file is selected
let events = [], cursors = { after: 0, pipeline_after: 0, pulse_after: 0 }, eventsRun = '';
let engineDraft = null, engineSaid = '', engineTone = '', question = '', asked = null, shown = '';
const FINAL = ['fresh', 'unavailable', 'failed', 'off'];
const STEPS = [['scan', 'Scan · inventario e moduli'], ['stack', 'Stack · tecnologie e librerie'], ['analyze', 'Analyze · analyzer per linguaggio'], ['dynamic', 'Dynamic · osservazione dei test'], ['union', 'Union · collegamento dei grafi']];
const STEP = Object.fromEntries(STEPS.map(([id, label]) => [id, label.split(' · ')[0]]));

function save() { try { localStorage.setItem(STORAGE, JSON.stringify(state)); } catch { storageAvailable = false; } }
function esc(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

// Ctrl+F: the search of the screen in view; a screen without one says so.
function searchView() {
  const field = document.querySelector('#graph-search, #premap-search');
  if (field) field.focus(); else notice('Questa schermata non ha una ricerca.');
}

// A result is a notice, which goes by itself; an error stays until it is dismissed and starts with the word.
const notice = message => notify(shell, message, { dismissLabel: 'Chiudi' });
const failure = message => notify(shell, message, { tone: 'err', errorWord: 'Errore', dismissLabel: 'Chiudi' });

// A load shows its waiting panel only when it takes longer than LOADING_DELAY_MS; one that ends sooner shows nothing.
const waits = new Set(), timers = {};
function startWait(name) {
  timers[name]?.();
  waits.delete(name);
  timers[name] = showAfter(LOADING_DELAY_MS, () => { waits.add(name); render(); });
}
function endWait(name) { timers[name]?.(); timers[name] = null; waits.delete(name); }
const panelHtml = (inner, busy = false) => `<section class="im-panel"${busy ? ' aria-busy="true"' : ''}><div class="im-panel-body">${inner}</div></section>`;
function loadingPanel(name, rows = 3) { return waits.has(name) ? panelHtml(panelStateHtml({ kind: 'loading', rows }), true) : ''; }
const retryButton = (action, label = 'Riprova') => buttonHtml(label, action, { icon: 'reload' });
const failedPanel = (text, action) => panelHtml(panelStateHtml({ kind: 'error', text, retryHtml: retryButton(action), errorWord: 'Errore' }));
const busyIcon = (busy, name) => busy ? '<span class="im-spinner" aria-hidden="true"></span>' : icon(name);

function heading(eyebrow, title, description, action = '') { return `<div class="im-split im-cluster"><div><p class="im-kicker">${eyebrow}</p><h1>${title}</h1><p>${description}</p></div>${action}</div>`; }
function selectOptions(items, value) { return items.map(([v, label]) => `<option value="${esc(v)}" ${String(v) === String(value) ? 'selected' : ''}>${esc(label)}</option>`).join(''); }
function number(n) { return Number(n || 0).toLocaleString('it-IT'); }

function ctx() { return server?.context || null; }
function slug(c = ctx()) { return c ? c.repository.owner + '/' + c.repository.name : ''; }
function pass() { return server?.run?.pass || {}; }
function complete() { return Boolean(ctx()) && FINAL.includes(pass().state); }
function explorerUrl() { return `/?token=${encodeURIComponent(token)}&run=${encodeURIComponent(ctx()?.run_id || '')}`; }

// -- the server --------------------------------------------------------------------------------------------------

// The page observes `/api/stream`: the app's state (`app`) first and whenever it changes, the run's events
// (`snapshot`, `update`) as they are written. A stream lasts a minute and opens again from the cursors; nothing asks
// on a timer.
function observe() {
  const source = new EventSource('/api/stream?' + new URLSearchParams({ token, max_seconds: 60, run: eventsRun, ...cursors }));
  let heard = false;
  source.addEventListener('app', message => { heard = true; applyState(JSON.parse(message.data)); });
  for (const name of ['snapshot', 'update']) source.addEventListener(name, message => { heard = true; applyEvents(JSON.parse(message.data)); });
  source.addEventListener('failure', message => { heard = false; serverError = JSON.parse(message.data).error; render(); });
  source.onerror = () => {  // the stream ended, or the server did not answer it: after a frame again at once
    source.close();
    if (!heard) { serverError ||= 'lo stream del server non risponde'; render(); }
    setTimeout(observe, heard ? 0 : 4000);
  };
}

function applyState(found) {
  const linked = server && server.links?.state !== 'done' && found.links?.state === 'done';  // new links: a new graph
  const mappingChanged = server && found.mapped?.state !== 'running' &&
    JSON.stringify(server.mapped) !== JSON.stringify(found.mapped);
  server = found;
  serverError = '';
  endWait('server');
  const c = ctx();
  if (engineDraft === null) engineDraft = { ...server.engine, api_key: '' };
  if (c && state.runId !== c.run_id) {  // what the browser kept belongs to another run
    if (state.runId && state.analysisStage !== 'repository') state.analysisStage = 'premap';
    Object.assign(state, { runId: c.run_id, treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '', graphOpen: [] });
    PREMAP = GRAPH = null;
  }
  if (!c) state.runId = '';
  if (selecting && server.job.state !== 'preparing') {
    selecting = false;
    if (c && server.job.state === 'ready') {
      state.analysisStage = 'premap';
      notice('Contesto pronto: ' + slug() + ' · ' + c.branch);
    }
  }
  if (linked || mappingChanged || pathPage?.run !== c?.run_id) pathPage = null;
  if (linked && c) loadGraph();
  loadViews();
  show();
}

function applyEvents(found) {
  const run = found.run_events;
  if (eventsRun !== run.run_id) { events = []; eventsRun = run.run_id; }
  cursors = { after: run.next_cursor, pipeline_after: run.pipeline.next_cursor, pulse_after: found.pulse.next_cursor };
  events.push(...run.events.map(e => ({ ...e, run: true })), ...run.pipeline.events);
  const grown = run.pipeline.events.some(e => e.kind === 'step.finished' || e.kind === 'graph.ready');
  if (grown && ctx()?.run_id === run.run_id) { pathPage = null; loadViews(); }
  if (grown && ctx()?.run_id === run.run_id && (state.analysisStage !== 'repository' || state.screen === 'graph')) loadGraph();
  show();
}

function viewingPaths() { return state.screen === 'analysis' && state.analysisStage === 'synthesis' && complete(); }

function loadViews() {  // what the stage on screen draws, read once a run
  const c = ctx();
  if (c && graphRun !== graphKey() && (state.analysisStage !== 'repository' || state.screen === 'graph')) loadGraph();
  if (viewingPaths() && !pathPage) loadPathPage();
  if (c && premapRun !== c.run_id && ['premap', 'synthesis'].includes(state.analysisStage)) loadPremap();
}

function show() {  // draws again what a frame changed
  const signature = JSON.stringify([server?.job, ctx()?.run_id, pass(), server?.run?.progress, events.length, server?.engine, server?.mcp_ready, server?.asked, server?.links, server?.mapped]);
  if (signature === shown) return;
  shown = signature;
  if (state.screen === 'analysis' && state.analysisStage === 'analysis' && document.getElementById('run-title')) updateAnalysisRun();
  else render();
}

async function loadPremap() {
  const run = ctx()?.run_id;
  if (!run || premapRun === run) return;
  premapRun = run; premapError = ''; PREMAP = null; startWait('premap');
  try {
    const found = await get('/api/app/premap');
    if (ctx()?.run_id !== run) return;
    PREMAP = { ...found, dependencies: found.units.flatMap(u => u.dependencies.map(d => ({ ...d, unit: u.name }))) };
  } catch (error) {
    premapRun = '';
    if (error.busy) { notice(error.message + ', riprovo'); setTimeout(loadPremap, 2000); return; }
    premapError = error.message;
  } finally {
    endWait('premap');
  }
  render();
}

// The graph opens its groups in place: the graph screen asks with the groups it holds open (`graphOpen`), the
// analysis's preview and synthesis with none. The server keeps each answer until the run's data change.
function shownOpen() { return state.screen === 'graph' ? [...state.graphOpen].sort() : []; }
function graphKey() { return (ctx()?.run_id || '') + ' ' + JSON.stringify(shownOpen()); }
const outside = n => Number(n.location === 'external');  // a group of the project before an external node
const opens = n => n.files.length > 0 || (n.members || []).length > 0;  // files, or the projects or symbols it holds
function closeGroup(id) {  // with the groups open inside it: `open` lists a parent before what it holds
  const gone = new Set([id]);
  for (const group of GRAPH?.open || []) if (gone.has(group.parent)) gone.add(group.id);
  state.graphOpen = state.graphOpen.filter(item => !gone.has(item));
}

async function loadGraph() {
  const run = ctx()?.run_id, open = shownOpen(), key = graphKey();
  if (!run || graphLoading) return;
  graphLoading = true; startWait('graph');
  if (GRAPH?.open.length && !open.length) GRAPH = null;  // the first grouping is never drawn from an opened graph
  try {
    const found = await get('/api/app/graph' + (open.length ? '?' + new URLSearchParams({ open: JSON.stringify(open) }) : ''));
    if (ctx()?.run_id !== run) return;
    GRAPH = found; graphRun = key; graphError = ''; SYMBOLS = null;
    if (!GRAPH.nodes.some(n => n.id === state.graphRoot)) {  // a group just opened keeps the focus inside it
      const related = id => GRAPH.edges.filter(e => e.source === id || e.target === id).length;  // the node with most relations first
      const inside = GRAPH.nodes.filter(n => n.group === state.graphRoot);
      state.graphRoot = [...(inside.length ? inside : GRAPH.nodes)].sort((a, b) => outside(a) - outside(b) || related(b.id) - related(a.id) || b.files.length - a.files.length)[0]?.id || '';
    }
  } catch (error) {
    if (error.busy) { notice(error.message + ', riprovo'); setTimeout(loadGraph, 2000); return; }  // what is drawn stays
    const refused = open.length && /to open: (".*")$/.exec(error.message);  // a group the run no longer shows: dropped, the others stay
    if (refused) { closeGroup(JSON.parse(refused[1])); graphRun = ''; failure(error.message); }
    else { graphError = error.message; graphRun = key; }
  } finally {
    graphLoading = false; endWait('graph');
  }
  if (ctx()?.run_id === run && graphRun !== graphKey()) return loadGraph();  // the groups wanted changed meanwhile
  if (state.screen === 'analysis' && state.analysisStage === 'analysis' && document.getElementById('build-viewport')) updateAnalysisRun();
  else render();
}

// -- the repository -----------------------------------------------------------------------------------------------

function preferredBranch(branches, fallback) {
  const names = branches.map(b => b.name);
  return names.includes('main') ? 'main' : names.includes('master') ? 'master' : fallback;
}

function repositorySlug() {
  const value = state.repositoryUrl.trim();
  const normalized = value.startsWith('github.com/') ? 'https://' + value : value;
  const match = /^https:\/\/github\.com\/([A-Za-z0-9-]+)\/([A-Za-z0-9._-]+)\/?$/i.exec(normalized);
  const name = match?.[2].replace(/\.git$/, '');
  return match && name && !['.', '..'].includes(name) ? match[1] + '/' + name : null;
}

async function verifyRepositoryUrl() {
  if (checking) return;
  if (!repositorySlug()) {
    checkError = state.repositoryUrl.trim() ? 'Usa un URL https://github.com/proprietario/repository, senza percorsi aggiuntivi.' : 'Inserisci l’URL GitHub della repository.';
    render();
    document.getElementById('repository-url').focus();
    return;
  }
  const mine = ++generation, url = state.repositoryUrl.trim();
  checking = true; checkError = ''; checked = null; selectError = '';
  render();
  try {
    const found = await post('/api/app/check', { url });
    if (mine !== generation) return;
    checked = found; checkedUrl = url;
    if (found.state === 'accessible') branch = preferredBranch(found.branches, found.default);
  } catch (error) {
    if (mine !== generation) return;
    checkError = error.message;
  }
  checking = false;
  render();
  if (checked?.state === 'accessible') notice(`${checked.repository.owner}/${checked.repository.name}: ${checked.branches.length} branch letti da GitHub.`);
}

async function selectRepository() {
  if (checked?.state !== 'accessible' || selecting) return;
  selectError = '';
  try {
    server = await post('/api/app/select', { url: checkedUrl, branch });
    selecting = true;
    PREMAP = GRAPH = null; premapRun = graphRun = '';
  } catch (error) {
    selectError = error.message;
  }
  render();
}

function repositoryContext() {
  const c = ctx();
  if (!c) return '';
  return `<div class="im-inset im-stack"><div>${icon('code')}<strong>${esc(slug(c))}</strong><span class="im-chip">${icon('branch')}${esc(c.branch)}</span><code>${esc(c.commit.slice(0, 12))}</code><span class="im-muted im-caption">Pubblica, senza login</span></div><p>Checkout in sola lettura del commit <code>${esc(c.commit.slice(0, 12))}</code>; run <code>${esc(c.run_id)}</code>. Nessun file del progetto viene eseguito.</p><button class="im-btn im-btn--ghost im-btn--sm" data-analysis-stage="repository">Cambia repository o branch ${icon('arrow')}</button></div>`;
}

function preparation() {
  const job = server?.job;
  if (!job || job.state === 'idle') return '';
  const step = { checkout: 'Checkout del branch', snapshot: 'Snapshot e pre-mappa' }[job.step] || job.step || '';
  if (job.state === 'preparing') return `<span class="im-loader" role="status"><span class="im-spinner" aria-hidden="true"></span>Preparazione in corso: ${esc(step)}${job.detail ? ' · ' + esc(job.detail) : ''}.</span>`;
  if (job.state === 'failed') return noteHtml({ tone: 'err', title: `Preparazione non riuscita (${step}).`, message: job.detail });
  return '';
}

// Why the branch and the button that opens the pre-map cannot be used now.
const repoWhy = (repo, checking, preparing) => preparing ? 'Preparazione in corso.' : checking ? 'Verifica in corso.' : 'Verifica prima l’accesso alla repository.';

function repositoryScreen() {
  const repo = checked?.state === 'accessible' ? checked : null;
  const preparing = server?.job.state === 'preparing';
  const feedback = checked && !repo ? {
    not_accessible: 'Repository non accessibile senza login: potrebbe non esistere o richiedere permessi. Il login GitHub non è disponibile in questa versione.',
    network: 'Errore di rete: riprova la verifica. Il login non risolve un errore di connessione.',
    empty: 'La repository non ha branch: non c’è nulla da analizzare.',
  }[checked.state] + (checked.detail ? ' (' + checked.detail + ')' : '') : '';
  const c = ctx();
  return noteHtml({ icon: 'info', title: 'Repository GitHub pubblica', message: 'Daodan legge i branch e scarica quello scelto in sola lettura; nulla del progetto viene eseguito su questa macchina. Il login GitHub non è disponibile in questa versione.' }) + `<div class="im-auto-grid"><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Repository GitHub</h2><span class="im-chip">Selezione del progetto</span></div><div class="im-inset im-stack"><form id="repository-form" novalidate><div class="im-field"><label class="im-field-label" for="repository-url">URL GitHub</label><span class="im-input"><input id="repository-url" type="url" value="${esc(state.repositoryUrl)}" placeholder="https://github.com/proprietario/repository" aria-describedby="repository-url-help repository-error repository-access-feedback" ${checkError ? 'aria-invalid="true"' : ''}></span><p id="repository-url-help" class="im-muted im-caption">Inserisci l’URL e verifica l’accesso. Senza login si aprono solo repository pubbliche.</p><p id="repository-error" class="im-field-error" role="alert">${checkError ? 'Errore: ' + esc(checkError) : ''}</p><p id="repository-access-feedback" class="im-muted" role="status">${esc(feedback)}</p></div><button class="im-btn" type="submit" id="verify-repository" ${checking ? 'aria-busy="true"' : ''}>${busyIcon(checking, 'check')}Verifica accesso</button></form>
  <div><div class="im-field"><label class="im-field-label" for="repository-branch">Branch da analizzare</label><select class="im-select" id="repository-branch" ${!repo || checking || preparing ? `disabled title="${esc(repoWhy(repo, checking, preparing))}"` : ''}>${repo ? selectOptions(repo.branches.map(b => [b.name, b.name + ' · ' + b.commit.slice(0, 12)]), branch) : '<option>Verifica prima l’accesso</option>'}</select></div><p class="im-muted im-caption">Preferenza automatica: <code>main</code>, poi <code>master</code>, altrimenti il branch predefinito della repository.</p>${repo ? `<p>${repo.branches.length} branch letti ora da GitHub; predefinito <code>${esc(repo.default || '—')}</code>.</p>` : ''}</div><div class="im-section">${preparation()}${selectError ? noteHtml({ tone: 'err', title: 'Selezione non riuscita.', message: selectError }) : ''}</div><div class="im-split im-cluster"><p class="im-muted im-caption">Un altro repository o branch prepara un nuovo checkout; lo stesso commit riusa l’analisi già fatta.</p><button class="im-btn im-btn--primary" data-action="use-repository" id="use-repository" ${preparing ? 'aria-busy="true"' : !repo || checking ? `disabled title="${esc(repoWhy(repo, checking, preparing))}"` : ''}>${preparing ? '<span class="im-spinner" aria-hidden="true"></span>Apri pre-mappa' : 'Apri pre-mappa ' + icon('arrow')}</button></div></div></section>
  <aside class="im-stack"><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Accesso GitHub</h2>${icon('code')}</div><div class="im-inset im-stack"><span class="im-chip">Non connesso</span><h3>Login non disponibile</h3><p class="im-muted">In questa versione Daodan legge solo repository pubbliche, senza account. Un accesso negato non dimostra che la repository sia privata: può non esistere o mancare un permesso.</p></div></section><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Contesto attivo</h2></div><div class="im-inset im-stack">${c ? `<ul class="im-detail-list"><li><strong>Repository</strong><span><code>${esc(slug(c))}</code></span></li><li><strong>Branch e commit</strong><span><code>${esc(c.branch)}</code> · <code>${esc(c.commit.slice(0, 12))}</code></span></li><li><strong>Run</strong><span><code>${esc(c.run_id)}</code></span></li></ul><button class="im-btn im-btn--ghost im-btn--sm" data-analysis-stage="premap">Torna alla pre-mappa ${icon('arrow')}</button>` : `<p class="im-muted">${preparing ? 'Preparazione in corso: il contesto sarà pronto alla fine del checkout e dello snapshot.' : 'Nessuna repository selezionata sul server.'}</p>`}</div></section></aside></div>`;
}

// -- the analysis workspace ---------------------------------------------------------------------------------------

function analysisWorkspace() {
  if (!server) return heading('Codebase intelligence', 'Analisi del repository', 'Lettura dello stato del server…') + (serverError ? serverNote() : loadingPanel('server'));
  if (!ctx() && state.analysisStage !== 'repository') state.analysisStage = 'repository';
  if (state.analysisStage === 'synthesis' && !complete()) state.analysisStage = 'analysis';
  const stage = state.analysisStage;
  const titles = {
    repository: ['Da GitHub all’analisi', 'Scegli repository e branch.', 'Inserisci un URL pubblico, verifica l’accesso e scegli il branch da analizzare.'],
    premap: ['Prima dell’analisi', 'Conosci il punto di partenza.', 'Tecnologie dichiarate, file e unità tecniche: una vista del repository prima di interpretarne il comportamento.'],
    analysis: ['Pipeline di analisi', 'Il grafo prende forma.', 'Segui passi, analyzer, avanzamento ed eventi del run.'],
    synthesis: ['Risultati dell’analisi', 'Dalla mappa alla comprensione.', 'Gruppi, relazioni e lacune del grafo di questo run.'],
  };
  const [eyebrow, title, description] = titles[stage];
  const action = stage === 'premap' ? `<button class="im-btn im-btn--primary" data-analysis-stage="analysis">${icon('play')}Segui l’analisi</button>`
    : stage === 'synthesis' ? `<button class="im-btn im-btn--primary" data-action="open-full-graph">${icon('graph')}Esplora il grafo completo</button>`
      : stage === 'analysis' ? `<button class="im-btn" data-action="open-explorer">${icon('external')}Apri l’esploratore</button>` : '';
  return heading(eyebrow, title, description, action) + '<nav id="stage-nav" aria-label="Percorso di analisi"></nav>' + (serverError ? serverNote() : '') +
    (stage === 'repository' ? repositoryScreen() : repositoryContext() + (stage === 'premap' ? premapScreen() : stage === 'synthesis' ? synthesisScreen() : analysisRunScreen()));
}

const serverNote = () => noteHtml({ tone: 'err', title: 'Server non raggiungibile.', message: serverError });

function selectStage(id) {
  state.screen = 'analysis';
  state.analysisStage = id;
  loadViews();
  render();
}

function mountStageNav() {
  const host = document.getElementById('stage-nav');
  if (!host) return;
  const stages = [['repository', 'Repository', 'GitHub e branch'], ['premap', 'Pre-mappa', 'Inventario e tecnologie'],
    ['analysis', 'Analisi', 'Pipeline e costruzione'], ['synthesis', 'Sintesi e grafo', 'Risultati e lacune']];
  host.append(stepList(document, 'Percorso di analisi', stages.map(([id, label, detail]) => ({
    label, detail, state: state.analysisStage === id ? 'now' : 'todo',
    action: { id: 'stage-' + id, disabled: (id !== 'repository' && !ctx()) || (id === 'synthesis' && !complete()),
      activate: () => selectStage(id) },
  }))));
  for (const [id] of stages) {  // a stage that cannot be opened says why
    const button = document.getElementById('stage-' + id);
    if (button?.disabled) button.title = !ctx() ? 'Scegli prima una repository e un branch.' : 'La sintesi è pronta quando la pipeline è conclusa.';
  }
}

// -- 1. pre-map ----------------------------------------------------------------------------------------------------

function premapSourceLine() {
  const c = ctx();
  return `<div class="im-content-toolbar im-split"><span>${icon('branch')}<strong>Checkout ${esc(slug(c))} · ${esc(c.branch)}</strong><code>${esc(c.commit.slice(0, 12))}</code></span><span>Snapshot del run ${esc(c.run_id)}</span><button class="im-btn im-btn--ghost im-btn--sm" data-action="premap-provenance">Provenienza ${icon('info')}</button></div>`;
}

function dependencyRow(dependency) {
  const { name, scope, state, unit, source, resolution_source, version, resolved_version, direct } = dependency;
  const declared = state === 'resolved' ? '—' : `<code>${esc(version || 'Non specificato')}</code><br><small>${esc(source)}</small>`;
  const resolved = resolved_version ? `<code>${esc(resolved_version)}</code><br><small>${esc(resolution_source || source)}</small>` : '—';
  const relation = direct === true ? 'Diretta' : direct === false ? 'Transitiva' : '—';
  return `<tr><td><strong>${esc(name)}</strong><br><small>${esc(scope)}</small></td><td>${esc(unit)}</td><td>${declared}</td><td>${resolved}</td><td>${relation}</td></tr>`;
}

function premapScreen() {
  if (premapError) return failedPanel('Pre-mappa non disponibile: ' + premapError, 'retry-premap');
  if (!PREMAP) return loadingPanel('premap');
  const languages = PREMAP.languages;
  return premapSourceLine() + `<div class="im-metric-grid">
    ${metric(document, String(number(PREMAP.files.length)), 'File nello snapshot', 'Inventario del checkout').outerHTML}
    ${metric(document, String(languages.length), 'Linguaggi rilevati', 'File sorgente riconosciuti').outerHTML}
    ${metric(document, String(PREMAP.units.length), 'Unità tecniche', 'Da manifest e strumenti di build').outerHTML}
    ${metric(document, String(number(PREMAP.dependencies.length)), 'Dipendenze per unità', 'Da manifest e modelli di build').outerHTML}
  </div>
  <div class="im-auto-grid">
    <section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="tree-title">
      <div class="im-panel-header im-split"><div><h2 id="tree-title">Struttura del repository</h2><p class="im-muted im-caption">Directory fisiche e unità tecniche restano distinte.</p></div>${icon('layers')}</div>
      <div class="im-content-toolbar"><span id="tree-mode"></span>
      <span class="im-input">${icon('search')}<input id="premap-search" type="search" aria-label="Cerca nell’albero" placeholder="Cerca percorso o unità…" value="${esc(state.treeSearch)}"></span></div>
      <div id="repository-tree" class="im-scroll im-scroll--bounded im-inset" aria-label="${state.treeMode === 'directories' ? 'Albero delle directory' : 'Albero delle unità tecniche'}"></div>
      <div class="im-inset" id="tree-selection">${premapSelection()}</div>
    </section>
    <aside class="im-stack" aria-label="Tecnologie e linguaggi">
      <section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Linguaggi</h2><span class="im-chip">Inventario</span></div><div>${languages.map(l => `<div class="im-split im-cluster"><span>${esc(l.name)}</span><strong>${number(l.files)}<small> file</small></strong></div>`).join('') || '<p class="im-muted im-caption">Nessun file sorgente riconosciuto.</p>'}</div><p class="im-caption im-inset">File sorgente dello snapshot, per linguaggio riconosciuto da Daodan.</p></section>
      <section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Tecnologie e framework</h2><span class="im-chip">Riconosciuti</span></div><div>${PREMAP.technologies.map(t => `<div class="im-inset"><div><strong>${esc(t.name)}</strong><span class="im-chip">${esc(t.category)}</span></div><p>${esc(t.version || (t.state === 'declared' ? 'Versione non dichiarata' : 'Versione non registrata'))}</p><code>${esc(t.source)}</code></div>`).join('') || '<p class="im-muted im-caption">Nessuna tecnologia riconosciuta nei manifest.</p>'}</div></section>
    </aside>
  </div>
  <section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="dependency-title">
    <div class="im-panel-header"><h2 id="dependency-title">Dipendenze per unità</h2></div>
    <div class="im-scroll im-scroll--bounded"><table class="im-table"><thead><tr><th>Dipendenza</th><th>Unità</th><th>Vincolo dichiarato</th><th>Versione risolta</th><th>Relazione</th></tr></thead>
    <tbody>${PREMAP.dependencies.map(dependencyRow).join('') || '<tr><td colspan="5" class="im-muted">Nessuna dipendenza registrata.</td></tr>'}</tbody></table></div>
  </section>`;
}

const UNIT_STATUS = { confirmed: 'Confermata', inferred: 'Inferita', incomplete: 'Incompleta' };
function directoryEntries(paths) {
  const root = new Map();
  for (const path of paths) {
    let folder = root, prefix = '';
    const parts = path.split('/');
    parts.forEach((name, i) => {
      prefix += (i ? '/' : '') + name;
      if (i === parts.length - 1) folder.set(name, { id: path, name, value: path });
      else {
        if (!folder.has(name)) folder.set(name, { id: 'directory:' + prefix, name, folders: new Map() });
        folder = folder.get(name).folders;
      }
    });
  }
  function entries(map) {
    return [...map.values()].sort((a, b) => Number(!!b.folders) - Number(!!a.folders) || a.name.localeCompare(b.name, 'it'))
      .map(entry => entry.folders ? { id: entry.id, name: entry.name, children: entries(entry.folders) } : entry);
  }
  return entries(root);
}

function unitEntries(query) {
  const byId = new Map(PREMAP.units.map(u => [u.id, u]));
  const visible = new Set();
  for (const unit of PREMAP.units.filter(u => [u.name,u.kind,u.root,u.manifest].join(' ').toLowerCase().includes(query))) {
    for (let item = unit; item && !visible.has(item.id); item = byId.get(item.parent)) visible.add(item.id);
  }
  const nodes = new Map();
  for (const unit of PREMAP.units.filter(u => visible.has(u.id))) {
    const id = 'unit:' + unit.id;
    const children = [{ id: JSON.stringify([id, 'info']), name: 'Confine tecnico e fonte', value: id }];
    if (unit.manifest) children.push({ id: JSON.stringify([id, 'manifest']), name: unit.manifest, value: unit.manifest });
    nodes.set(unit.id, { id, name: [unit.name, unit.kind, UNIT_STATUS[unit.status] || unit.status].filter(Boolean).join(' · '), children });
  }
  const roots = [];
  for (const [key, node] of nodes) (nodes.get(byId.get(key).parent)?.children ?? roots).push(node);
  return roots;
}

function mountTree(active) {
  const host = document.getElementById('repository-tree');
  if (!host) return;
  const chooser = segmentedControl(document, {
    name: 'tree-mode', label: 'Tipo di albero', value: state.treeMode,
    choices: [{ value: 'directories', label: 'Directory' }, { value: 'units', label: 'Unità tecniche' }],
    onChange(value) { state.treeMode = value; render(); },
  });
  for (const [value, input] of chooser.inputs) input.id = 'tree-mode-' + value;
  document.getElementById('tree-mode').append(chooser.element);

  const query = state.treeSearch.trim().toLowerCase();
  const physical = state.treeMode === 'directories';
  const paths = physical ? PREMAP.files.filter(p => p.toLowerCase().includes(query)) : [];
  const entries = physical ? directoryEntries(paths) : unitEntries(query);
  if (!entries.length) {
    host.innerHTML = '<p>Nessun risultato.</p>' + (query ? '<button class="im-btn" data-action="clear-tree-search">Azzera ricerca</button>' : '');
    return;
  }
  const expanded = [];
  let selected;
  function visit(items, level) {
    for (const item of items) {
      if (item.value && item.value === state.treeSelected && selected === undefined) selected = item.id;
      if (item.children) {
        if (query || (state.treeOpen[item.id] ?? level === 0)) expanded.push(item.id);
        visit(item.children, level + 1);
      }
    }
  }
  visit(entries, 0);
  const summary = document.createElement('strong');
  summary.textContent = physical ? ctx().repository.name + ' · ' + paths.length + ' file' : 'Unità da manifest';
  const tree = fileTree(document, entries, {
    label: physical ? 'Albero delle directory' : 'Albero delle unità tecniche', expanded, selected, active,
    onSelect(entry) {
      if (!entry.value) return;
      state.treeSelected = entry.value;
      document.getElementById('tree-selection').innerHTML = premapSelection();
      save();
    },
    onToggle(entry, open) { if (!query) { state.treeOpen[entry.id] = open; save(); } },
  });
  host.replaceChildren(summary, tree);
  if (active) tree.querySelector('[tabindex="0"]')?.focus({ preventScroll: true });
}

function premapSelection() {
  const selected = state.treeSelected;
  if (!selected) return `<span class="im-muted">${icon('info')}Seleziona un file o apri un’unità per leggerne la provenienza.</span>`;
  if (selected.startsWith('unit:')) {
    const unit = PREMAP.units.find(u => 'unit:' + u.id === selected);
    if (unit) return `<p class="im-kicker">Unità tecnica · ${esc(UNIT_STATUS[unit.status] || unit.status || 'dichiarata')}</p><h3>${esc(unit.name)}</h3><p>${esc(unit.kind)} · <code>${esc(unit.root || '.')}</code></p>${unit.manifest ? `<code>${esc(unit.manifest)}</code>` : ''}${unit.description ? `<p>${esc(unit.description)}</p>` : ''}<p class="im-muted">${unit.dependencies.length} dipendenze registrate.</p>`;
  }
  const extension = selected.split('/').pop().includes('.') ? selected.split('.').pop() : 'senza estensione';
  return `<p class="im-kicker">File dell’inventario</p><h3>${esc(selected.split('/').pop())}</h3><code>${esc(selected)}</code><p class="im-muted">Tipo: ${esc(extension)} · fonte: snapshot del commit ${esc(ctx().commit.slice(0, 12))}. Il contenuto non viene eseguito.</p>`;
}

// -- 2. analysis ---------------------------------------------------------------------------------------------------

function pipelineEvents() { return events.filter(e => !e.run); }

// The run's steps follow their own events: the pass's state is the
// engine's, whose end does not end the steps after it. The note comes from the run: the progress, the cause of a
// step that failed or of an analyzer that could not run, and the pass's cause for a step the run will not reach.
function steps() {
  const status = {}, causes = {}, failed = {};
  for (const e of pipelineEvents()) {
    if (e.kind === 'step.started') { status[e.step] = 'running'; causes[e.step] = []; delete failed[e.step]; }
    if (e.kind === 'step.finished') status[e.step] = 'done';
    if (e.kind === 'step.failed' || (e.kind === 'log' && e.level === 'error' && e.data?.cause)) failed[e.step] = e.data?.cause || e.message;
    if (e.kind === 'analyzer.unavailable') (causes[e.step] ||= []).push(`${e.analyzer || 'analyzer'}: ${e.data?.cause || e.message}`);
  }
  const progress = server?.run?.progress, p = pass(), of = id => failed[id] ? 'failed' : status[id] || 'pending';
  const reached = !complete() || STEPS.some(([id]) => of(id) === 'running');  // a step still runs: the next may start
  return STEPS.map(([id, label]) => {
    const s = of(id), cause = causes[id]?.join(' · ');
    const note = s === 'done' ? (cause ? 'Completata con lacune · ' + cause : 'Completata')
      : s === 'running' ? 'In corso' + (progress?.step === id && progress.total ? ` · ${progress.done}/${progress.total}` : '')
        : s === 'failed' ? 'Non riuscita · ' + failed[id]
          : reached ? 'In attesa' : 'Non eseguita' + (p.reason ? ' · ' + p.reason : '');
    return { id, label, status: s === 'pending' && !reached ? 'skipped' : s, note };
  });
}

function mountPipeline() {
  const host = document.getElementById('pipeline-steps');
  if (!host) return;
  const states = { running: 'now', done: 'done', failed: 'failed', pending: 'todo', skipped: 'skipped' };
  host.replaceChildren(stepList(document, 'Passi della pipeline', steps().map(({ label, status, note }) => ({
    label, state: states[status], detail: note,
  }))));
  setProgress(document.getElementById('run-progress'), runPercent());
}

function runPercent() {
  if (!ctx()) return 0;
  const list = steps(), progress = server?.run?.progress;
  const running = list.find(t => t.status === 'running');
  const part = running && progress?.step === running.id && progress.total ? progress.done / progress.total : 0;
  return Math.round(100 * (list.filter(t => t.status === 'done').length + part) / list.length);
}

function runPhaseLabel() {
  const running = steps().find(t => t.status === 'running');
  if (running) return running.label;
  return { fresh: 'Pipeline completata', unavailable: 'Pipeline completata con lacune', failed: 'Pipeline conclusa, grafo delle chiamate non rifinito', off: 'Passaggio del grafo spento' }[pass().state] || 'In attesa del passaggio del grafo';
}

function statusLabel() {
  return { fresh: 'Completata', unavailable: 'Completata con lacune', failed: 'Da riprovare', off: 'Spenta' }[pass().state] || 'In esecuzione';
}

function runHelp() {
  const p = server?.run?.progress;
  if (complete()) return pass().state === 'fresh' ? 'Pipeline conclusa: sintesi e grafo sono pronti da leggere.' : 'Pipeline conclusa: sintesi e grafo mostrano quello che c’è, con le sue lacune.';
  return p ? `Ultimo avanzamento: ${STEP[p.step] || p.step || 'pipeline'}${p.analyzer ? ' · ' + p.analyzer : ''} · ${p.message || p.done + '/' + p.total}` : 'In attesa del primo avanzamento del run.';
}

function passAlert() {
  const p = pass();
  if (!['unavailable', 'failed', 'off'].includes(p.state)) return '';
  return noteHtml({ tone: p.state === 'failed' ? 'err' : 'warn',
    title: p.state === 'failed' ? 'Il passaggio che rifinisce il grafo delle chiamate non è riuscito.' : 'Lacuna: il passaggio che rifinisce il grafo delle chiamate non è disponibile.',
    message: p.reason || 'Nessuna causa registrata.', actionsHtml: p.state === 'failed' ? buttonHtml('Riprova il passaggio', 'retry-pass', { icon: 'play' }) : '' });
}

const RUN_EVENT = { run_created: 'Run creato', engine_started: 'Passaggio del grafo avviato', engine_unavailable: 'Passaggio del grafo non disponibile', engine_failed: 'Passaggio del grafo interrotto', index_failed: 'Indice lessicale non costruito', modules_failed: 'Grafo dei moduli non costruito' };
const KIND = { 'step.started': 'avviato', 'step.finished': 'completato', 'analyzer.started': 'analyzer avviato', 'analyzer.unavailable': 'analyzer non disponibile', 'analyzer.finished': 'analyzer completato', gap: 'lacuna', 'graph.ready': 'grafo pronto', log: 'nota' };
function logItems() {
  return events.filter(e => e.run || (e.kind !== 'progress' && e.level !== 'debug')).map(e => e.run
    ? { title: RUN_EVENT[e.event] || e.event, detail: e.message, type: /failed/.test(e.event) ? 'error' : /unavailable/.test(e.event) ? 'gap' : '', at: e.timestamp }
    : { title: `${STEP[e.step] || e.step || 'Pipeline'} · ${KIND[e.kind] || e.kind}${e.analyzer && e.kind !== 'gap' ? ' · ' + e.analyzer : ''}`, detail: e.kind === 'gap' ? (e.data?.gap?.detail || e.message) + (e.data?.gap?.remedy ? ' Rimedio: ' + e.data.gap.remedy : '') : e.kind === 'analyzer.unavailable' ? e.data?.cause || e.message : e.kind === 'step.finished' && e.data?.outputs ? 'Scritti: ' + e.data.outputs.join(', ') : e.kind === 'step.started' && e.data?.inputs ? 'Legge: ' + e.data.inputs.join(', ') : e.message, type: e.level === 'error' ? 'error' : e.kind === 'gap' || e.level === 'warning' ? 'gap' : '', at: e.at });
}
function renderLogs() {
  const items = logItems();
  if (!items.length) return '<p class="im-muted im-caption">Nessun evento ancora.</p>';
  return items.slice(-8).reverse().map(l => `<div class="im-inset im-cluster" data-im-tone="${l.type === 'error' ? 'err' : l.type === 'gap' ? 'warn' : 'info'}"><span class="im-dot"></span><div><strong>${esc(l.title)}</strong><p>${esc(l.detail)}</p></div><time datetime="${esc(l.at)}">${esc(l.at ? new Date(l.at).toLocaleTimeString('it-IT') : '')}</time></div>`).join('');
}

// The links between modules: the engine writes the project's link rules, the machine applies them and decides every
// link. What the block says is the server's state, from the stream.
function plural(n, one, many) { return `${number(n)} ${Number(n) === 1 ? one : many}`; }
function mapNotice() {
  const map = server?.mapped;
  if (!map) return '';
  const review = map.needs_review || {};
  const counts = [
    review.nodes?.count && plural(review.nodes.count, 'nodo', 'nodi'),
    review.flows?.count && plural(review.flows.count, 'flusso', 'flussi'),
    review.refused_proposals?.count && plural(review.refused_proposals.count, 'proposta rifiutata', 'proposte rifiutate'),
  ].filter(Boolean);
  const partial = counts.length > 0 || map.state === 'incomplete';
  const title = partial ? 'Mappa del sistema parziale' : {
    running: 'Mappatura del sistema in corso', failed: 'Mappatura del sistema interrotta',
    no_engine: 'Mappatura in attesa di un motore', done: 'Mappa del sistema registrata',
  }[map.state];
  if (!title) return '';
  const cause = map.cause === 'the recorded map still has stale or incomplete records'
    ? 'Alcune prove sono incomplete o si riferiscono a una revisione precedente.' : map.cause;
  const tone = partial || map.state === 'no_engine' ? 'warn' : map.state === 'failed' ? 'err' : 'info';
  return noteHtml({ tone, title, message: [counts.length && `Da verificare: ${counts.join(', ')}.`, cause].filter(Boolean).join(' ') });
}
function linksNote() {
  const l = server?.links || { state: 'idle' }, chosen = Boolean(server?.engine?.engine), running = l.state === 'running';
  const said = { idle: 'Non ancora cercati: il motore scrive le regole del progetto, la macchina le applica e decide ogni legame.', running: 'In corso: il motore scrive le regole, la macchina le applica e gli rimanda quello che resta scollegato.', done: 'Trovati dalla macchina con le regole del progetto.', failed: 'Non trovati.', no_engine: 'Nessun motore scelto.' }[l.state] || l.state;
  const counts = l.state === 'done' ? `${plural(l.routes.called, 'richiesta', 'richieste')}, ${plural(l.routes.offered, 'rotta', 'rotte')}, ${plural(l.routes.linked, 'legame', 'legami')}, ${plural(l.gaps, 'lacuna', 'lacune')}${l.stores ? ', ' + plural(l.stores, 'archivio', 'archivi') : ''}.` : '';
  const action = `<button class="im-btn" data-action="find-links" ${running ? 'aria-busy="true"' : chosen ? '' : 'disabled title="Scegli e salva prima un motore."'}>${busyIcon(running, 'play')}Trova i legami</button>${chosen ? '' : `<button class="im-btn" data-screen="engine">${icon('arrow')}Scegli il motore</button>`}`;
  return noteHtml({ icon: 'graph', title: 'Legami tra i moduli', tone: l.state === 'failed' ? 'err' : undefined,
    message: [said, counts, l.state === 'failed' && l.cause, chosen ? '' : 'Scegli e salva prima un motore.'].filter(Boolean).join(' '), actionsHtml: action });
}

function runButton() {
  return complete() ? `<button id="run-toggle" class="im-btn im-btn--primary" data-analysis-stage="synthesis">${icon('document')}Leggi sintesi</button>` : `<button class="im-btn" id="run-toggle" aria-busy="true">${busyIcon(true)}Analisi in corso</button>`;
}

function nodeName(n) { return n.kind === 'directory' && n.name === '.' ? 'radice del repository' : n.name; }
const NODE_STATUS = { confirmed: 'confermato', inferred: 'inferito', incomplete: 'incompleto', proposed: 'proposto' };
function nodeState(n) { return n.location === 'external' ? 'esterno' : NODE_STATUS[n.status] || n.status || 'senza stato'; }
function nodeFacts(n) { return n.location === 'external' ? [n.node_type, 'esterno'].filter(Boolean).join(' · ') : n.kind === 'symbol' ? ['righe ' + (n.lines || []).join('–'), n.members ? `${n.members.length} simboli` : '', n.node_type].filter(Boolean).join(' · ') : `${n.files.length} file · ${nodeState(n)}`; }
const STACK_SHOWN = 2;  // the tiles that fit the text column of a card; the inspector lists them all
function markImg(id) { return `<img class="im-inline-mark" src="${esc('/api/app/mark?' + new URLSearchParams({ id, token }))}" alt="">`; }
// The frameworks a group declares, as tiles under its name, on its card and on its frame when it is open.
function stackRow(n) { const p = n.projects || []; return p.length ? `<span class="im-cluster" title="Stack: ${esc(p.map(x => x.name).join(', '))}">${p.slice(0, STACK_SHOWN).map(x => `<span class="im-cluster">${markImg(x.mark)}<span>${esc(x.name)}</span></span>`).join('')}${p.length > STACK_SHOWN ? `<span class="im-caption">+${p.length - STACK_SHOWN}</span>` : ''}</span>` : ''; }
function stackBlock(n) { return `<div class="im-section"><h3>Stack</h3><ul class="im-detail-list">${(n.projects || []).map(x => `<li>${markImg(x.mark)}<span>${esc(x.name)}</span><span class="im-chip">${esc(x.category)}</span>${x.evidence.map(e => `<code>${esc(e.path)}${e.line ? ':' + e.line : ''}</code>`).join('')}</li>`).join('') || '<li class="im-muted">Nessun framework o libreria riconosciuti dal registro.</li>'}</ul>${n.other_dependencies ? `<p class="im-muted im-caption">Altre dipendenze dichiarate: ${n.other_dependencies}</p>` : ''}</div>`; }
// A node's picture: the mark of its registry entry, from the app's server; without one, or when it does not load, the icon of its kind.
function nodeIcon(n) { return n.mark ? markImg(n.mark) : icon(n.location === 'external' ? 'external' : 'layers'); }
document.addEventListener('error', event => { if (event.target.matches?.('img.im-inline-mark')) event.target.outerHTML = icon('external'); }, true);
function levelLabel() { return GRAPH?.grouping === 'modules' ? 'Moduli' : 'Directory'; }
// The system map's levels the graph shows, by their own names, never «the» graph: the app builds codice and infrastruttura.
function levelsName() { return (GRAPH?.levels || []).map(level => level[0].toUpperCase() + level.slice(1)).join(' · '); }
const SELECTED = { directory: 'Directory selezionata', file: 'File selezionato', symbol: 'Simbolo selezionato' };
// The name of a node or of an open group, for an arrow that ends on either.
function endName(id) { const n = GRAPH.nodes.find(item => item.id === id); return n ? nodeName(n) : GRAPH.open.find(group => group.id === id)?.name || id; }

function buildPreview() {
  if (graphError) return panelStateHtml({ kind: 'error', text: 'Grafo non disponibile: ' + graphError, retryHtml: retryButton('retry-graph'), errorWord: 'Errore' });
  const g = GRAPH;
  if (!g) return waits.has('graph') ? panelStateHtml({ kind: 'loading', rows: 3 }) : '';
  if (!g.nodes.length) return panelStateHtml({ kind: 'empty', title: 'Prima l’inventario, poi le relazioni.', text: 'Il grafo del run non ha ancora gruppi di file. I nodi compaiono quando la pipeline scrive un artefatto.' });
  return '<div class="im-fill" id="preview-diagram"></div>';
}

function fragment(markup) {
  const template = document.createElement('template');
  template.innerHTML = markup;
  return template.content;
}
function sceneNode(n, x, y, width, height, preview) {
  return { id: n.id, label: nodeName(n), x, y, width, height,
    selected: !preview && n.id === state.graphRoot, external: n.location === 'external',
    openLabel: !preview && opens(n) ? 'Apri ' + nodeName(n) : undefined,
    content: fragment(`<span>${nodeIcon(n)}</span><span class="im-row-text"><strong class="im-row-title">${esc(nodeName(n))}</strong>${preview ? '' : stackRow(n)}<small class="im-row-sub">${esc(nodeFacts(n))}</small></span>`),
  };
}
function proofLabel(status, conflict = false) {
  const label = { observed: 'osservata in esecuzione', sampled: 'campionata dal profiler', uncertain: 'incerta' }[status] || '';
  return [label, conflict && 'destinazioni in conflitto'].filter(Boolean).join(' · ');
}
function runtimeSummary(edges) {
  const observed = edges.filter(e => !e.conflict && e.status === 'observed').length;
  const sampled = edges.filter(e => !e.conflict && e.status === 'sampled').length;
  const conflicts = edges.filter(e => e.conflict).length;
  return [observed && plural(observed, 'osservata in esecuzione', 'osservate in esecuzione'),
    sampled && plural(sampled, 'campionata dal profiler', 'campionate dal profiler'),
    conflicts && plural(conflicts, 'in conflitto', 'in conflitto')].filter(Boolean).join(' · ');
}
function sceneEdge(e) {
  return { source: e.source, target: e.target, dashed: e.conflict || e.status === 'uncertain' || e.status === 'sampled',
    tone: e.conflict || e.status === 'uncertain' ? 'warn' : ['observed', 'sampled'].includes(e.status) ? 'accent' : undefined,
    label: [endName(e.source), '→', endName(e.target), Object.entries(e.counts ?? {}).map(([k,v]) => k + ': ' + v).join(', '), proofLabel(e.status, e.conflict)].filter(Boolean).join(' ') };
}
function previewScene() {
  return { nodes: GRAPH.nodes.map((n,i) => sceneNode(n, (i % 3) * 201, Math.floor(i / 3) * 92, 178, 62, true)),
    edges: GRAPH.edges.map(sceneEdge) };
}

function buildCounts() { return GRAPH ? `${GRAPH.nodes.length} ${GRAPH.grouping === 'modules' ? 'moduli' : 'directory'} · ${GRAPH.edges.length} relazioni · ${number(GRAPH.files)} file` : '—'; }
function buildStatus() {
  if (graphLoading) return 'Lettura del grafo…';
  if (pipelineEvents().some(e => e.kind === 'graph.ready')) return 'Grafo del codice scritto';
  return complete() ? 'Costruzione conclusa' : 'Costruzione in corso';
}

function analysisRunScreen() {
  const c = ctx(), percent = runPercent(), alert = passAlert();
  return noteHtml({ icon: 'info', title: `Analisi del commit ${c.commit.slice(0, 12)}.`, message: `Avanzamento ed eventi sono quelli del run ${c.run_id}. Il grafo cresce solo quando la pipeline scrive un artefatto.` }) + `
  <div class="im-auto-grid"><section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="run-title"><div class="im-inset im-stack"><div class="im-split im-cluster"><div><p class="im-kicker">Esecuzione</p><h2 id="run-title">${esc(runPhaseLabel())}</h2><div class="im-cluster"><span class="im-chip" data-im-tone="${pass().state === 'failed' ? 'err' : 'accent'}" id="run-badge"><span class="im-dot"></span>${statusLabel()}</span><span id="run-button-wrap">${runButton()}</span></div></div><div class="im-metric-value"><span id="progress-value">${percent}</span><small>%</small></div></div><div class="im-progress" role="progressbar" aria-label="Passi completati della pipeline" id="run-progress"></div><p id="run-help">${esc(runHelp())}</p><div id="pipeline-steps"></div><div id="run-error" ${alert ? '' : 'hidden'}>${alert}</div><div id="map-status">${mapNotice()}</div><div id="links-block">${linksNote()}</div></div><div class="im-panel-foot im-cluster"><span class="im-muted">Repository: <code>${esc(slug(c))}</code> · <code>${esc(c.branch)}</code> · intero progetto</span></div></section>
  <section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="building-title"><div class="im-panel-header im-split"><div><h2 id="building-title">Costruzione del grafo</h2><p class="im-muted im-caption">Gruppi di file e relazioni dal grafo del run.</p></div><span class="im-chip" id="build-level">${esc(levelsName() || levelLabel())}</span></div><div class="im-canvas-frame im-canvas-frame--preview" id="build-viewport">${buildPreview()}</div><div class="im-panel-foot im-cluster"><span id="build-counts">${buildCounts()}</span><span id="build-status">${buildStatus()}</span></div></section></div>
  <section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="activity-title"><div class="im-panel-header im-split"><h2 id="activity-title">Eventi e feedback</h2><span class="im-chip">${logItems().length} eventi</span></div><div class="im-scroll im-scroll--bounded" id="logs" aria-live="polite" aria-relevant="additions">${renderLogs()}</div></section>`;
}

function updateAnalysisRun() {
  const stageButton = document.getElementById('stage-synthesis');
  if (stageButton) stageButton.disabled = !complete();
  if (state.screen !== 'analysis' || state.analysisStage !== 'analysis' || !ctx() || !document.getElementById('run-title')) return render();
  const percent = runPercent(), alert = passAlert();
  document.getElementById('run-title').textContent = runPhaseLabel();
  document.getElementById('progress-value').textContent = percent;
  const badge = document.getElementById('run-badge');
  badge.className = 'im-chip';
  badge.dataset.imTone = pass().state === 'failed' ? 'err' : 'accent';
  badge.textContent = statusLabel();
  document.getElementById('run-help').textContent = runHelp();
  mountPipeline();
  const error = document.getElementById('run-error');
  error.hidden = !alert;
  error.innerHTML = alert;
  document.getElementById('links-block').innerHTML = linksNote();
  document.getElementById('map-status').innerHTML = mapNotice();
  const hadFocus = document.activeElement?.id === 'run-toggle';
  document.getElementById('run-button-wrap').innerHTML = runButton();
  if (hadFocus) document.getElementById('run-toggle')?.focus({ preventScroll: true });
  document.getElementById('logs').innerHTML = renderLogs();
  const viewport = document.getElementById('build-viewport');
  const version = graphError || GRAPH;
  if (previewVersion !== version || !viewport.hasChildNodes()) {
    viewport.innerHTML = buildPreview();
    mountDiagram();
    previewVersion = version;
  }
  document.getElementById('build-level').textContent = levelsName() || levelLabel();
  document.getElementById('build-counts').textContent = buildCounts();
  document.getElementById('build-status').textContent = buildStatus();
  updateChrome();
}

// -- 3. synthesis --------------------------------------------------------------------------------------------------

function gapLines() {
  const lines = [];
  if (passAlert()) lines.push('Grafo delle chiamate non rifinito: ' + (pass().reason || pass().state));
  if (GRAPH?.unassigned.count) lines.push(`${number(GRAPH.unassigned.count)} file non assegnati a un modulo.`);
  for (const e of pipelineEvents().filter(e => e.kind === 'gap')) lines.push(e.data?.gap?.detail || e.message);
  for (const gap of GRAPH?.gaps || []) lines.push(gap.reason);
  return [...new Set(lines)];
}

async function loadPathPage(id = null, offset = 0, previous = null, focus = false) {
  const page = { run: ctx().run_id, id, offset, previous };
  pathPage = page; startWait('paths');
  const query = new URLSearchParams({ offset });
  if (id === orphanWrites) query.set('effects', '1');
  else if (id) query.set('id', id);
  drawPaths();
  try {
    const result = await get('/api/app/paths?' + query);
    if (result.run_id && result.run_id !== page.run) throw new Error('Il run attivo è cambiato.');
    const rows = id === orphanWrites ? result.effects : id ? result.steps : result.cards;
    if (!Array.isArray(rows)) throw new Error(result.reason || 'La pagina dei percorsi non è disponibile.');
    page.result = result;
  } catch (error) { page.error = error.message; }
  endWait('paths');
  if (page === pathPage && viewingPaths()) drawPaths(focus);
}

function drawPaths(focus = false) {
  const panel = document.getElementById('flow-paths');
  if (!panel) return;
  panel.innerHTML = pathContents();
  if (focus) panel.focus({ preventScroll: true });
}

function pathContents() {
  const page = pathPage;
  const top = '<div class="im-panel-header im-split"><h2 id="flow-paths-title">Percorsi per ingresso</h2>' +
    (page?.id ? '<button class="im-btn im-btn--ghost im-btn--sm" data-action="path-list">Torna agli ingressi</button>' :
      '<button class="im-btn im-btn--ghost im-btn--sm" data-action="path-effects">Scritture senza ingresso</button>') + '</div>';
  if (!page || (!page.result && !page.error)) return top + '<div class="im-panel-body">' + (waits.has('paths') ? panelStateHtml({ kind: 'loading', rows: 2 }) : '') + '</div>';
  if (page.error) return top + '<div class="im-panel-body">' + panelStateHtml({ kind: 'error', text: page.error, retryHtml: retryButton('path-retry'), errorWord: 'Errore' }) + '</div>';
  const { card, cards, steps, effects, count, next_offset } = page.result;
  const items = page.id === orphanWrites ? effects : page.id ? steps : cards;
  const previous = page.previous && page.id === page.previous.id;
  const noun = page.id === orphanWrites ? 'Scritture' : page.id ? 'Passaggi' : 'Ingressi';
  const paging = `<div class="im-cluster"><span class="im-muted im-caption">${noun} ${number(page.offset + 1)}–${number(page.offset + items.length)} di ${number(count)}</span>
    ${previous ? `<button class="im-btn im-btn--sm" data-action="path-prev">${noun} precedenti</button>` : ''}
    ${Number.isInteger(next_offset) ? `<button class="im-btn im-btn--sm" data-action="path-next">${noun} ${effects ? 'successive' : 'successivi'}</button>` : ''}</div>`;
  if (page.id === orphanWrites) {
    const rows = effects.map(e => `<li><p><code>${esc(e.writer)}</code> → <code>${esc(e.effect)}</code></p>
      <p class="im-caption">${esc(e.site)}</p><p>${esc(e.reason)}</p>
      ${e.stopped_at ? `<p>Le prove si fermano in <code>${esc(e.stopped_at)}</code>.</p>` : ''}</li>`).join('');
    return top + `<div class="im-inset im-stack"><h3>Scritture senza ingresso</h3>
      <p>${number(page.result.without_entry)} di ${number(page.result.writes)} scritture senza un percorso provato da un ingresso.
      Con un percorso provato: ${number(page.result.reached)}.</p>${rows ? `<ul class="im-detail-list">${rows}</ul>${paging}` : ''}</div>`;
  }
  if (!page.id) {
    const rows = items.map(c => `<li><button class="im-btn im-btn--ghost" data-path-card="${esc(c.card_id)}">
      <span><strong>${esc(c.label || c.event)}</strong><br><code>${esc(c.handler)}</code> · ${esc(c.site)}</span>${icon('arrow')}</button></li>`).join('');
    const missing = server?.mapped?.discovery?.effect_coverage?.without_entry;
    const coverage = missing ? `<p>${number(missing)} scritture senza un percorso provato da un ingresso.</p>` : '';
    return top + '<div class="im-inset im-stack">' + coverage + (rows ? `<ul class="im-detail-list">${rows}</ul>${paging}` :
      '<p>Nessun ingresso classificato per questo snapshot.</p>') + '</div>';
  }
  const rows = steps.map(step => {
    const evidence = [proofLabel(step.confidence, step.conflict) || step.confidence, step.origin, step.resolver].filter(Boolean);
    const end = step.end === 'lacuna' ? 'Lacuna' : step.end === 'effetto' ? 'Effetto' : '';
    return `<li value="${Number(step.n)}"><p><strong>Passaggio ${number(step.n)}</strong>${step.parent ? ' · dal passo ' + number(step.parent) : ''}
      ${end ? `<span class="im-chip" data-im-tone="${step.end === 'lacuna' ? 'warn' : 'accent'}">${end}</span>` : ''}</p>
      <p><code>${esc(step.from)}</code>${step.to ? ` · ${esc(step.type)} → <code>${esc(step.to)}</code>` : ''}</p>
      <p class="im-muted im-caption">${esc([step.site, ...evidence].filter(Boolean).join(' · '))}</p>
      ${step.reason ? `<p>${esc(step.reason)}</p>` : ''}</li>`;
  }).join('');
  return top + `<div class="im-inset im-stack"><h3>${esc(card.label || card.event)}</h3>
    <dl class="im-facts"><dt>Evento</dt><dd>${esc(card.event)} · ${esc(card.kind)}</dd>
    <dt>Gestore</dt><dd><code>${esc(card.handler)}</code></dd>
    ${card.handler_source || card.handler_confidence ? `<dt>Fonte del gestore</dt><dd>${esc(
      [card.handler_source, proofLabel(card.handler_confidence) || card.handler_confidence].filter(Boolean).join(' · '))}</dd>` : ''}
    <dt>Ingresso</dt><dd><code>${esc(card.site)}</code></dd></dl>
    ${rows ? `<ol class="im-stack">${rows}</ol>${paging}` : '<p>Nessun passaggio provato dal gestore.</p>'}</div>`;
}

function synthesisScreen() {
  const intro = mapNotice() + `<section class="im-surface im-panel" data-im-surface="sheet" id="flow-paths" tabindex="-1" aria-labelledby="flow-paths-title">${pathContents()}</section>`;
  if (!GRAPH) return intro + (graphError ? failedPanel('Grafo non disponibile: ' + graphError, 'retry-graph') : loadingPanel('graph'));
  const top = [...GRAPH.nodes].sort((a, b) => b.files.length - a.files.length).slice(0, 3), gaps = gapLines();
  const modules = GRAPH.grouping === 'modules';
  return `${intro}${noteHtml({ icon: 'info', title: 'Sintesi testuale in attesa.', message: `Questa versione non fa scrivere una sintesi al motore: qui ci sono i conteggi, le responsabilità dichiarate e le lacune del run ${ctx().run_id}. Le domande al motore sono in «Motore e domande».` })}<div class="im-metric-grid">${metric(document, String(GRAPH.nodes.length), modules ? 'Moduli' : 'Directory con file', 'Gruppi del grafo').outerHTML}${metric(document, String(GRAPH.edges.length), 'Relazioni nel grafo', runtimeSummary(GRAPH.edges) || 'Tra i gruppi visualizzati').outerHTML}${metric(document, String(number(GRAPH.files)), 'File nel grafo', `Snapshot del commit ${ctx().commit.slice(0, 7)}`).outerHTML}${metric(document, String(number(modules ? GRAPH.unassigned.count : GRAPH.nodes.filter(n => n.location === 'external').length)), modules ? 'File senza modulo' : 'Nodi esterni', modules ? 'Lacuna esplicita del grafo' : 'Servizi riconosciuti dallo stack').outerHTML}</div>
  <div class="im-auto-grid"><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Responsabilità da esplorare</h2><span class="im-chip">${esc(levelsName())}</span></div><div class="im-stack">${top.map(n => `<button class="im-btn" data-preview-node="${esc(n.id)}"><span>${icon('layers')}</span><span><strong>${esc(nodeName(n))}</strong><p>${esc(n.responsibility || 'Responsabilità non descritta nel grafo.')}</p><small>${esc(nodeFacts(n))}</small></span>${icon('arrow')}</button>`).join('') || '<p class="im-muted im-caption">Nessun gruppo nel grafo.</p>'}</div></section><aside class="im-stack"><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Dipendenze dopo l’analisi</h2></div><div class="im-inset im-stack"><p>${PREMAP ? `${number(PREMAP.dependencies.filter(d => d.resolved_version).length)} voci con versione risolta nel modello di build.` : 'Inventario delle dipendenze non disponibile.'}</p></div></section><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Cosa manca al quadro</h2></div><div class="im-inset im-stack"><ul>${gaps.slice(0, 8).map(g => `<li>${esc(g)}</li>`).join('') || '<li>Nessuna lacuna registrata dal run.</li>'}</ul>${gaps.length > 8 ? `<p class="im-muted im-caption">Altre ${gaps.length - 8} lacune in «Provenienza e lacune».</p>` : ''}<button class="im-btn im-btn--ghost" data-action="snapshot">${icon('file')}Provenienza e lacune</button></div></section></aside></div>`;
}

// -- the graph -----------------------------------------------------------------------------------------------------

function nodeById(id) { return GRAPH?.nodes.find(n => n.id === id) || GRAPH?.nodes[0]; }

function visibleGraph() {
  let nodes = GRAPH.nodes, edges = GRAPH.edges.filter(e => state.graphKind === 'all' || (e.counts[state.graphKind] || 0) > 0);
  if (state.graphDepth !== 'all' && nodeById(state.graphRoot)) {
    const root = nodeById(state.graphRoot).id, found = new Set([root]);
    let frontier = [root];
    for (let d = 0; d < Number(state.graphDepth); d++) {
      const next = [];
      for (const id of frontier) for (const e of edges) {
        if ((state.graphDirection === 'out' || state.graphDirection === 'both') && e.source === id && !found.has(e.target)) { found.add(e.target); next.push(e.target); }
        if ((state.graphDirection === 'in' || state.graphDirection === 'both') && e.target === id && !found.has(e.source)) { found.add(e.source); next.push(e.source); }
      }
      frontier = next;
    }
    nodes = nodes.filter(n => found.has(n.id));
  }
  if (state.graphSearch.trim()) { const q = state.graphSearch.trim().toLowerCase(); nodes = nodes.filter(n => [n.name, n.id, n.responsibility, ...n.files].join(' ').toLowerCase().includes(q)); }
  const ids = new Set([...nodes.map(n => n.id), ...GRAPH.open.map(group => group.id)]);  // an open group holds the arrows of its own
  return { nodes, edges: edges.filter(e => ids.has(e.source) && ids.has(e.target)) };
}

function graphCanvas(g) {
  if (g.nodes.length) return '<div class="im-fill" id="map-diagram"></div>';
  return panelStateHtml({ kind: 'empty', title: 'Nessun gruppo trovato', text: 'Cambia ricerca o amplia il perimetro del grafo.', actionHtml: '<button class="im-btn" data-action="clear-graph">Azzera filtri</button>' });
}
function mapScene(g) {
  // The grid of the page, row after row: an open group starts a row and is drawn around what it holds, which can hold
  // an open group in turn; the rest stays in its order. Laid out again at each step.
  const order = (a, b) => outside(a) - outside(b) || a.name.localeCompare(b.name, 'it');
  const cols = Math.min(3, g.nodes.length), positions = new Map(), placed = [], frames = [];
  let y = 42, right = cols * 254 + 20;
  const place = (holder, depth) => {
    const x0 = 30 + depth * 18;
    let col = 0;
    for (const item of [...g.nodes.filter(n => n.group === holder), ...GRAPH.open.filter(o => o.parent === holder)].sort(order)) {
      if (!('parent' in item)) {
        positions.set(item.id, { x: x0 + col * 254, y }); placed.push(item); right = Math.max(right, x0 + col * 254 + 250);
        if (++col === cols) { col = 0; y += 130; }
        continue;
      }
      if (col) { col = 0; y += 130; }
      const top = y;
      y += 44;
      place(item.id, depth + 1);
      frames.push({ ...item, x: x0 - 10, y: top, height: Math.max(52, y - top - 40) });
      y += 18;
    }
    if (col) y += 130;
  };
  place(null, 0);
  return {
    nodes: placed.map(n => { const p = positions.get(n.id); return sceneNode(n, p.x, p.y, 232, 74, false); }),
    groups: frames.map(f => ({ id: f.id, x: f.x, y: f.y, width: right + 12 - f.x, height: f.height,
      content: fragment(`<div class="im-cluster"><strong>${esc(nodeName(f))}</strong>${stackRow(f)}<button class="im-btn im-btn--sm" data-close-node="${esc(f.id)}" aria-label="Chiudi ${esc(nodeName(f))}">Chiudi</button></div>`),
    })),
    edges: g.edges.map(sceneEdge),
  };
}

function previewNode(id, opener) {
  const n = nodeById(id);
  detail(nodeName(n), `${GRAPH.grouping === 'modules' ? 'Modulo' : 'Directory'} del grafo di questo run.`,
    `<p>${esc(n.responsibility || 'Responsabilità non descritta nel grafo.')}</p><p class="im-muted im-caption">${esc(nodeFacts(n))} · commit ${esc(ctx().commit.slice(0, 12))}</p>`,
    `<button class="im-btn" data-preview-node="${esc(n.id)}">${icon('graph')}Apri nel grafo</button>`, opener);
}
function openGroup(id) {
  state.graphOpen = [...new Set([...state.graphOpen, id])];
  state.graphRoot = id; wantGroup = true; loadGraph(); render();
}
function mountDiagram() {
  const host = document.querySelector('#preview-diagram, #map-diagram');
  if (!host) {
    diagram?.dispose(); diagram = diagramHost = diagramKey = null;
    return;
  }
  const preview = host.id === 'preview-diagram';
  const key = JSON.stringify([host.id, state.runId, preview ? null : [state.graphOpen,state.graphSearch,state.graphDepth,state.graphDirection,state.graphKind]]);
  if (diagram && key === diagramKey) {
    if (host !== diagramHost) host.replaceWith(diagramHost);
  } else {
    diagram?.dispose();
    diagramKey = key; diagramHost = host;
    diagram = graphView(host, { label: preview ? 'Costruzione del grafo' : 'Grafo del codice', controls: graphControls,
      onSelect(id) {
        if (preview) previewNode(id, document.activeElement);
        else { state.graphRoot = id; wantGroup = true; render(); notice('Selezionato: ' + nodeName(nodeById(id))); }
      }, onOpen: openGroup,
    });
  }
  diagram.draw(preview ? previewScene() : mapScene(visibleGraph()));
}

function groupDetails() {
  const n = nodeById(state.graphRoot);
  const related = GRAPH.edges.filter(e => e.source === n.id || e.target === n.id);
  const runtime = related.filter(e => e.conflict || ['observed', 'sampled'].includes(e.status));
  return fragment(detailHtml(GROUP_LABEL, `<p class="im-kicker">${n.location === 'external' ? 'Nodo esterno selezionato' : SELECTED[n.kind] || 'Modulo selezionato'}</p><h2>${esc(nodeName(n))}</h2><span class="im-chip" data-im-tone="${n.location === 'external' ? 'info' : 'accent'}">${n.location === 'external' ? esc(['Dipendenza esterna', n.node_type].filter(Boolean).join(' · ')) : esc(nodeState(n))}</span><p class="im-muted">${esc(n.responsibility || 'Responsabilità non descritta nel grafo.')}</p>${opens(n) ? `<button class="im-btn im-btn--primary" data-open-node="${esc(n.id)}">${icon('layers')}Apri sul posto</button>` : ''}<div class="im-section"><h3>Perimetro</h3><dl class="im-facts">${n.kind === 'symbol' ? `<dt>Righe</dt><dd>${esc((n.lines || []).join('–'))}</dd>${n.members ? `<dt>Simboli dentro</dt><dd>${n.members.length}</dd>` : ''}` : `<dt>File assegnati</dt><dd>${n.files.length}</dd>`}<dt>Relazioni nel grafo</dt><dd>${related.length}</dd><dt>Provenienza</dt><dd>${esc(n.provenance || { directory: 'Directory del checkout', file: 'File del checkout', symbol: 'Outline del file' }[n.kind] || 'Non registrata')}</dd></dl>${runtime.length ? `<details><summary>Prove delle chiamate (${number(runtime.length)})</summary><ul class="im-detail-list">${runtime.map(e => `<li>${esc(endName(e.source))} → ${esc(endName(e.target))} · ${proofLabel(e.status, e.conflict)}</li>`).join('')}</ul></details>` : ''}</div>${n.projects ? stackBlock(n) : ''}${n.kind === 'file' ? symbolsBlock(n) : ''}<div class="im-section"><h3>Evidenze</h3><ul class="im-detail-list">${(n.evidence || []).map(e => `<li><code>${esc(e.path)}${e.line ? ':' + e.line : ''}</code></li>`).join('') || '<li class="im-muted">Nessuna evidenza dichiarata.</li>'}</ul></div>${n.kind === 'symbol' ? '' : `<div class="im-section"><h3>File del gruppo</h3><ul class="im-detail-list">${n.files.slice(0, 4).map(path => `<li><button class="im-btn" data-source-path="${esc(path)}">${icon('file')}<span>${esc(path.split('/').slice(-2).join('/'))}</span></button></li>`).join('') || '<li class="im-muted">Gruppo esterno: nessun file locale.</li>'}</ul>${n.files.length > 4 ? `<button class="im-btn im-btn--ghost im-btn--sm" data-action="component-files">Tutti i ${n.files.length} file ${icon('arrow')}</button>` : ''}</div>`}`));
}

// A file is the lowest node: its symbols and the calls among them, with their lines, are the inspector's, asked when
// the file is selected and kept by the server like the graph.
function symbolsBlock(n) {
  const block = body => `<div class="im-section"><h3>Simboli e chiamate</h3>${body}</div>`;
  if (SYMBOLS?.file !== n.id) loadSymbols(n.id);
  if (SYMBOLS.loading) return block('<span class="im-loader" role="status"><span class="im-spinner" aria-hidden="true"></span>Lettura dei simboli…</span>');
  if (SYMBOLS.error) return block(noteHtml({ tone: 'err', title: 'Simboli non disponibili.', message: SYMBOLS.error, actionsHtml: retryButton('retry-symbols') }));
  const name = ref => SYMBOLS.symbols.find(s => s.id === ref)?.name || ref.replace(/^file:/, '');
  const sites = call => call.evidence.map(e => esc(e.path.split('/').pop() + ':' + e.line)).join(', ');
  return block(`<ul class="im-detail-list">${SYMBOLS.symbols.map(s => `<li><code>${esc(s.name)}</code> <span class="im-muted im-caption">righe ${esc((s.lines || []).join('–'))}${s.freshness ? ' · ' + esc(s.freshness) : ''}</span></li>`).join('') || '<li class="im-muted">Nessun simbolo nell’outline.</li>'}</ul><ul class="im-detail-list">${SYMBOLS.calls.map(c => `<li><code>${esc(name(c.source))} → ${esc(name(c.target))}</code> <span class="im-muted im-caption">${[sites(c), proofLabel(c.status, c.conflict)].filter(Boolean).join(' · ')}</span></li>`).join('') || '<li class="im-muted">Nessuna chiamata risolta da o verso i suoi simboli.</li>'}</ul>`);
}

async function loadSymbols(file) {
  SYMBOLS = { file, loading: true };
  try {
    const found = await get('/api/app/symbols?' + new URLSearchParams({ file }));
    if (SYMBOLS?.file === file) SYMBOLS = found;
  } catch (error) {
    if (error.busy) { setTimeout(() => { if (SYMBOLS?.file === file) loadSymbols(file); }, 2000); return; }
    if (SYMBOLS?.file === file) SYMBOLS = { file, error: error.message };
  }
  if (state.screen === 'graph') render();
}

function graph() {
  const action = ctx() ? `<div class="im-cluster"><button class="im-btn" data-action="snapshot">${icon('file')}Grafo e lacune</button><button class="im-btn" data-action="open-explorer">${icon('external')}Esploratore completo</button></div>` : '';
  const head = heading('Esplora le relazioni', 'Grafo del codice', 'Gruppi di file, dipendenze e percorsi del run. Ogni relazione conserva le sue evidenze.', action);
  if (!ctx()) return head + panelHtml(panelStateHtml({ kind: 'empty', title: 'Nessun grafo', text: 'Seleziona prima una repository e un branch.', actionHtml: '<button class="im-btn" data-screen="analysis">Vai al repository</button>' }));
  if (graphError) return head + failedPanel('Grafo non disponibile: ' + graphError, 'retry-graph');
  if (!GRAPH) return head + loadingPanel('graph');
  const g = visibleGraph();
  return head + `<div class="im-content-toolbar"><span class="im-input">${icon('search')}<input id="graph-search" type="search" aria-label="Cerca un gruppo o un file" placeholder="Cerca gruppo o file…" value="${esc(state.graphSearch)}"></span><div class="im-cluster"><div class="im-field"><label class="im-field-label" for="graph-direction">Direzione</label><select class="im-select" id="graph-direction">${selectOptions([['out', 'Dipendenze →'], ['in', '← Chiamanti'], ['both', 'Entrambe ↔']], state.graphDirection)}</select></div><div class="im-field"><label class="im-field-label" for="graph-depth">Profondità</label><select class="im-select" id="graph-depth">${selectOptions([['1', '1 livello'], ['2', '2 livelli'], ['all', 'Tutto il grafo']], state.graphDepth)}</select></div><div class="im-field"><label class="im-field-label" for="graph-kind">Relazioni</label><select class="im-select" id="graph-kind">${selectOptions([['all', 'Tutte'], ['calls', 'Chiamate'], ['imports', 'Import'], ['uses', 'Utilizzi']], state.graphKind)}</select></div><button class="im-btn im-btn--ghost im-btn--sm" data-action="clear-graph">Azzera filtri</button><span class="im-chip" data-im-tone="accent" data-im-align="end" title="Livelli della mappa del sistema mostrati">${esc(levelsName())}</span><span class="im-muted im-caption">${g.nodes.length} / ${GRAPH.nodes.length} nodi</span></div></div><section aria-label="Grafo interattivo"><div class="im-canvas-frame" id="graph-viewport">${graphCanvas(g)}</div>${graphLegendHtml([{ label: levelLabel() }, { label: 'Esterno', stroke: 'dashed' }, { label: 'Osservata in esecuzione', tone: 'accent' },
    { label: 'Campionata dal profiler', tone: 'accent', stroke: 'dashed' }, { label: 'Incerta o in conflitto', tone: 'warn', stroke: 'dashed' }],
    `${g.edges.length} relazioni visibili · seleziona un nodo, apri › sul posto`)}</section>`;
}

// -- the engine ----------------------------------------------------------------------------------------------------

function engineScreen() {
  const d = engineDraft || { engine: null, base_url: '', model: '', api_key: '' };
  const engines = server?.engine?.engines || [];
  const openai = d.engine === 'openai';
  const c = ctx();
  return heading('Motore e domande', 'Chiedi al codice.', 'Il motore legge la mappa solo con le operazioni di Daodan: cerca, poi legge quello che serve.') + `<div class="im-auto-grid"><section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="ask-title"><div class="im-panel-header im-split"><h2 id="ask-title">Domanda sul repository</h2><span class="im-chip">${c ? esc(slug(c)) : 'Nessuna repository'}</span></div><div class="im-inset im-stack"><form id="ask-form" novalidate><div class="im-field"><label class="im-field-label" for="question">Domanda</label><textarea class="im-textarea" id="question" rows="4" placeholder="Dove viene firmato un token, e chi lo verifica?" ${!c ? 'disabled' : ''}>${esc(question)}</textarea><p class="im-muted im-caption">${c ? 'Il motore usa il run ' + esc(c.run_id) + '.' : 'Seleziona prima una repository: il motore la legge dal suo run.'}</p></div><button class="im-btn im-btn--primary" type="submit" id="ask-button" ${server?.asked?.state === 'running' ? 'aria-busy="true"' : !c || !server?.engine?.engine ? `disabled title="${c ? 'Scegli e salva prima un motore.' : 'Seleziona prima una repository.'}"` : ''}>${busyIcon(server?.asked?.state === 'running', 'play')}Chiedi</button>${c && !server?.engine?.engine ? '<p class="im-muted im-caption">Scegli e salva prima un motore.</p>' : ''}</form><div id="answer-box" aria-live="polite">${answerMarkup()}</div></div></section>
  <aside class="im-stack"><section data-im-surface="sheet" class="im-surface im-panel" aria-labelledby="engine-title"><div class="im-panel-header im-split"><h2 id="engine-title">Motore</h2><span class="im-chip" data-im-tone="${server?.engine?.engine ? 'accent' : 'info'}">${esc(server?.engine?.engine || 'Non scelto')}</span></div><div class="im-inset im-stack"><form id="engine-form" novalidate><div class="im-field"><label class="im-field-label" for="engine-name">Motore</label><select class="im-select" id="engine-name">${selectOptions([['', 'Nessuno'], ...engines.map(e => [e, { openai: 'Endpoint compatibile OpenAI', claude: 'Claude Code (riga di comando)', codex: 'Codex (riga di comando)' }[e] || e])], d.engine || '')}</select></div>${openai ? `${textFieldHtml('Indirizzo dell’endpoint', 'base-url', d.base_url, { id: 'base-url', type: 'url', error: false })}${textFieldHtml('Modello', 'model', d.model, { id: 'model', error: false })}${textFieldHtml('Chiave', 'api-key', d.api_key, { id: 'api-key', type: 'password', error: false, attrs: { autocomplete: 'off' },
      hint: server?.engine?.api_key === 'set' ? 'Chiave impostata: lasciare vuoto per tenerla.' : 'Va nel deposito delle credenziali del sistema.' })}` : ''}${server?.engine?.unkept ? `<p class="im-muted im-caption">Non conservato per il prossimo avvio: ${esc(server.engine.unkept)}.</p>` : ''}<div class="im-cluster"><button class="im-btn" type="submit" id="engine-save">${icon('check')}Salva</button><button class="im-btn" type="button" data-action="probe" id="engine-probe">${icon('reload')}Prova il motore</button>${openai && server?.engine?.api_key === 'set' ? `<button class="im-btn im-btn--danger" type="button" data-action="forget-key">${icon('close')}Rimuovi la chiave</button>` : ''}</div><p id="engine-said" class="${engineTone === 'bad' ? 'im-text-err' : 'im-muted'}" role="status">${esc(engineSaid)}</p></form></div></section><section data-im-surface="sheet" class="im-surface im-panel"><div class="im-panel-header im-split"><h2>Server MCP</h2></div><div class="im-inset im-stack">${server?.mcp ? `<p class="im-muted">Per una sessione tua: avvia Daodan sul checkout con</p><code>${esc([server.mcp.command, ...server.mcp.args].join(' '))}</code><p class="im-muted im-caption">Pacchetti del server: ${esc(server.mcp_ready === 'ready' ? 'pronti' : server.mcp_ready)}</p>` : '<p class="im-muted">Disponibile dopo la selezione di una repository.</p>'}</div></section></aside></div>`;
}

function answerMarkup() {
  if (!asked) return server?.asked?.question ? `<p class="im-muted im-caption">Ultima domanda: ${esc(server.asked.question)} · ${esc(server.asked.state)}${server.asked.cause ? ' · ' + esc(server.asked.cause) : ''}</p>` : '';
  const tools = asked.tools.map(t => `<li><code>${esc(t)}</code></li>`).join('');
  return `${tools ? `<p class="im-kicker">Operazioni di Daodan usate</p><ul class="im-detail-list">${tools}</ul>` : ''}<p class="im-kicker">Risposta</p><p class="im-readout">${esc(asked.text || (asked.state === 'running' ? 'In attesa del motore…' : ''))}</p>${asked.state !== 'running' && asked.state !== 'done' ? noteHtml({ tone: 'err', title: asked.state, message: asked.cause || '' }) : ''}`;
}

function readEngineForm() {
  const value = id => document.getElementById(id)?.value;
  engineDraft = { ...engineDraft, engine: value('engine-name') || null };
  for (const [id, key] of [['base-url', 'base_url'], ['model', 'model'], ['api-key', 'api_key']]) if (document.getElementById(id)) engineDraft[key] = value(id).trim();
}

// The setting in the form: a key left empty is left out, and the server keeps the one it has.
function engineBody() {
  readEngineForm();
  const body = { engine: engineDraft.engine, base_url: engineDraft.base_url || '', model: engineDraft.model || '' };
  if (engineDraft.api_key) body.api_key = engineDraft.api_key;
  return body;
}

async function saveEngine() {
  const described = await post('/api/app/engine', engineBody());
  server.engine = described;
  engineDraft = { ...described, api_key: '' };
}

async function ask() {
  if (asked?.state === 'running' || server?.asked?.state === 'running') return;  // a busy button's submit, from the keyboard, does nothing
  question = document.getElementById('question').value;
  asked = { state: 'running', text: '', tools: [], cause: null };
  render();
  try {
    await post('/api/app/ask', { question });
    let after = 0;
    for (;;) {
      const found = await get(`/api/app/answer?after=${after}`);
      after = found.next;
      asked.tools.push(...found.events.filter(e => e.kind === 'tool').map(e => `${e.name} ${typeof e.arguments === 'string' ? e.arguments : JSON.stringify(e.arguments ?? '')}`));
      Object.assign(asked, { state: found.state, text: found.text, cause: found.cause });
      const box = document.getElementById('answer-box');
      if (box) box.innerHTML = answerMarkup();
      if (found.state !== 'running') break;
      await new Promise(resolve => setTimeout(resolve, 700));
    }
  } catch (error) {
    Object.assign(asked, { state: 'failed', cause: error.message });
  }
  render();
}

// -- the page ------------------------------------------------------------------------------------------------------

// -- the frame -----------------------------------------------------------------------------------------------------

// The window of Imago, written once: the three screens are the views of the title bar, the repository and the run are
// the status row, and the service (the app is local, the server answers, the engine) is the footer. The sidebar has no
// room in it: the app has one context at a time and no list of objects.
const SCREENS = [['analysis', 'Analisi', 'Vai ad Analisi'], ['graph', 'Grafo', 'Vai al Grafo'], ['engine', 'Motore e domande', 'Vai a Motore e domande']];
const screenTabs = () => SCREENS.map(([id, label]) => ({ id, label, controls: 'main', count: id === 'graph' ? GRAPH?.nodes.length : 0, countLabel: 'gruppi' }));

function writeFrame() {
  renderShellFrame(shell, shellFrameHtml({
    titlebarHtml: titlebarHtml({ brand: { name: 'Daodan' }, navigationHtml: tabNavigationHtml(screenTabs(), state.screen, { label: 'Schermate', action: 'screen' }),
      views: { label: 'Schermate', action: 'views' }, commands: { label: 'Comandi', action: 'palette', shortcut: formatKeys('Ctrl+K').join(' ') } }),
    statusHtml: '<span class="im-chip" id="context-state"></span><span class="im-status-text" id="context-text"></span><span class="im-spacer"></span><span class="im-status-end" id="context-run"></span>',
    contentHtml: '', contentLabel: 'Analisi', skipLabel: 'Vai al contenuto', inspectorLabel: 'Dettaglio',
    footerHtml: '<span class="im-dot" id="service-dot"></span><span class="im-footer-text" id="service-text"></span><span class="im-spacer"></span>',
  }));
  mountPage(shell, registry, { search: searchView });
  for (const [id, , title] of SCREENS) registry.register({ id: 'daodan.screen.' + id, title, group: 'Schermate', run: () => navigate(id) });
  roving(shell.querySelector('.im-titlebar'), { item: '[role="tab"]', orientation: 'horizontal', onSelect: tab => tab.click() });
  shell.querySelector('.im-footer').append(footerKeys(document, registry, [PALETTE_COMMAND, SEARCH_COMMAND, { keys: 'F6', title: 'Area successiva' }]));
}

function viewsMenu(anchor) {  // a radio item stays open: choosing a view closes the menu, and the page takes the focus
  const close = openMenu(anchor, SCREENS.map(([id, label]) => ({ label, checked: () => state.screen === id, run: () => { close(); navigate(id); } })));
}

// What a frame of the server or a click changes in the frame: the tab in view and its count, the context, the service.
function updateChrome() {
  const c = ctx(), preparing = server?.job.state === 'preparing', engine = server?.engine?.engine;
  for (const tab of shell.querySelectorAll('.im-titlebar [role="tab"]')) {
    const on = tab.dataset.id === state.screen;
    tab.setAttribute('aria-selected', String(on));
    if (on) tab.setAttribute('aria-current', 'page'); else tab.removeAttribute('aria-current');
    if (tab.dataset.id !== 'graph') continue;
    const count = GRAPH?.nodes.length || 0, badge = tab.querySelector('.im-count');
    if (count && !badge) tab.insertAdjacentHTML('beforeend', '<span class="im-count" aria-hidden="true"></span>');
    if (!count) badge?.remove(); else tab.querySelector('.im-count').textContent = count;
    if (count) tab.setAttribute('aria-label', `Grafo, ${count} gruppi`); else tab.removeAttribute('aria-label');
  }
  const main = document.getElementById('main'), name = SCREENS.find(([id]) => id === state.screen)[1];
  main.setAttribute('aria-label', name);
  const chip = document.getElementById('context-state');
  chip.textContent = c ? 'Contesto pronto' : preparing ? 'Preparazione in corso' : 'Nessuna repository';
  if (c) chip.dataset.imTone = 'ok'; else if (preparing) chip.dataset.imTone = 'info'; else delete chip.dataset.imTone;
  document.getElementById('context-text').innerHTML = c ? `<code id="context-repo" class="im-content-text">${esc(slug(c))}</code> · <code id="context-branch" class="im-content-text">${esc(c.branch)}</code> · <code id="context-commit" class="im-content-text">${esc(c.commit.slice(0, 12))}</code>` : '';
  document.getElementById('context-run').innerHTML = c ? `run <code id="context-run-id" class="im-content-text">${esc(c.run_id)}</code>` : '';
  const reachable = Boolean(server) && !serverError;
  document.getElementById('service-dot').dataset.imTone = reachable ? 'ok' : 'err';
  document.getElementById('service-text').textContent = (reachable ? 'App locale: il codice resta sul tuo disco' : 'Server non raggiungibile') + ' · ' + (engine ? 'Motore: ' + engine : 'Motore non scelto');
}

function render() {
  const focused = document.activeElement, activeId = focused?.id;
  let start, end;
  try { start = focused.selectionStart; end = focused.selectionEnd; } catch { }

  if (state.screen === 'engine' && document.getElementById('question')) question = document.getElementById('question').value;
  const treeFocus = focused?.dataset.imEntry;
  const focusedGraphNode = focused?.closest('[data-im-node]')?.dataset.imNode;
  page().innerHTML = '<div class="im-page-content">' + (state.screen === 'graph' ? graph() : state.screen === 'engine' ? engineScreen() : analysisWorkspace()) + '</div>';
  mountStageNav();
  mountTree(treeFocus);
  mountPipeline();
  mountDiagram();
  if (focusedGraphNode) {
    const card = [...(diagramHost?.querySelectorAll('[data-im-node]') ?? [])].find(el => el.dataset.imNode === focusedGraphNode);
    card?.querySelector(focused.classList.contains('im-graph-open') ? '.im-graph-open' : '.im-graph-node')?.focus({ preventScroll: true });
  }
  updateChrome();
  drawInspector();
  if (activeId) { const el = document.getElementById(activeId); if (el) { el.focus({ preventScroll: true }); if (start != null && typeof el.setSelectionRange === 'function') try { el.setSelectionRange(start, end); } catch { } } }
  save();
}

function navigate(screen, keepFocus = false) {  // a tab keeps its focus, a menu or a command takes it to the page
  closeInspector();
  wantGroup = screen === 'graph';
  state.screen = screen;
  loadViews();  // the graph screen draws its level, the analysis the first one
  render();
  page().scrollTop = 0;
  if (!keepFocus) document.getElementById('main').focus({ preventScroll: true });
}

// The details are the inspector's, which is not modal: the rest of the window keeps working. A view has a header with
// its title and its close button, a body that scrolls and, with actions, a foot. `opener` gets the focus back when the
// view closes, and takes it into the inspector now; a view with no opener leaves the focus where it is.
const GROUP_LABEL = 'Dettaglio del gruppo';
let drawn = null, wantGroup = false;  // what the inspector shows of the graph, and whether the person just asked for it
const inspectorRegion = () => shell.querySelector('.im-inspector');
function detailHtml(title, body, foot = '') {
  return `<header class="im-panel-header"><h4 class="im-panel-title">${esc(title)}</h4><span class="im-spacer"></span>${iconButtonHtml('Chiudi dettaglio', 'close-detail', 'close')}</header><div class="im-panel-body im-content-text">${body}</div>${foot ? `<footer class="im-panel-foot im-cluster">${foot}</footer>` : ''}`;
}
function detail(title, description, body, foot, opener, push = false) {
  const view = fragment(detailHtml(title, `<p class="im-muted">${esc(description)}</p>${body}`, foot));
  if (push && inspector(shell).isOpen()) { inspector(shell).push(view, opener); return; }
  inspectorRegion().setAttribute('aria-label', title);
  inspector(shell).open(view, opener);
}
function closeInspector() { while (inspector(shell).isOpen()) inspector(shell).close(); }

// After each drawing: the group of the graph screen is in the inspector when it just was chosen, or when its node, its
// symbols or the graph changed under it; never over another detail, and never from under a view pushed on it.
function drawInspector() {
  const region = inspectorRegion(), open = inspector(shell).isOpen();
  const n = state.screen === 'graph' && GRAPH && nodeById(state.graphRoot);
  if (!n || region.querySelector('[data-im-covered]') || (open && region.getAttribute('aria-label') !== GROUP_LABEL)) return;
  const changed = !drawn || drawn.root !== n.id || drawn.graph !== GRAPH || drawn.symbols !== SYMBOLS;
  if (!wantGroup && !changed) return;
  wantGroup = false;
  const content = groupDetails();  // asks the symbols of a file: SYMBOLS is what it asked
  drawn = { root: n.id, graph: GRAPH, symbols: SYMBOLS };
  region.setAttribute('aria-label', GROUP_LABEL);
  inspector(shell).open(content);
}

function snapshotDetail(opener) {
  const m = GRAPH?.meta || {}, gaps = gapLines();
  detail('Provenienza e lacune del grafo', 'Dati registrati nel run selezionato.', `<dl class="im-facts"><dt>Repository</dt><dd><code>${esc(slug())}</code></dd><dt>Branch e commit</dt><dd><code>${esc(ctx()?.branch)}</code> · <code>${esc(ctx()?.commit.slice(0, 12))}</code></dd><dt>Run</dt><dd><code>${esc(ctx()?.run_id)}</code></dd><dt>Grafo costruito</dt><dd>${esc(m.created_at || '—')}</dd><dt>File</dt><dd>${number(GRAPH?.files)}</dd><dt>${levelLabel()} / relazioni</dt><dd>${GRAPH?.nodes.length ?? '—'} / ${GRAPH?.edges.length ?? '—'}</dd><dt>Passaggio del grafo</dt><dd>${esc(pass().state || '—')}</dd></dl><p class="im-kicker">Limiti dichiarati</p>${noteHtml({ message: 'Le relazioni osservate provengono da chiamate registrate durante l’esecuzione. Le relazioni campionate provengono dal profiler. Possono esserci altre chiamate.' })}<ul class="im-detail-list">${gaps.map(g => `<li>${icon('info')}<span>${esc(g)}</span></li>`).join('') || `<li>${icon('check')}<span>Nessuna lacuna registrata dal run.</span></li>`}</ul><p class="im-caption im-muted">Digest dello snapshot: <code>${esc(m.snapshot_digest || '—')}</code></p>`, '', opener);
}

function premapProvenance(opener) {
  const c = ctx();
  detail('Provenienza della pre-mappa', 'Snapshot del checkout, manifest e risultati degli strumenti di build.', `<dl class="im-facts"><dt>Repository</dt><dd><code>${esc(slug(c))}</code></dd><dt>Branch</dt><dd><code>${esc(c.branch)}</code></dd><dt>Commit</dt><dd><code>${esc(c.commit)}</code></dd><dt>Run</dt><dd><code>${esc(c.run_id)}</code></dd><dt>File nello snapshot</dt><dd>${number(PREMAP?.files.length)}</dd><dt>Unità tecniche</dt><dd>${PREMAP?.units.length ?? '—'}</dd><dt>Dipendenze per unità</dt><dd>${number(PREMAP?.dependencies.length)}</dd></dl><ul class="im-detail-list"><li>${icon('info')}<span>I linguaggi provengono dai sorgenti dello snapshot. Le tecnologie e le dipendenze provengono dalla mappa dello stack.</span></li><li>${icon('info')}<span>Il manifest fornisce il vincolo dichiarato. Il modello di build fornisce la versione risolta e la relazione diretta o transitiva, quando disponibili.</span></li><li>${icon('info')}<span>Uno strumento usato dagli analyzer non prova che il progetto usi quel framework.</span></li></ul>`, '', opener);
}

function sourceDetail(path, opener) {
  const edges = GRAPH.edges.flatMap(e => e.evidence.filter(ev => ev.path === path || ev.target === path).map(ev => ({ ...ev, source: e.source, target: e.target, status: e.status })));
  detail(path.split('/').pop(), 'File dello snapshot del run.', `<p><code>${esc(path)}</code></p><p class="im-muted">La pagina mostra la provenienza registrata, senza aprire o eseguire il sorgente.</p><h3>Relazioni registrate</h3><ul class="im-detail-list">${edges.slice(0, 8).map(e => `<li>${icon('arrow')}<span>${esc(endName(e.source))} → ${esc(endName(e.target))}<br><code>${esc(e.kind)}${e.key ? ' · ' + esc(e.key) : ''}${proofLabel(e.status, e.conflict) ? ' · ' + proofLabel(e.status, e.conflict) : ''}${e.line ? ' · riga ' + e.line : ''}${e.target && e.path === path ? ' · ' + esc(e.target) : ''}</code></span></li>`).join('') || '<li>Nessuna relazione tra gruppi cita questo file.</li>'}</ul>`, '', opener, true);
}

document.addEventListener('click', async event => {
  const b = event.target.closest('button');
  if (!b || b.disabled || b.getAttribute('aria-busy') === 'true') return;  // a busy button ignores a second press, the keyboard's too
  if (b.dataset.screen) { navigate(b.dataset.screen); return; }
  if (b.dataset.action === 'screen') { navigate(b.dataset.id, true); return; }
  if (b.dataset.action === 'views') { viewsMenu(b); return; }
  if (b.dataset.action === 'palette') { registry.get(PALETTE_COMMAND)?.run(); return; }
  if (b.dataset.analysisStage) { selectStage(b.dataset.analysisStage); return; }




  if (b.dataset.pathCard) { loadPathPage(b.dataset.pathCard, 0, pathPage, true); return; }
  if (b.dataset.previewNode) { state.graphRoot = b.dataset.previewNode; state.graphOpen = []; state.graphDepth = '1'; state.graphSearch = ''; navigate('graph'); return; }
  if (b.dataset.openNode) { openGroup(b.dataset.openNode); return; }

  if (b.dataset.closeNode) { closeGroup(b.dataset.closeNode); state.graphRoot = b.dataset.closeNode; wantGroup = true; loadGraph(); render(); return; }  // the group closed is selected again
  if (b.dataset.sourcePath) { sourceDetail(b.dataset.sourcePath, b); return; }
  switch (b.dataset.action) {
    case 'path-effects': loadPathPage(orphanWrites, 0, pathPage, true); break;
    case 'path-next': loadPathPage(pathPage.id, pathPage.result.next_offset, pathPage, true); break;
    case 'path-prev': pathPage = pathPage.previous; drawPaths(true); break;
    case 'path-list': {
      const refresh = Boolean(pathPage?.error);
      while (pathPage?.id) pathPage = pathPage.previous;
      if (!pathPage || refresh) loadPathPage(null, 0, null, true);
      else drawPaths(true);
      break;
    }
    case 'path-retry': loadPathPage(pathPage.id, pathPage.offset, pathPage.previous, true); break;
    case 'use-repository': await selectRepository(); break;
    case 'retry-premap': premapRun = ''; loadPremap(); break;
    case 'retry-graph': graphError = ''; graphRun = ''; loadGraph(); break;
    case 'retry-symbols': SYMBOLS = null; drawn = null; wantGroup = true; render(); break;
    case 'retry-pass': try { applyState(await post('/api/app/retry', {})); } catch (error) { failure(error.message); } break;
    case 'find-links': try { applyState(await post('/api/app/link', {})); } catch (error) { failure(error.message); } break;
    case 'close-detail': inspector(shell).close(); break;
    case 'snapshot': snapshotDetail(b); break;
    case 'open-explorer': window.open(explorerUrl(), '_blank', 'noopener'); break;
    case 'premap-provenance': premapProvenance(b); break;
    case 'open-full-graph': state.graphDepth = 'all'; state.graphSearch = ''; state.graphOpen = []; navigate('graph'); break;
    case 'clear-tree-search': state.treeSearch = ''; render(); break;
    case 'clear-graph': state.graphSearch = ''; state.graphDepth = 'all'; state.graphDirection = 'both'; state.graphKind = 'all'; render(); notice('Filtri azzerati: tutti i gruppi del grafo sono visibili.'); break;
    case 'component-files': { const n = nodeById(state.graphRoot); detail('File di ' + nodeName(n), 'File assegnati al gruppo nel grafo del run.', `<ul class="im-detail-list">${n.files.map(p => `<li><code>${esc(p)}</code></li>`).join('')}</ul>`, '', b, true); break; }
    case 'forget-key':
      if (!await confirm(shell, { title: 'Rimuovere la chiave?', danger: true, confirm: 'Rimuovi la chiave', cancel: 'Annulla',
        body: 'La chiave dell’endpoint viene tolta dal deposito delle credenziali del sistema e non si può recuperare: per usare di nuovo il motore dovrai inserirla un’altra volta.' })) break;
      try { server.engine = await post('/api/app/engine', { api_key: '' }); engineSaid = server.engine.api_key === 'set' ? 'Chiave rimossa: resta quella dell’ambiente.' : 'Chiave rimossa.'; engineTone = 'good'; } catch (error) { engineSaid = error.message; engineTone = 'bad'; }
      render();
      break;
    case 'probe': {
      engineSaid = 'Prova in corso…'; engineTone = ''; render();
      try {
        const found = await post('/api/app/probe', engineBody());
        const tools = found.tools === null ? 'strumenti tramite MCP' : found.tools ? 'chiama gli strumenti' : 'non ha chiamato lo strumento';
        engineSaid = found.reachable ? `${found.engine}: risponde, ${tools}.` : `${found.engine}: non risponde. ${found.detail || ''}`;
        engineTone = found.reachable && found.tools !== false ? 'good' : 'bad';
      } catch (error) { engineSaid = error.message; engineTone = 'bad'; }
      render();
      break;
    }
  }
});

document.addEventListener('submit', async event => {
  event.preventDefault();
  if (event.target.id === 'repository-form') await verifyRepositoryUrl();
  if (event.target.id === 'ask-form') await ask();
  if (event.target.id === 'engine-form') {
    try { await saveEngine(); engineSaid = 'Motore salvato.'; engineTone = 'good'; } catch (error) { engineSaid = error.message; engineTone = 'bad'; }
    render();
  }
});

document.addEventListener('input', event => {
  const el = event.target;
  if (el.id === 'repository-url') {
    state.repositoryUrl = el.value;
    generation++;
    checked = null; checking = false; checkError = ''; selectError = '';
    render();
  } else if (el.id === 'premap-search') { state.treeSearch = el.value; render(); }
  else if (el.id === 'graph-search') { state.graphSearch = el.value; render(); }
  else if (el.id === 'question') question = el.value;
});

document.addEventListener('change', event => {
  const el = event.target;
  if (el.id === 'repository-branch') { branch = el.value; return; }
  if (el.id === 'engine-name') { readEngineForm(); render(); return; }
  const map = { 'graph-direction': 'graphDirection', 'graph-depth': 'graphDepth', 'graph-kind': 'graphKind' };
  if (map[el.id]) { state[map[el.id]] = el.value; render(); }
});



writeFrame();
startWait('server');
render();
observe();
if (!storageAvailable) notice('Archiviazione del browser non disponibile: le scelte durano questa apertura.');
