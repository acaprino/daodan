"use strict";
// The app's page: the journey of the mockup (repository, pre-map, analysis, synthesis and graph) over the local server.
// The server's state is the truth; the browser keeps only where the person was looking.
const token = new URLSearchParams(location.search).get('token') ?? '';
const auth = { 'X-Daodan-Token': token };
async function answer(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `il server ha risposto ${response.status}`);
  return body;
}
const get = path => fetch(path, { headers: auth, cache: 'no-store' }).then(answer);
const post = (path, body) => fetch(path, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(answer);

const STORAGE = 'daodan-app-v2';  // v2: the graph opens whole, so what v1 kept of its filters is dropped
const defaults = { screen: 'analysis', analysisStage: 'repository', repositoryUrl: '', runId: '', treeMode: 'directories', treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '', graphDirection: 'both', graphDepth: 'all', graphKind: 'all' };
let state = { ...defaults }, storageAvailable = true, toastTimer, modalReturnFocus = null;
try { const stored = JSON.parse(localStorage.getItem(STORAGE) || 'null'); if (stored && typeof stored === 'object') state = { ...defaults, ...stored }; } catch { storageAvailable = false; }
if (!['analysis', 'graph', 'engine'].includes(state.screen)) state.screen = 'analysis';
if (!['repository', 'premap', 'analysis', 'synthesis'].includes(state.analysisStage)) state.analysisStage = 'repository';

// What the server answered: never kept in the browser.
let server = null, serverError = '';
let checked = null, checkedUrl = '', branch = '', checking = false, checkError = '', selectError = '', selecting = false, generation = 0;
let PREMAP = null, premapRun = '', premapError = '';
let GRAPH = null, graphRun = '', graphError = '', graphLoading = false;
let events = [], cursors = { after: 0, pipeline_after: 0, pulse_after: 0 }, eventsRun = '';
let engineDraft = null, engineSaid = '', engineTone = '', question = '', asked = null, shown = '';
const FINAL = ['fresh', 'unavailable', 'failed', 'off'];
const STEPS = [['scan', 'Scan · inventario e moduli'], ['stack', 'Stack · tecnologie e librerie'], ['analyze', 'Analyze · analyzer per linguaggio'], ['dynamic', 'Dynamic · osservazione dei test'], ['union', 'Union · collegamento dei grafi']];
const STEP = Object.fromEntries(STEPS.map(([id, label]) => [id, label.split(' · ')[0]]));

function save() { try { localStorage.setItem(STORAGE, JSON.stringify(state)); } catch { storageAvailable = false; } }
function esc(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function icon(name){const paths={analysis:'<path d="M4 19V9m8 10V4m8 15v-7"/>',graph:'<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M9 6h9v9M6 9v9h9"/>',review:'<path d="M14 3H5v18h14V8z"/><path d="M14 3v6h5M8 13h8M8 17h5"/>',check:'<path d="m5 12 4 4L19 6"/>',pause:'<path d="M8 5v14M16 5v14"/>',play:'<path d="m8 4 12 8-12 8z"/>',arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',chevron:'<path d="m9 5 7 7-7 7"/>',search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',close:'<path d="m6 6 12 12M18 6 6 18"/>',plus:'<path d="M12 5v14M5 12h14"/>',file:'<path d="M14 3H5v18h14V8zM14 3v6h5"/>',branch:'<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="6" r="2"/><path d="M6 7v10M8 15h4a6 6 0 0 0 6-6V8"/>',info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',warning:'<path d="m12 3 10 18H2zM12 9v5m0 3h.01"/>',reload:'<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 7a7 7 0 0 1 12-2l2 2M4 17l2 2a7 7 0 0 0 12-2"/>',external:'<path d="M14 3h7v7M21 3 10 14M10 5H4v15h15v-6"/>',download:'<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>',copy:'<rect x="8" y="8" width="12" height="13" rx="1"/><path d="M16 8V3H3v13h5"/>',code:'<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"/>',layers:'<path d="m12 3 10 6-10 6L2 9zM2 13l10 6 10-6M2 17l10 6 10-6"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',spinner:'<path d="M21 12a9 9 0 1 1-9-9"/>',shield:'<path d="m12 3 8 3v6c0 4-8 9-8 9s-8-5-8-9V6z"/><path d="m8 12 3 3 5-6"/>'};return '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'+(paths[name]||paths.code)+'</svg>';}
function toast(message) { const el = document.getElementById('toast'); el.textContent = message; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => el.hidden = true, 4500); }
function heading(eyebrow, title, description, action = '') { return `<div class="page-heading"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${description}</p></div>${action}</div>`; }
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
  server = found;
  serverError = '';
  const c = ctx();
  if (engineDraft === null) engineDraft = { ...server.engine, api_key: '' };
  if (c && state.runId !== c.run_id) {  // what the browser kept belongs to another run
    if (state.runId && state.analysisStage !== 'repository') state.analysisStage = 'premap';
    Object.assign(state, { runId: c.run_id, treeSearch: '', treeSelected: '', treeOpen: {}, graphSearch: '', graphRoot: '' });
    PREMAP = GRAPH = null;
  }
  if (!c) state.runId = '';
  if (selecting && server.job.state !== 'preparing') {
    selecting = false;
    if (c && server.job.state === 'ready') {
      state.analysisStage = 'premap';
      toast('Contesto pronto: ' + slug() + ' · ' + c.branch);
    }
  }
  loadViews();
  show();
}

function applyEvents(found) {
  const run = found.run_events;
  if (eventsRun !== run.run_id) { events = []; eventsRun = run.run_id; }
  cursors = { after: run.next_cursor, pipeline_after: run.pipeline.next_cursor, pulse_after: found.pulse.next_cursor };
  events.push(...run.events.map(e => ({ ...e, run: true })), ...run.pipeline.events);
  const grown = run.pipeline.events.some(e => e.kind === 'step.finished' || e.kind === 'graph.ready');
  if (grown && ctx()?.run_id === run.run_id && (state.analysisStage !== 'repository' || state.screen === 'graph')) loadGraph();
  show();
}

function loadViews() {  // what the stage on screen draws, read once a run
  const c = ctx();
  if (c && graphRun !== c.run_id && (state.analysisStage !== 'repository' || state.screen === 'graph')) loadGraph();
  if (c && premapRun !== c.run_id && ['premap', 'synthesis'].includes(state.analysisStage)) loadPremap();
}

function show() {  // draws again what a frame changed
  const signature = JSON.stringify([server?.job, ctx()?.run_id, pass(), server?.run?.progress, events.length, server?.engine, server?.mcp_ready, server?.asked]);
  if (signature === shown) return;
  shown = signature;
  if (state.screen === 'analysis' && state.analysisStage === 'analysis' && document.getElementById('run-title')) updateAnalysisRun();
  else render();
}

async function loadPremap() {
  const run = ctx()?.run_id;
  if (!run || premapRun === run) return;
  premapRun = run; premapError = ''; PREMAP = null;
  try {
    const found = await get('/api/app/premap');
    if (ctx()?.run_id !== run) return;
    PREMAP = { ...found, dependencies: found.units.flatMap(u => u.dependencies.map(d => ({ ...d, unit: u.name }))) };
  } catch (error) {
    premapError = error.message;
    premapRun = '';
  }
  render();
}

async function loadGraph() {
  const run = ctx()?.run_id;
  if (!run || graphLoading) return;
  graphLoading = true;
  try {
    const found = await get('/api/app/graph');
    if (ctx()?.run_id !== run) return;
    GRAPH = found; graphRun = run; graphError = '';
    if (!GRAPH.nodes.some(n => n.id === state.graphRoot)) {
      const related = id => GRAPH.edges.filter(e => e.source === id || e.target === id).length;  // the group with most relations first
      state.graphRoot = [...GRAPH.nodes].sort((a, b) => related(b.id) - related(a.id) || b.files.length - a.files.length)[0]?.id || '';
    }
  } catch (error) {
    graphError = error.message;
    graphRun = run;
  } finally {
    graphLoading = false;
  }
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
  if (checked?.state === 'accessible') toast(`${checked.repository.owner}/${checked.repository.name}: ${checked.branches.length} branch letti da GitHub.`);
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
  return `<div class="repository-context"><div>${icon('code')}<strong>${esc(slug(c))}</strong><span class="badge">${icon('branch')}${esc(c.branch)}</span><code>${esc(c.commit.slice(0, 12))}</code><span class="muted small">Pubblica, senza login</span></div><p>Checkout in sola lettura del commit <code>${esc(c.commit.slice(0, 12))}</code>; run <code>${esc(c.run_id)}</code>. Nessun file del progetto viene eseguito.</p><button class="textbutton small" data-analysis-stage="repository">Cambia repository o branch ${icon('arrow')}</button></div>`;
}

function preparation() {
  const job = server?.job;
  if (!job || job.state === 'idle') return '';
  const step = { checkout: 'Checkout del branch', snapshot: 'Snapshot e pre-mappa' }[job.step] || job.step || '';
  if (job.state === 'preparing') return `<p class="repository-auth-copy" role="status">${icon('spinner')} Preparazione in corso: ${esc(step)}${job.detail ? ' · ' + esc(job.detail) : ''}.</p>`;
  if (job.state === 'failed') return `<div class="alert error" role="alert"><strong>Preparazione non riuscita (${esc(step)}).</strong><br>${esc(job.detail)}</div>`;
  return '';
}

function repositoryScreen() {
  const repo = checked?.state === 'accessible' ? checked : null;
  const preparing = server?.job.state === 'preparing';
  const feedback = checked && !repo ? {
    not_accessible: 'Repository non accessibile senza login: potrebbe non esistere o richiedere permessi. Il login GitHub non è disponibile in questa versione.',
    network: 'Errore di rete: riprova la verifica. Il login non risolve un errore di connessione.',
    empty: 'La repository non ha branch: non c’è nulla da analizzare.',
  }[checked.state] + (checked.detail ? ' (' + checked.detail + ')' : '') : '';
  const c = ctx();
  return `<div class="source-note">${icon('info')}<div><strong>Repository GitHub pubblica</strong><p>Daodan legge i branch e scarica quello scelto in sola lettura; nulla del progetto viene eseguito su questa macchina. Il login GitHub non è disponibile in questa versione.</p></div></div><div class="repository-layout"><section class="panel"><div class="panel-head"><h2>Repository GitHub</h2><span class="badge">Selezione del progetto</span></div><div class="panel-body"><form id="repository-form" novalidate><div class="field"><label for="repository-url">URL GitHub</label><input id="repository-url" type="url" value="${esc(state.repositoryUrl)}" placeholder="https://github.com/proprietario/repository" aria-describedby="repository-url-help repository-error repository-access-feedback" ${checkError ? 'aria-invalid="true"' : ''}><p id="repository-url-help" class="muted small">Inserisci l’URL e verifica l’accesso. Senza login si aprono solo repository pubbliche.</p><p id="repository-error" class="error-text" role="alert">${esc(checkError)}</p><p id="repository-access-feedback" class="repository-auth-copy" role="status">${esc(feedback)}</p></div><button type="submit" id="verify-repository" ${checking ? 'disabled' : ''}>${icon(checking ? 'spinner' : 'check')}${checking ? 'Verifica…' : 'Verifica accesso'}</button></form>
  <div class="repository-branch"><div class="field"><label for="repository-branch">Branch da analizzare</label><select id="repository-branch" ${!repo || checking || preparing ? 'disabled' : ''}>${repo ? selectOptions(repo.branches.map(b => [b.name, b.name + ' · ' + b.commit.slice(0, 12)]), branch) : '<option>Verifica prima l’accesso</option>'}</select></div><p class="muted small">Preferenza automatica: <code>main</code>, poi <code>master</code>, altrimenti il branch predefinito della repository.</p>${repo ? `<p class="repository-branch-source">${repo.branches.length} branch letti ora da GitHub; predefinito <code>${esc(repo.default || '—')}</code>.</p>` : ''}</div><div class="repository-preparation">${preparation()}${selectError ? `<p class="error-text" role="alert">${esc(selectError)}</p>` : ''}</div><div class="repository-next"><p class="muted small">Un altro repository o branch prepara un nuovo checkout; lo stesso commit riusa l’analisi già fatta.</p><button class="primary" data-action="use-repository" id="use-repository" ${!repo || checking || preparing ? 'disabled' : ''}>${preparing ? icon('spinner') + 'Preparazione…' : 'Apri pre-mappa ' + icon('arrow')}</button></div></div></section>
  <aside class="stack"><section class="panel"><div class="panel-head"><h2>Accesso GitHub</h2>${icon('code')}</div><div class="panel-body"><span class="badge">Non connesso</span><h3 style="margin-top:16px">Login non disponibile</h3><p class="repository-auth-copy">In questa versione Daodan legge solo repository pubbliche, senza account. Un accesso negato non dimostra che la repository sia privata: può non esistere o mancare un permesso.</p></div></section><section class="panel"><div class="panel-head"><h2>Contesto attivo</h2></div><div class="panel-body">${c ? `<ul class="repository-source-list"><li><strong>Repository</strong><span><code>${esc(slug(c))}</code></span></li><li><strong>Branch e commit</strong><span><code>${esc(c.branch)}</code> · <code>${esc(c.commit.slice(0, 12))}</code></span></li><li><strong>Run</strong><span><code>${esc(c.run_id)}</code></span></li></ul><button class="textbutton small" data-analysis-stage="premap">Torna alla pre-mappa ${icon('arrow')}</button>` : `<p class="repository-auth-copy">${preparing ? 'Preparazione in corso: il contesto sarà pronto alla fine del checkout e dello snapshot.' : 'Nessuna repository selezionata sul server.'}</p>`}</div></section></aside></div>`;
}

// -- the analysis workspace ---------------------------------------------------------------------------------------

function analysisWorkspace() {
  if (!server) return heading('Codebase intelligence', 'Analisi del repository', 'Lettura dello stato del server…') + (serverError ? `<div class="alert error" role="alert"><strong>Server non raggiungibile.</strong> ${esc(serverError)}</div>` : waiting('Lettura dello stato…', 'Repository, run e passaggi li dice il server.'));
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
  const action = stage === 'premap' ? `<button class="primary" data-analysis-stage="analysis">${icon('play')}Segui l’analisi</button>`
    : stage === 'synthesis' ? `<button class="primary" data-action="open-full-graph">${icon('graph')}Esplora il grafo completo</button>`
      : stage === 'analysis' ? `<button data-action="open-explorer">${icon('external')}Apri l’esploratore</button>` : '';
  return heading(eyebrow, title, description, action) + analysisStageNav() + (serverError ? `<div class="alert error" role="alert"><strong>Server non raggiungibile.</strong> ${esc(serverError)}</div>` : '') +
    (stage === 'repository' ? repositoryScreen() : repositoryContext() + (stage === 'premap' ? premapScreen() : stage === 'synthesis' ? synthesisScreen() : analysisRunScreen()));
}

function analysisStageNav() {
  return `<nav class="analysis-journey" aria-label="Percorso di analisi">
    ${[['repository', 'Repository', 'GitHub e branch'], ['premap', 'Pre-mappa', 'Inventario e tecnologie'], ['analysis', 'Analisi', 'Pipeline e costruzione'], ['synthesis', 'Sintesi e grafo', 'Risultati e lacune']].map(([id, title, sub], i) => `
      <button data-analysis-stage="${id}" id="stage-${id}" ${state.analysisStage === id ? 'aria-current="step"' : ''} ${(id !== 'repository' && !ctx()) || (id === 'synthesis' && !complete()) ? 'disabled' : ''}>
        <span class="journey-number">${state.analysisStage === id ? icon(id === 'premap' ? 'layers' : id === 'analysis' ? 'analysis' : id === 'repository' ? 'code' : 'graph') : String(i + 1).padStart(2, '0')}</span>
        <span><strong>${title}</strong><small>${sub}</small></span>${i < 3 ? icon('chevron') : ''}
      </button>`).join('')}
  </nav>`;
}

function waiting(title, text) {
  return `<div class="panel skeleton"><div class="stack"><h2>${title}</h2><p class="muted">${text}</p></div></div>`;
}

// -- 1. pre-map ----------------------------------------------------------------------------------------------------

function premapSourceLine() {
  const c = ctx();
  return `<div class="source-strip"><span>${icon('branch')}<strong>Checkout ${esc(slug(c))} · ${esc(c.branch)}</strong><code>${esc(c.commit.slice(0, 12))}</code></span><span>Snapshot del run ${esc(c.run_id)} · dichiarazioni dei manifest</span><button class="textbutton small" data-action="premap-provenance">Provenienza ${icon('info')}</button></div>`;
}

function premapScreen() {
  if (premapError) return `<div class="alert error" role="alert"><strong>Pre-mappa non disponibile.</strong> ${esc(premapError)}</div><button data-action="retry-premap">${icon('reload')}Riprova</button>`;
  if (!PREMAP) return waiting('Lettura della pre-mappa…', 'Inventario dello snapshot, tecnologie e manifest del run.');
  const languages = PREMAP.languages;
  return premapSourceLine() + `<div class="premap-summary metrics">
    <div class="metric"><div class="value">${number(PREMAP.files.length)}</div><p>File nello snapshot</p><small>Inventario del checkout</small></div>
    <div class="metric"><div class="value">${languages.length}</div><p>Linguaggi rilevati</p><small>File sorgente riconosciuti</small></div>
    <div class="metric"><div class="value">${PREMAP.units.length}</div><p>Unità tecniche</p><small>Da manifest e strumenti di build</small></div>
    <div class="metric"><div class="value">${number(PREMAP.dependencies.length)}</div><p>Dichiarazioni di dipendenza</p><small>Manifest, non risoluzione</small></div>
  </div>
  <div class="premap-layout">
    <section class="panel premap-tree-panel" aria-labelledby="tree-title">
      <div class="panel-head"><div><h2 id="tree-title">Struttura del repository</h2><p class="muted small">Directory fisiche e unità tecniche restano distinte.</p></div>${icon('layers')}</div>
      <div class="tree-toolbar"><div class="segmented" aria-label="Tipo di albero"><button data-tree-mode="directories" aria-pressed="${state.treeMode === 'directories'}">${icon('file')}Directory</button><button data-tree-mode="units" aria-pressed="${state.treeMode === 'units'}">${icon('code')}Unità tecniche</button></div>
      <label class="searchbox">${icon('search')}<span class="sr-only">Cerca nell’albero</span><input id="premap-search" type="search" placeholder="Cerca percorso o unità…" value="${esc(state.treeSearch)}"></label></div>
      <div class="repository-tree" aria-label="${state.treeMode === 'directories' ? 'Albero delle directory' : 'Albero delle unità tecniche'}">${state.treeMode === 'directories' ? directoryTree() : technicalTree()}</div>
      <div class="tree-selection" id="tree-selection">${premapSelection()}</div>
    </section>
    <aside class="stack premap-context" aria-label="Tecnologie e dipendenze dichiarate">
      <section class="panel"><div class="panel-head"><h2>Linguaggi</h2><span class="badge">Inventario</span></div><div class="language-list">${languages.map(l => `<div class="language-row"><span><i style="background:${languageColor(l.name)}"></i>${esc(l.name)}</span><strong>${number(l.files)}<small> file</small></strong></div>`).join('') || '<p class="muted small" style="padding:16px">Nessun file sorgente riconosciuto.</p>'}</div><p class="aside-note">File sorgente dello snapshot, per linguaggio riconosciuto da Daodan.</p></section>
      <section class="panel"><div class="panel-head"><h2>Tecnologie e framework</h2><span class="badge">Riconosciuti</span></div><div class="technology-list">${PREMAP.technologies.map(t => `<div class="technology-row"><div><strong>${esc(t.name)}</strong><span class="badge">${esc(t.category)}</span></div><p>${esc(t.version || (t.state === 'declared' ? 'Versione non dichiarata' : 'Versione non registrata'))}</p><code>${esc(t.source)}</code></div>`).join('') || '<p class="muted small" style="padding:16px">Nessuna tecnologia riconosciuta nei manifest.</p>'}</div></section>
    </aside>
  </div>
  <section class="panel dependency-panel" aria-labelledby="dependency-title"><div class="panel-head"><div><h2 id="dependency-title">Librerie prima dell’analisi</h2><p class="muted small">Dichiarazioni dei manifest, lette dallo step stack.</p></div><span class="badge">Dipendenze dichiarate</span></div><div class="dependency-table-wrap"><table class="dependency-table"><thead><tr><th>Dipendenza</th><th>Versione dichiarata</th><th>Ecosistema</th><th>Fonte</th></tr></thead><tbody>${PREMAP.dependencies.map(d => `<tr><td><strong>${esc(d.name)}</strong></td><td><code>${esc(d.version || 'Non scritta nel manifest')}</code></td><td><span class="badge">${esc(d.scope)}</span></td><td><code>${esc(d.source)}</code></td></tr>`).join('') || '<tr><td colspan="4" class="muted">Nessuna libreria dichiarata nei manifest.</td></tr>'}</tbody></table></div><p class="aside-note">Una dichiarazione non dimostra che una libreria sia installata, risolta o chiamata. La versione è quella scritta nel manifest, non quella installata.</p></section>`;
}

function languageColor(name) {
  const colors = { Python: '#64748b', TypeScript: '#a78bba', JavaScript: '#c9a65d', CSS: '#859eab', HTML: '#bd8c78' };
  return colors[name] || '#a1a1aa';
}

function directoryTree() {
  const query = state.treeSearch.trim().toLowerCase();
  const paths = PREMAP.files.filter(p => !query || p.toLowerCase().includes(query));
  if (!paths.length) return '<div class="empty"><p>Nessun percorso corrisponde alla ricerca.</p><button class="textbutton" data-action="clear-tree-search">Azzera ricerca</button></div>';
  const root = { children: Object.create(null), count: paths.length };
  for (const path of paths) {
    let node = root;
    const parts = path.split('/');
    parts.forEach((part, i) => {
      node.children[part] ||= { children: Object.create(null), count: 0, path: parts.slice(0, i + 1).join('/'), file: i === parts.length - 1 };
      node = node.children[part];
      node.count++;
    });
  }
  function draw(node, depth) {
    return Object.entries(node.children).sort(([a, x], [b, y]) => Number(x.file) - Number(y.file) || a.localeCompare(b, 'it')).map(([name, child]) => {
      const selected = state.treeSelected === child.path;
      if (child.file) return `<button class="tree-file ${selected ? 'selected' : ''}" data-tree-select="${esc(child.path)}" style="--depth:${depth}" aria-pressed="${selected}">${icon('file')}<span>${esc(name)}</span></button>`;
      const id = 'directory:' + child.path;
      const open = query || state.treeOpen[id] || (depth === 0 && state.treeOpen[id] !== false);
      return `<details class="tree-directory" data-tree-id="${esc(id)}" ${open ? 'open' : ''}><summary style="--depth:${depth}"><span class="tree-caret">${icon('chevron')}</span>${icon('layers')}<span>${esc(name)}</span><small>${child.count}</small></summary><div>${draw(child, depth + 1)}</div></details>`;
    }).join('');
  }
  return `<div class="tree-root">${icon('code')}<strong>${esc(ctx().repository.name)}</strong><span>${paths.length} file${query ? ' trovati' : ''}</span></div>${draw(root, 0)}`;
}

const UNIT_STATUS = { confirmed: 'Confermata', inferred: 'Inferita', incomplete: 'Incompleta' };
function technicalTree() {
  const query = state.treeSearch.trim().toLowerCase();
  const matched = PREMAP.units.filter(u => !query || [u.name, u.kind, u.root, u.manifest].join(' ').toLowerCase().includes(query));
  if (!matched.length) return `<div class="empty"><p>${PREMAP.units.length ? 'Nessuna unità tecnica corrisponde alla ricerca.' : 'Nessuna unità tecnica dichiarata dai manifest.'}</p>${query ? '<button class="textbutton" data-action="clear-tree-search">Azzera ricerca</button>' : ''}</div>`;
  const visible = new Set(matched.map(u => u.id));
  for (const unit of matched) {
    let parent = unit.parent;
    while (parent) {
      visible.add(parent);
      parent = PREMAP.units.find(u => u.id === parent)?.parent;
    }
  }
  function draw(parent) {
    return PREMAP.units.filter(u => (u.parent || null) === parent && visible.has(u.id)).map(u => {
      const id = 'unit:' + u.id;
      const selected = state.treeSelected === id;
      return `<details class="technical-unit" data-tree-id="${esc(id)}" ${query || state.treeOpen[id] || (parent === null && state.treeOpen[id] !== false) ? 'open' : ''}><summary><span class="tree-caret">${icon('chevron')}</span>${icon('code')}<span>${esc(u.name)}<small>${esc(u.kind)}</small></span><span class="badge">${esc(UNIT_STATUS[u.status] || u.status || 'Dichiarata')}</span></summary><div class="unit-members"><button class="tree-file ${selected ? 'selected' : ''}" data-tree-select="${esc(id)}" aria-pressed="${selected}">${icon('info')}<span>Confine tecnico e fonte</span></button>${u.manifest ? `<button class="tree-file" data-tree-select="${esc(u.manifest)}" aria-pressed="${state.treeSelected === u.manifest}">${icon('file')}<span>${esc(u.manifest)}</span></button>` : ''}<p><code>${esc(u.root || '.')}</code></p>${draw(u.id)}</div></details>`;
    }).join('');
  }
  return `<div class="tree-root">${icon('code')}<strong>Unità da manifest</strong><span>${PREMAP.units.length} ${PREMAP.units.length === 1 ? 'unità' : 'unità'}</span></div>${draw(null)}`;
}

function premapSelection() {
  const selected = state.treeSelected;
  if (!selected) return `<span class="muted">${icon('info')}Seleziona un file o apri un’unità per leggerne la provenienza.</span>`;
  if (selected.startsWith('unit:')) {
    const unit = PREMAP.units.find(u => 'unit:' + u.id === selected);
    if (unit) return `<p class="eyebrow">Unità tecnica · ${esc(UNIT_STATUS[unit.status] || unit.status || 'dichiarata')}</p><h3>${esc(unit.name)}</h3><p>${esc(unit.kind)} · <code>${esc(unit.root || '.')}</code></p>${unit.manifest ? `<code>${esc(unit.manifest)}</code>` : ''}${unit.description ? `<p>${esc(unit.description)}</p>` : ''}<p class="muted">${unit.dependencies.length} librerie dichiarate. Il manifest ne indica il confine tecnico; non è una responsabilità semantica inferita.</p>`;
  }
  const extension = selected.split('/').pop().includes('.') ? selected.split('.').pop() : 'senza estensione';
  return `<p class="eyebrow">File dell’inventario</p><h3>${esc(selected.split('/').pop())}</h3><code>${esc(selected)}</code><p class="muted">Tipo: ${esc(extension)} · fonte: snapshot del commit ${esc(ctx().commit.slice(0, 12))}. Il contenuto non viene eseguito.</p>`;
}

// -- 2. analysis ---------------------------------------------------------------------------------------------------

function pipelineEvents() { return events.filter(e => !e.run); }

// The run's steps as SmoothUI's AITaskList draws them, in the states their events say: the pass's state is the
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
    return { id, label, status: s, note };
  });
}

function mountPipeline() {
  const host = document.getElementById('smooth-analysis-tasks');
  if (!host) return;
  if (window.DaodanSmoothUI) window.DaodanSmoothUI.mount(host, Object.values(STEP).join(' → '), steps());
  else host.textContent = 'Passi della pipeline non disegnati: smoothui.bundle.js non è stato caricato.';
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
  return `<strong>${p.state === 'failed' ? 'Il passaggio che rifinisce il grafo delle chiamate non è riuscito.' : 'Lacuna: il passaggio che rifinisce il grafo delle chiamate non è disponibile.'}</strong><br>${esc(p.reason || 'Nessuna causa registrata.')}${p.state === 'failed' ? `<br><button data-action="retry-pass" style="margin-top:10px">${icon('play')}Riprova il passaggio</button>` : ''}`;
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
  if (!items.length) return '<p class="muted small" style="padding:14px 0">Nessun evento ancora.</p>';
  return items.slice(-8).reverse().map(l => `<div class="log-item ${l.type}"><span class="dot"></span><div><strong>${esc(l.title)}</strong><p>${esc(l.detail)}</p></div><time datetime="${esc(l.at)}">${esc(l.at ? new Date(l.at).toLocaleTimeString('it-IT') : '')}</time></div>`).join('');
}

function runButton() {
  return complete() ? `<button id="run-toggle" class="primary" data-analysis-stage="synthesis">${icon('review')}Leggi sintesi</button>` : `<button id="run-toggle" disabled>${icon('spinner')}Analisi in corso</button>`;
}

function nodeName(n) { return n.kind === 'directory' && n.name === '.' ? 'radice del repository' : n.name; }
const NODE_STATUS = { confirmed: 'confermato', inferred: 'inferito', incomplete: 'incompleto', proposed: 'proposto' };
function nodeState(n) { return n.location === 'external' ? 'esterno' : NODE_STATUS[n.status] || n.status || 'senza stato'; }
function levelLabel() { return GRAPH?.level === 'modules' ? 'Moduli' : 'Directory'; }

function buildPreview() {
  if (graphError) return `<div class="build-empty">${icon('warning')}<h3>Grafo non disponibile.</h3><p>${esc(graphError)}</p></div>`;
  const g = GRAPH;
  if (!g || !g.nodes.length) return `<div class="build-empty">${icon('graph')}<h3>Prima l’inventario, poi le relazioni.</h3><p>${g ? 'Il grafo del run non ha ancora gruppi di file.' : 'Lettura del grafo del run…'}<br>I nodi compaiono quando la pipeline scrive un artefatto.</p></div>`;
  const width = 624, cols = 3, height = Math.max(300, Math.ceil(g.nodes.length / cols) * 92 + 46);
  const position = new Map(g.nodes.map((n, i) => [n.id, { x: 22 + (i % cols) * 201, y: 24 + Math.floor(i / cols) * 92 }]));
  return `<div class="build-world" style="width:${width}px;height:${height}px"><svg class="build-connections" width="${width}" height="${height}" aria-hidden="true">${g.edges.map(e => { const a = position.get(e.source), b = position.get(e.target); return `<path d="M${a.x + 88},${a.y + 59} C${a.x + 88},${a.y + 79} ${b.x + 88},${b.y - 20} ${b.x + 88},${b.y}"></path>`; }).join('')}</svg>${g.nodes.map(n => { const p = position.get(n.id); return `<button class="build-node" data-build-node="${esc(n.id)}" style="left:${p.x}px;top:${p.y}px">${icon(n.location === 'external' ? 'external' : 'layers')}<span>${esc(nodeName(n))}<small>${n.files.length} file · ${esc(nodeState(n))}</small></span></button>`; }).join('')}</div>`;
}

function buildCounts() { return GRAPH ? `${GRAPH.nodes.length} ${GRAPH.level === 'modules' ? 'moduli' : 'directory'} · ${GRAPH.edges.length} relazioni · ${number(GRAPH.files)} file` : '—'; }
function buildStatus() {
  if (graphLoading) return 'Lettura del grafo…';
  if (pipelineEvents().some(e => e.kind === 'graph.ready')) return 'Grafo completo scritto';
  return complete() ? 'Costruzione conclusa' : 'Costruzione in corso';
}

function analysisRunScreen() {
  const c = ctx(), percent = runPercent(), alert = passAlert();
  return `<div class="source-note">${icon('info')}<div><strong>Analisi del commit ${esc(c.commit.slice(0, 12))}.</strong><p>Avanzamento ed eventi sono quelli del run <code>${esc(c.run_id)}</code>. Il grafo cresce solo quando la pipeline scrive un artefatto.</p></div></div>
  <div class="run-build-layout"><section class="panel" aria-labelledby="run-title"><div class="panel-body"><div class="run-status"><div><p class="eyebrow">Esecuzione</p><h2 id="run-title">${esc(runPhaseLabel())}</h2><div class="row"><span class="badge ${pass().state === 'failed' ? 'bad' : 'cyan'}" id="run-badge"><span class="dot"></span>${statusLabel()}</span><span id="run-button-wrap">${runButton()}</span></div></div><div class="progress-number"><span id="progress-value">${percent}</span><small>%</small></div></div><div class="progress" role="progressbar" aria-label="Passi completati della pipeline" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}" id="run-progress"><span id="progress-fill" style="width:${percent}%"></span></div><p class="run-help" id="run-help">${esc(runHelp())}</p><div id="smooth-analysis-tasks" class="daodan-pipeline"></div><div id="run-error" class="alert ${pass().state === 'failed' ? 'error' : ''}" style="margin-top:16px" role="status" ${alert ? '' : 'hidden'}>${alert}</div></div><div class="run-footer"><span class="muted">Repository: <code>${esc(slug(c))}</code> · <code>${esc(c.branch)}</code> · intero progetto</span></div></section>
  <section class="panel building-panel" aria-labelledby="building-title"><div class="panel-head"><div><h2 id="building-title">Costruzione del grafo</h2><p class="muted small">Gruppi di file e relazioni dal grafo del run.</p></div><span class="badge" id="build-level">${levelLabel()}</span></div><div class="build-viewport" id="build-viewport">${buildPreview()}</div><div class="build-foot"><span id="build-counts">${buildCounts()}</span><span id="build-status">${buildStatus()}</span></div></section></div>
  <section class="panel run-activity" aria-labelledby="activity-title"><div class="panel-head"><h2 id="activity-title">Eventi e feedback</h2><span class="badge">${logItems().length} eventi</span></div><div class="logs" id="logs" aria-live="polite" aria-relevant="additions">${renderLogs()}</div></section>`;
}

function updateAnalysisRun() {
  const stageButton = document.getElementById('stage-synthesis');
  if (stageButton) stageButton.disabled = !complete();
  if (state.screen !== 'analysis' || state.analysisStage !== 'analysis' || !ctx() || !document.getElementById('run-title')) return render();
  const percent = runPercent(), alert = passAlert();
  document.getElementById('run-title').textContent = runPhaseLabel();
  document.getElementById('progress-value').textContent = percent;
  document.getElementById('progress-fill').style.width = percent + '%';
  document.getElementById('run-progress').setAttribute('aria-valuenow', percent);
  const badge = document.getElementById('run-badge');
  badge.className = 'badge ' + (pass().state === 'failed' ? 'bad' : 'cyan');
  badge.innerHTML = '<span class="dot"></span>' + statusLabel();
  document.getElementById('run-help').textContent = runHelp();
  mountPipeline();
  const error = document.getElementById('run-error');
  error.hidden = !alert;
  error.className = 'alert ' + (pass().state === 'failed' ? 'error' : '');
  error.innerHTML = alert;
  const hadFocus = document.activeElement?.id === 'run-toggle';
  document.getElementById('run-button-wrap').innerHTML = runButton();
  if (hadFocus) document.getElementById('run-toggle').focus({ preventScroll: true });
  document.getElementById('logs').innerHTML = renderLogs();
  const viewport = document.getElementById('build-viewport');
  const drawn = GRAPH ? GRAPH.nodes.length + '/' + GRAPH.edges.length : graphError || 'none';
  if (viewport.dataset.drawn !== drawn) {
    const left = viewport.scrollLeft, top = viewport.scrollTop;
    viewport.innerHTML = buildPreview();
    viewport.dataset.drawn = drawn;
    viewport.scrollLeft = left; viewport.scrollTop = top;
  }
  document.getElementById('build-level').textContent = levelLabel();
  document.getElementById('build-counts').textContent = buildCounts();
  document.getElementById('build-status').textContent = buildStatus();
  document.getElementById('graph-nav-count').textContent = GRAPH ? GRAPH.nodes.length : '—';
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

function synthesisScreen() {
  if (!GRAPH) return graphError ? `<div class="alert error" role="alert"><strong>Grafo non disponibile.</strong> ${esc(graphError)}</div>` : waiting('Lettura del grafo…', 'Gruppi, relazioni e lacune del run.');
  const top = [...GRAPH.nodes].sort((a, b) => b.files.length - a.files.length).slice(0, 3), gaps = gapLines();
  const modules = GRAPH.level === 'modules';
  return `<div class="source-note">${icon('info')}<div><strong>Sintesi testuale in attesa.</strong><p>Questa versione non fa scrivere una sintesi al motore: qui ci sono i conteggi, le responsabilità dichiarate e le lacune del run <code>${esc(ctx().run_id)}</code>. Le domande al motore sono in «Motore e domande».</p></div></div><div class="metrics"><div class="metric"><div class="value">${GRAPH.nodes.length}</div><p>${modules ? 'Moduli' : 'Directory con file'}</p><small>Gruppi del grafo</small></div><div class="metric"><div class="value">${GRAPH.edges.length}</div><p>Relazioni statiche</p><small>Non tracce runtime</small></div><div class="metric"><div class="value">${number(GRAPH.files)}</div><p>File nel grafo</p><small>Snapshot del commit ${esc(ctx().commit.slice(0, 7))}</small></div><div class="metric"><div class="value">${number(modules ? GRAPH.unassigned.count : GRAPH.symbols)}</div><p>${modules ? 'File senza modulo' : 'Simboli definiti'}</p><small>${modules ? 'Lacuna esplicita del grafo' : 'Dall’outline dei file'}</small></div></div>
  <div class="synthesis-layout"><section class="panel"><div class="panel-head"><h2>Responsabilità da esplorare</h2><span class="badge">${levelLabel()}</span></div><div class="synthesis-components">${top.map(n => `<button data-preview-node="${esc(n.id)}"><span class="synthesis-icon">${icon('layers')}</span><span><strong>${esc(nodeName(n))}</strong><p>${esc(n.responsibility || 'Responsabilità non descritta nel grafo.')}</p><small>${n.files.length} file · ${esc(nodeState(n))}</small></span>${icon('arrow')}</button>`).join('') || '<p class="muted small" style="padding:16px">Nessun gruppo nel grafo.</p>'}</div></section><aside class="stack"><section class="panel"><div class="panel-head"><h2>Dipendenze dopo l’analisi</h2></div><div class="panel-body"><span class="badge orange">Risoluzione non disponibile</span><p class="synthesis-note">${PREMAP ? number(PREMAP.dependencies.length) + ' librerie dichiarate nei manifest. ' : ''}Daodan non risolve le versioni installate: un riferimento statico non prova quale versione di una libreria sia usata.</p></div></section><section class="panel"><div class="panel-head"><h2>Cosa manca al quadro</h2></div><div class="panel-body"><ul class="synthesis-gaps">${gaps.slice(0, 8).map(g => `<li>${esc(g)}</li>`).join('') || '<li>Nessuna lacuna registrata dal run.</li>'}</ul>${gaps.length > 8 ? `<p class="muted small">Altre ${gaps.length - 8} lacune in «Provenienza e lacune».</p>` : ''}<button class="textbutton" data-action="snapshot">${icon('file')}Provenienza e lacune</button></div></section></aside></div>`;
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
  const ids = new Set(nodes.map(n => n.id));
  return { nodes, edges: edges.filter(e => ids.has(e.source) && ids.has(e.target)) };
}

function graphCanvas(g) {
  if (!g.nodes.length) return '<div class="empty"><h2>Nessun gruppo trovato</h2><p style="margin:10px 0">Cambia ricerca o amplia il perimetro del grafo.</p><button data-action="clear-graph">Azzera filtri</button></div>';
  const ordered = [...g.nodes].sort((a, b) => a.id === state.graphRoot ? -1 : b.id === state.graphRoot ? 1 : a.name.localeCompare(b.name, 'it'));
  const cols = Math.min(3, ordered.length), width = Math.max(650, cols * 254 + 50), height = Math.max(460, Math.ceil(ordered.length / cols) * 130 + 90);
  const positions = new Map(ordered.map((n, i) => [n.id, { x: 30 + (i % cols) * 254, y: 42 + Math.floor(i / cols) * 130 }]));
  const paths = g.edges.map(e => { const a = positions.get(e.source), b = positions.get(e.target), same = a.y === b.y; const fromX = a.x + 102, fromY = a.y + 74, toX = b.x + 102, toY = b.y; const d = same ? `M${a.x + 204},${a.y + 37} C${a.x + 230},${a.y + 37} ${b.x - 26},${b.y + 37} ${b.x},${b.y + 37}` : `M${fromX},${fromY} C${fromX},${fromY + 32} ${toX},${toY - 32} ${toX},${toY}`; return `<path d="${d}" marker-end="url(#arrowhead)"><title>${esc(nodeName(nodeById(e.source)))} → ${esc(nodeName(nodeById(e.target)))} · ${Object.entries(e.counts).map(([k, v]) => esc(k) + ': ' + v).join(', ')}</title></path>`; }).join('');
  return `<div class="graph-world" style="width:${width}px;height:${height}px"><svg class="connections" width="${width}" height="${height}" aria-hidden="true"><defs><marker id="arrowhead" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" style="fill:var(--edge);stroke:none"></path></marker></defs>${paths}</svg>${ordered.map(n => { const p = positions.get(n.id); return `<button class="graph-node ${n.id === state.graphRoot ? 'selected' : ''} ${n.location === 'external' ? 'external' : ''}" data-node="${esc(n.id)}" aria-pressed="${n.id === state.graphRoot}" style="left:${p.x}px;top:${p.y}px"><span class="node-icon">${icon(n.location === 'external' ? 'external' : 'layers')}</span><span><span class="node-name">${esc(nodeName(n))}</span><small>${n.files.length} file · ${esc(nodeState(n))}</small></span></button>`; }).join('')}</div>`;
}

function inspector() {
  const n = nodeById(state.graphRoot);
  const related = GRAPH.edges.filter(e => e.source === n.id || e.target === n.id);
  return `<aside class="graph-inspector" aria-label="Dettaglio del gruppo"><p class="eyebrow">${GRAPH.level === 'modules' ? 'Modulo selezionato' : 'Directory selezionata'}</p><h2>${esc(nodeName(n))}</h2><span class="badge ${n.location === 'external' ? '' : 'cyan'}">${n.location === 'external' ? 'Dipendenza esterna' : esc(nodeState(n))}</span><p class="description">${esc(n.responsibility || 'Responsabilità non descritta nel grafo.')}</p><div class="inspector-block"><h3>Perimetro</h3><dl class="facts"><dt>File assegnati</dt><dd>${n.files.length}</dd><dt>Relazioni statiche</dt><dd>${related.length}</dd><dt>Provenienza</dt><dd>${esc(n.provenance || (n.kind === 'directory' ? 'Directory del checkout' : 'Non registrata'))}</dd></dl></div><div class="inspector-block"><h3>Evidenze</h3><ul class="source-list">${(n.evidence || []).map(e => `<li><code>${esc(e.path)}${e.line ? ':' + e.line : ''}</code></li>`).join('') || '<li class="muted">Nessuna evidenza dichiarata.</li>'}</ul></div><div class="inspector-block"><h3>File del gruppo</h3><ul class="source-list">${n.files.slice(0, 4).map(path => `<li><button data-source-path="${esc(path)}">${icon('file')}<span>${esc(path.split('/').slice(-2).join('/'))}</span></button></li>`).join('') || '<li class="muted">Gruppo esterno: nessun file locale.</li>'}</ul>${n.files.length > 4 ? `<button class="textbutton small" data-action="component-files">Tutti i ${n.files.length} file ${icon('arrow')}</button>` : ''}</div></aside>`;
}

function graph() {
  const action = ctx() ? `<div class="heading-actions"><button data-action="snapshot">${icon('file')}Grafo e lacune</button><button data-action="open-explorer">${icon('external')}Esploratore completo</button></div>` : '';
  const head = heading('Esplora le relazioni', 'Grafo del codice', 'Gruppi di file, dipendenze e percorsi del run. Ogni relazione conserva le sue evidenze.', action);
  if (!ctx()) return head + `<div class="empty"><h2>Nessun grafo</h2><p style="margin:10px 0">Seleziona prima una repository e un branch.</p><button data-screen="analysis">Vai al repository</button></div>`;
  if (graphError) return head + `<div class="alert error" role="alert"><strong>Grafo non disponibile.</strong> ${esc(graphError)}</div>`;
  if (!GRAPH) return head + waiting('Lettura del grafo…', 'Gruppi, relazioni e lacune del run.');
  const g = visibleGraph();
  return head + `<div class="graph-toolbar"><label class="searchbox">${icon('search')}<span class="sr-only">Cerca un gruppo o un file</span><input id="graph-search" type="search" placeholder="Cerca gruppo o file…" value="${esc(state.graphSearch)}"></label><div class="filter-row"><label class="field-inline">Direzione<select id="graph-direction">${selectOptions([['out', 'Dipendenze →'], ['in', '← Chiamanti'], ['both', 'Entrambe ↔']], state.graphDirection)}</select></label><label class="field-inline">Profondità<select id="graph-depth">${selectOptions([['1', '1 livello'], ['2', '2 livelli'], ['all', 'Tutto il grafo']], state.graphDepth)}</select></label><label class="field-inline">Relazioni<select id="graph-kind">${selectOptions([['all', 'Tutte'], ['calls', 'Chiamate'], ['imports', 'Import'], ['uses', 'Utilizzi']], state.graphKind)}</select></label><button class="textbutton small" data-action="clear-graph">Azzera filtri</button><span class="muted small" style="margin-left:auto">${g.nodes.length} / ${GRAPH.nodes.length} ${GRAPH.level === 'modules' ? 'moduli' : 'directory'}</span></div></div><div class="graph-layout"><section class="graph-stage" aria-label="Grafo interattivo"><div class="graph-viewport" id="graph-viewport">${graphCanvas(g)}</div><div class="graph-foot"><span><span style="color:var(--accent)">■</span> ${levelLabel()} &nbsp; <span style="color:var(--muted)">□</span> Esterno</span><span>${g.edges.length} relazioni visibili · seleziona un nodo</span></div></section>${inspector()}</div>`;
}

// -- the engine ----------------------------------------------------------------------------------------------------

function engineScreen() {
  const d = engineDraft || { engine: null, base_url: '', model: '', api_key: '' };
  const engines = server?.engine?.engines || [];
  const openai = d.engine === 'openai';
  const c = ctx();
  return heading('Motore e domande', 'Chiedi al codice.', 'Il motore legge la mappa solo con le operazioni di Daodan: cerca, poi legge quello che serve.') + `<div class="repository-layout"><section class="panel" aria-labelledby="ask-title"><div class="panel-head"><h2 id="ask-title">Domanda sul repository</h2><span class="badge">${c ? esc(slug(c)) : 'Nessuna repository'}</span></div><div class="panel-body"><form id="ask-form" novalidate><div class="field"><label for="question">Domanda</label><textarea id="question" rows="4" placeholder="Dove viene firmato un token, e chi lo verifica?" ${!c ? 'disabled' : ''}>${esc(question)}</textarea><p class="muted small">${c ? 'Il motore usa il run ' + esc(c.run_id) + '.' : 'Seleziona prima una repository: il motore la legge dal suo run.'}</p></div><button type="submit" class="primary" id="ask-button" style="margin-top:12px" ${!c || server?.asked?.state === 'running' || !server?.engine?.engine ? 'disabled' : ''}>${icon(server?.asked?.state === 'running' ? 'spinner' : 'play')}${server?.asked?.state === 'running' ? 'Il motore risponde…' : 'Chiedi'}</button>${c && !server?.engine?.engine ? '<p class="muted small">Scegli e salva prima un motore.</p>' : ''}</form><div id="answer-box" class="answer-box" aria-live="polite">${answerMarkup()}</div></div></section>
  <aside class="stack"><section class="panel" aria-labelledby="engine-title"><div class="panel-head"><h2 id="engine-title">Motore</h2><span class="badge ${server?.engine?.engine ? 'cyan' : ''}">${esc(server?.engine?.engine || 'Non scelto')}</span></div><div class="panel-body"><form id="engine-form" novalidate><div class="field"><label for="engine-name">Motore</label><select id="engine-name">${selectOptions([['', 'Nessuno'], ...engines.map(e => [e, { openai: 'Endpoint compatibile OpenAI', claude: 'Claude Code (riga di comando)', codex: 'Codex (riga di comando)' }[e] || e])], d.engine || '')}</select></div>${openai ? `<div class="field"><label for="base-url">Indirizzo dell’endpoint</label><input id="base-url" type="url" value="${esc(d.base_url)}"></div><div class="field"><label for="model">Modello</label><input id="model" type="text" value="${esc(d.model)}"></div><div class="field"><label for="api-key">Chiave</label><input id="api-key" type="password" autocomplete="off" value="${esc(d.api_key)}" placeholder="${server?.engine?.api_key === 'set' ? 'Impostata: resta in memoria' : 'Resta in memoria, non viene scritta'}"></div>` : ''}<div class="row"><button type="submit" id="engine-save">${icon('check')}Salva</button><button type="button" data-action="probe" id="engine-probe">${icon('reload')}Prova il motore</button></div><p id="engine-said" class="${engineTone === 'bad' ? 'error-text' : 'repository-auth-copy'}" role="status">${esc(engineSaid)}</p></form></div></section><section class="panel"><div class="panel-head"><h2>Server MCP</h2></div><div class="panel-body">${server?.mcp ? `<p class="repository-auth-copy">Per una sessione tua: avvia Daodan sul checkout con</p><code style="overflow-wrap:anywhere">${esc([server.mcp.command, ...server.mcp.args].join(' '))}</code><p class="muted small" style="margin-top:12px">Pacchetti del server: ${esc(server.mcp_ready === 'ready' ? 'pronti' : server.mcp_ready)}</p>` : '<p class="repository-auth-copy">Disponibile dopo la selezione di una repository.</p>'}</div></section></aside></div>`;
}

function answerMarkup() {
  if (!asked) return server?.asked?.question ? `<p class="muted small">Ultima domanda: ${esc(server.asked.question)} · ${esc(server.asked.state)}${server.asked.cause ? ' · ' + esc(server.asked.cause) : ''}</p>` : '';
  const tools = asked.tools.map(t => `<li><code>${esc(t)}</code></li>`).join('');
  return `${tools ? `<p class="eyebrow" style="margin-top:20px">Operazioni di Daodan usate</p><ul class="source-list">${tools}</ul>` : ''}<p class="eyebrow" style="margin-top:20px">Risposta</p><p style="white-space:pre-wrap">${esc(asked.text || (asked.state === 'running' ? 'In attesa del motore…' : ''))}</p>${asked.state !== 'running' && asked.state !== 'done' ? `<div class="alert error" role="alert"><strong>${esc(asked.state)}</strong> ${esc(asked.cause || '')}</div>` : ''}`;
}

function readEngineForm() {
  const value = id => document.getElementById(id)?.value;
  engineDraft = { ...engineDraft, engine: value('engine-name') || null };
  for (const [id, key] of [['base-url', 'base_url'], ['model', 'model'], ['api-key', 'api_key']]) if (document.getElementById(id)) engineDraft[key] = value(id).trim();
}

async function saveEngine() {
  readEngineForm();
  const body = { engine: engineDraft.engine, base_url: engineDraft.base_url || '', model: engineDraft.model || '' };
  if (engineDraft.api_key) body.api_key = engineDraft.api_key;
  const described = await post('/api/app/engine', body);
  server.engine = described;
  engineDraft = { ...described, api_key: '' };
}

async function ask() {
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

function render() {
  const focused = document.activeElement, activeId = focused?.id;
  let start, end;
  try { start = focused.selectionStart; end = focused.selectionEnd; } catch { }
  const scroll = document.getElementById('graph-viewport');
  const graphScroll = scroll ? { left: scroll.scrollLeft, top: scroll.scrollTop } : null;
  if (state.screen === 'engine' && document.getElementById('question')) question = document.getElementById('question').value;
  window.DaodanSmoothUI?.unmount();  // its host goes with the markup it is in
  document.getElementById('main').innerHTML = state.screen === 'graph' ? graph() : state.screen === 'engine' ? engineScreen() : analysisWorkspace();
  mountPipeline();
  document.querySelectorAll('[data-screen]').forEach(b => { if (b.classList.contains('nav-item') && b.dataset.screen === state.screen) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
  const c = ctx(), preparing = server?.job.state === 'preparing';
  document.getElementById('crumb-screen').textContent = { analysis: 'Analisi', graph: 'Grafo', engine: 'Motore e domande' }[state.screen];
  document.getElementById('crumb-project').textContent = c ? c.repository.name : '—';
  document.getElementById('graph-nav-count').textContent = GRAPH ? GRAPH.nodes.length : '—';
  document.getElementById('selected-repository-mark').textContent = c ? c.repository.name[0].toUpperCase() : 'D';
  document.getElementById('selected-repository-name').textContent = c ? c.repository.name : preparing ? 'Preparazione…' : 'Seleziona repository';
  document.getElementById('selected-repository-meta').textContent = c ? c.branch + ' · ' + c.commit.slice(0, 7) : 'GitHub · pubblica';
  document.getElementById('context-source').innerHTML = c ? '<code>' + esc(slug(c)) + '</code><span>·</span><code>' + esc(c.branch) + '</code>' : '<span>' + (preparing ? 'Preparazione in corso' : 'Nessuna repository') + '</span>';
  document.getElementById('engine-foot').textContent = server?.engine?.engine ? 'Motore: ' + server.engine.engine + '.' : 'Motore non scelto.';
  document.querySelectorAll('[data-icon]').forEach(el => el.innerHTML = icon(el.dataset.icon));
  if (activeId) { const el = document.getElementById(activeId); if (el) { el.focus({ preventScroll: true }); if (start != null && typeof el.setSelectionRange === 'function') try { el.setSelectionRange(start, end); } catch { } } }
  if (graphScroll && state.screen === 'graph') { const viewport = document.getElementById('graph-viewport'); if (viewport) { viewport.scrollLeft = graphScroll.left; viewport.scrollTop = graphScroll.top; } }
  save();
}

function navigate(screen) {
  state.screen = screen;
  if (screen === 'graph' && ctx() && graphRun !== ctx().run_id) loadGraph();
  render();
  window.scrollTo({ top: 0, behavior: 'instant' });
  document.getElementById('main').focus({ preventScroll: true });
}

function modal(title, description, body, footer) { modalReturnFocus = document.activeElement; document.getElementById('modal-root').innerHTML = `<div class="modal-backdrop"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="modal-description"><div class="modal-head"><div><h2 id="modal-title">${title}</h2><p id="modal-description">${description}</p></div><button aria-label="Chiudi finestra" data-action="close-modal">${icon('close')}</button></div><div class="modal-body">${body}</div>${footer ? `<div class="modal-footer">${footer}</div>` : ''}</section></div>`; document.body.style.overflow = 'hidden'; const first = document.querySelector('.modal-body input,.modal-body textarea,.modal-body select') || document.querySelector('.modal-head button'); first?.focus(); }
function closeModal() { document.getElementById('modal-root').innerHTML = ''; document.body.style.overflow = ''; modalReturnFocus?.focus({ preventScroll: true }); }

function snapshotModal() {
  const m = GRAPH?.meta || {}, gaps = gapLines();
  modal('Provenienza e lacune del grafo', 'Dati del run selezionato; nessun file del progetto è stato eseguito.', `<dl class="facts"><dt>Repository</dt><dd><code>${esc(slug())}</code></dd><dt>Branch e commit</dt><dd><code>${esc(ctx()?.branch)}</code> · <code>${esc(ctx()?.commit.slice(0, 12))}</code></dd><dt>Run</dt><dd><code>${esc(ctx()?.run_id)}</code></dd><dt>Grafo costruito</dt><dd>${esc(m.created_at || '—')}</dd><dt>File / simboli</dt><dd>${number(GRAPH?.files)} / ${number(GRAPH?.symbols)}</dd><dt>${levelLabel()} / relazioni</dt><dd>${GRAPH?.nodes.length ?? '—'} / ${GRAPH?.edges.length ?? '—'}</dd><dt>Passaggio del grafo</dt><dd>${esc(pass().state || '—')}</dd></dl><p class="eyebrow" style="margin:20px 0 10px">Limiti dichiarati</p><div class="alert">Le relazioni statiche non dimostrano un comportamento runtime. L’assenza di un arco di chiamata non dimostra indipendenza.</div><ul class="checked-list">${gaps.map(g => `<li>${icon('info')}<span>${esc(g)}</span></li>`).join('') || `<li>${icon('check')}<span>Nessuna lacuna registrata dal run.</span></li>`}</ul><p class="small muted" style="margin-top:16px">Digest dello snapshot: <code style="overflow-wrap:anywhere">${esc(m.snapshot_digest || '—')}</code></p>`, `<button class="primary" data-action="close-modal">${icon('check')}Chiudi</button>`);
}

function premapProvenance() {
  const c = ctx();
  modal('Provenienza della pre-mappa', 'Snapshot del checkout e dichiarazioni dei manifest, senza eseguire nulla del progetto.', `<dl class="facts"><dt>Repository</dt><dd><code>${esc(slug(c))}</code></dd><dt>Branch</dt><dd><code>${esc(c.branch)}</code></dd><dt>Commit</dt><dd><code>${esc(c.commit)}</code></dd><dt>Run</dt><dd><code>${esc(c.run_id)}</code></dd><dt>File nello snapshot</dt><dd>${number(PREMAP?.files.length)}</dd><dt>Unità tecniche</dt><dd>${PREMAP?.units.length ?? '—'}</dd><dt>Dichiarazioni di dipendenza</dt><dd>${number(PREMAP?.dependencies.length)}</dd></dl><ul class="checked-list"><li>${icon('info')}<span>Linguaggi dai file sorgente dello snapshot; tecnologie e librerie dallo step stack, che legge i manifest.</span></li><li>${icon('info')}<span>Una dipendenza dichiarata non è una versione installata o risolta; le versioni delle librerie non sono ancora nel record.</span></li><li>${icon('info')}<span>Uno strumento usato dagli analyzer non prova che il progetto usi quel framework.</span></li></ul>`, `<button class="primary" data-action="close-modal">Chiudi provenienza</button>`);
}

function sourceModal(path) {
  const edges = GRAPH.edges.flatMap(e => e.evidence.filter(ev => ev.path === path || ev.target === path).map(ev => ({ ...ev, source: e.source, target: e.target })));
  modal(esc(path.split('/').pop()), 'File dello snapshot del run.', `<p style="overflow-wrap:anywhere"><code>${esc(path)}</code></p><p class="muted" style="font-size:12px;margin:12px 0 16px">La pagina mostra la provenienza registrata, senza aprire o eseguire il sorgente.</p><h3 style="margin-bottom:12px">Riferimenti statici</h3><ul class="checked-list">${edges.slice(0, 8).map(e => `<li>${icon('arrow')}<span>${esc(nodeName(nodeById(e.source)))} → ${esc(nodeName(nodeById(e.target)))}<br><code>${esc(e.kind)}${e.line ? ' · riga ' + e.line : ''}${e.target && e.path === path ? ' · ' + esc(e.target) : ''}</code></span></li>`).join('') || '<li>Nessuna relazione tra gruppi cita questo file.</li>'}</ul>`, `<button class="primary" data-action="close-modal">Chiudi dettaglio</button>`);
}

document.addEventListener('click', async event => {
  const b = event.target.closest('button');
  if (!b || b.disabled) return;
  if (b.dataset.screen) { navigate(b.dataset.screen); return; }
  if (b.dataset.analysisStage) {
    state.screen = 'analysis';
    state.analysisStage = b.dataset.analysisStage;
    loadViews();
    render();
    return;
  }
  if (b.dataset.treeMode) { state.treeMode = b.dataset.treeMode; render(); return; }
  if (b.dataset.treeSelect) {
    state.treeSelected = b.dataset.treeSelect;
    document.querySelectorAll('[data-tree-select]').forEach(x => { const selected = x.dataset.treeSelect === state.treeSelected; x.classList.toggle('selected', selected); x.setAttribute('aria-pressed', String(selected)); });
    document.getElementById('tree-selection').innerHTML = premapSelection();
    save();
    return;
  }
  if (b.dataset.buildNode) {
    const n = nodeById(b.dataset.buildNode);
    modal(esc(nodeName(n)), `${GRAPH.level === 'modules' ? 'Modulo' : 'Directory'} del grafo di questo run.`, `<p>${esc(n.responsibility || 'Responsabilità non descritta nel grafo.')}</p><p class="muted small" style="margin-top:16px">${n.files.length} file · ${esc(nodeState(n))} · commit ${esc(ctx().commit.slice(0, 12))}</p>`, `<button data-preview-node="${esc(n.id)}">${icon('graph')}Apri nel grafo</button><button class="primary" data-action="close-modal">Chiudi dettaglio</button>`);
    return;
  }
  if (b.dataset.previewNode) { closeModal(); state.graphRoot = b.dataset.previewNode; state.graphDepth = '1'; state.graphSearch = ''; navigate('graph'); return; }
  if (b.dataset.node) { state.graphRoot = b.dataset.node; render(); toast('Selezionato: ' + nodeName(nodeById(state.graphRoot))); return; }
  if (b.dataset.sourcePath) { sourceModal(b.dataset.sourcePath); return; }
  switch (b.dataset.action) {
    case 'use-repository': await selectRepository(); break;
    case 'retry-premap': premapRun = ''; loadPremap(); break;
    case 'retry-pass': try { applyState(await post('/api/app/retry', {})); } catch (error) { toast(error.message); } break;
    case 'close-modal': closeModal(); break;
    case 'snapshot': snapshotModal(); break;
    case 'open-explorer': window.open(explorerUrl(), '_blank', 'noopener'); break;
    case 'premap-provenance': premapProvenance(); break;
    case 'open-full-graph': state.graphDepth = 'all'; state.graphSearch = ''; navigate('graph'); break;
    case 'clear-tree-search': state.treeSearch = ''; render(); break;
    case 'clear-graph': state.graphSearch = ''; state.graphDepth = 'all'; state.graphDirection = 'both'; state.graphKind = 'all'; render(); toast('Filtri azzerati: tutti i gruppi del grafo sono visibili.'); break;
    case 'component-files': { const n = nodeById(state.graphRoot); modal('File di ' + esc(nodeName(n)), 'File assegnati al gruppo nel grafo del run.', `<ul class="source-list">${n.files.map(p => `<li><code>${esc(p)}</code></li>`).join('')}</ul>`, `<button class="primary" data-action="close-modal">Chiudi elenco</button>`); break; }
    case 'probe': {
      engineSaid = 'Prova in corso…'; engineTone = ''; render();
      try {
        await saveEngine();
        const found = await post('/api/app/probe', {});
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

document.addEventListener('toggle', event => {
  if (event.target.dataset?.treeId && document.contains(event.target)) { state.treeOpen[event.target.dataset.treeId] = event.target.open; save(); }
}, true);

document.addEventListener('keydown', event => { const dialog = document.querySelector('.modal'); if (!dialog) return; if (event.key === 'Escape') { event.preventDefault(); closeModal(); return; } if (event.key === 'Tab') { const focusable = [...dialog.querySelectorAll('button:not(:disabled),input:not(:disabled),textarea:not(:disabled),select:not(:disabled),a[href],[tabindex="0"]')]; const first = focusable[0], last = focusable.at(-1); if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } } });

render();
observe();
if (!storageAvailable) toast('Archiviazione del browser non disponibile: le scelte durano questa apertura.');
