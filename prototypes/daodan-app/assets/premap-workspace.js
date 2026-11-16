/* Current inventory is a UI composition, separate from the core pre-map contract. */
const PREMAP_RAW = JSON.parse(document.getElementById('premap-data').textContent);
const PREMAP = {
  source: {
    ...PREMAP_RAW.source,
    generatedAt: PREMAP_RAW.source.captured_at.slice(0, 16).replace('T', ' · ') + ' UTC',
  },
  files: PREMAP_RAW.files,
  languages: PREMAP_RAW.languages.map(l => ({ ...l, count: l.files })),
  technologies: PREMAP_RAW.technologies.map(t => ({ ...t, kind: t.category })),
  units: PREMAP_RAW.units.map(u => ({ ...u, path: u.root })),
  dependencies: PREMAP_RAW.units.flatMap(u => (u.dependencies || []).map(d => ({ ...d, kind: d.scope }))),
};

let repositoryError = '';
let repositoryBusy = false;
const PRIVATE_REPOSITORY_DEMO = {
  slug: 'organizzazione-demo/progetto-privato',
  visibility: 'private',
  branches: ['master', 'feature/demo'],
  defaultBranch: 'feature/demo',
  branchSource: 'demo',
};

function preferredBranch(branches, defaultBranch) {
  return branches.includes('main') ? 'main' : branches.includes('master') ? 'master' : defaultBranch;
}

function invalidateRepositoryRun() {
  state.progress = 0;
  state.runStatus = 'idle';
  state.logs = [];
  state.analysisStage = 'repository';
  state.treeSelected = '';
  state.treeSearch = '';
  state.treeOpen = {};
}

function setRepository(repository) {
  const nextBranch = preferredBranch(repository.branches, repository.defaultBranch);
  if (state.repository?.slug !== repository.slug || state.repository?.visibility !== repository.visibility || state.repositoryBranch !== nextBranch) invalidateRepositoryRun();
  state.repository = { ...repository };
  state.repositoryBranch = nextBranch;
  save();
}

function repositoryUsesLocalDataset() {
  return state.repository?.slug.toLowerCase() === 'acaprino/daodan' && state.repositoryBranch === 'main';
}

function repositoryContext() {
  const repo = state.repository;
  if (!repo) return '';
  return `<div class="repository-context"><div>${icon('code')}<strong>${esc(repo.slug)}</strong><span class="badge">${repo.visibility === 'private' ? 'Privata · demo' : 'Pubblica'}</span><span class="badge">${icon('branch')}${esc(state.repositoryBranch)}${repo.branchSource === 'demo' ? ' · demo' : ''}</span><span class="muted small">${state.mockGithubLogin ? 'Accesso GitHub simulato' : 'Accesso pubblico'}</span></div><p>Nessun checkout remoto eseguito. ${repositoryUsesLocalDataset() ? 'La pre-mappa usa il dataset locale della stessa origine Git; il grafo usa uno snapshot storico separato.' : 'La pre-mappa e il grafo mostrano solo dati esempio Daodan, non risultati di questa repository o branch.'}</p><button class="textbutton small" data-analysis-stage="repository">Cambia repository o branch ${icon('arrow')}</button></div>`;
}

function repositoryScreen() {
  const repo = state.repository;
  const privateMode = state.repositoryVisibility === 'private';
  const canContinue = repo && (!privateMode || state.mockGithubLogin);
  return `<div class="demo-source-note">${icon('info')}<div><strong>Connessione GitHub · demo offline</strong><p>Nessun account, token, richiesta API o checkout. L’accesso privato e i branch dimostrativi servono a provare il percorso della futura app.</p></div></div><div class="repository-layout"><section class="panel"><div class="panel-head"><h2>Repository GitHub</h2><span class="badge">Selezione del progetto</span></div><div class="panel-body"><div class="segmented repository-kind" aria-label="Visibilità della repository"><button data-repository-kind="public" aria-pressed="${!privateMode}">Pubblica</button><button data-repository-kind="private" aria-pressed="${privateMode}">Privata · demo</button></div>${privateMode ? `<div class="private-repo-demo"><span class="repo-mark">P</span><div><strong>Repository privata · demo</strong><code>${PRIVATE_REPOSITORY_DEMO.slug}</code><p>${state.mockGithubLogin ? 'Fixture dimostrativa accessibile con il login simulato.' : 'Simula l’accesso GitHub per selezionare questo esempio privato.'}</p></div></div>` : `<form id="repository-form" novalidate><div class="field"><label for="repository-url">URL GitHub pubblico</label><input id="repository-url" type="url" value="${esc(state.repositoryUrl)}" placeholder="https://github.com/proprietario/repository" aria-describedby="repository-url-help repository-error" ${repositoryError ? 'aria-invalid="true"' : ''}><p id="repository-url-help" class="muted small">Esempio reale: acaprino/daodan, origine del dataset locale. Gli altri URL vengono validati solo nella forma.</p><p id="repository-error" class="error-text" role="alert">${esc(repositoryError)}</p></div><button type="submit" id="verify-repository" ${repositoryBusy ? 'disabled' : ''}>${icon(repositoryBusy ? 'spinner' : 'check')}${repositoryBusy ? 'Verifica…' : 'Verifica URL · demo'}</button></form>`}
  <div class="repository-branch"><div class="field"><label for="repository-branch">Branch da analizzare</label><select id="repository-branch" ${!repo || !canContinue || repositoryBusy ? 'disabled' : ''}>${repo ? selectOptions(repo.branches.map(branch => [branch, branch + (repo.branchSource === 'demo' ? ' · demo' : ' · cache locale')]), state.repositoryBranch) : '<option>Seleziona prima una repository</option>'}</select></div><p class="muted small">Preferenza automatica: <code>main</code>, poi <code>master</code>, altrimenti il default dei metadati.</p>${repo ? `<p class="repository-branch-source">${repo.branchSource === 'cache' ? 'Rami realmente presenti nella cache Git locale, letta il 16/11/2026; nessuna verifica remota eseguita ora.' : 'Rami e default interamente dimostrativi. Il default reale richiederà i metadati API GitHub.'}</p>` : ''}</div><div class="repository-next"><p class="muted small">Un cambio di repository o branch azzera avanzamento e sintesi precedenti.</p><button class="primary" data-action="use-repository" id="use-repository" ${!canContinue || repositoryBusy ? 'disabled' : ''}>Apri pre-mappa ${icon('arrow')}</button></div></div></section>
  <aside class="stack"><section class="panel"><div class="panel-head"><h2>Accesso GitHub</h2>${icon('code')}</div><div class="panel-body"><span class="badge ${state.mockGithubLogin ? 'cyan' : ''}">${state.mockGithubLogin ? 'Accesso simulato attivo' : 'Non connesso'}</span><h3 style="margin-top:16px">${state.mockGithubLogin ? 'Profilo dimostrativo' : 'Pubblico, senza login'}</h3><p class="repository-auth-copy">${state.mockGithubLogin ? 'Puoi provare la selezione della repository privata di esempio. Non è collegato alcun account reale.' : 'Una repository pubblica è selezionabile con il suo URL. Per il percorso privato, prova il pulsante di accesso simulato.'}</p><button data-action="${state.mockGithubLogin ? 'mock-github-logout' : 'mock-github-login'}" id="mock-github-login" ${repositoryBusy ? 'disabled' : ''}>${icon(state.mockGithubLogin ? 'close' : 'play')}${state.mockGithubLogin ? 'Scollega accesso simulato' : 'Simula accesso GitHub'}</button></div></section><section class="panel"><div class="panel-head"><h2>Fonti distinte</h2></div><div class="panel-body"><ul class="repository-source-list"><li><strong>Selezione</strong><span>Repository e branch scelti in questa demo.</span></li><li><strong>Pre-mappa</strong><span>Inventario locale Daodan ${esc(PREMAP.source.commit)}, acquisito il 16/11/2026.</span></li><li><strong>Grafo</strong><span>Snapshot storico ${esc(SNAPSHOT.source.git.commit)}, usato solo come esempio di costruzione.</span></li></ul></div></section></aside></div>`;
}

async function verifyRepositoryUrl(button) {
  const value = state.repositoryUrl.trim();
  const normalized = value.startsWith('github.com/') ? 'https://' + value : value;
  const match = /^https:\/\/github\.com\/([A-Za-z0-9-]+)\/([A-Za-z0-9._-]+)\/?$/i.exec(normalized);
  const repoName = match?.[2].replace(/\.git$/, '');
  if (!match || !repoName || ['.', '..'].includes(repoName)) {
    repositoryError = value ? 'Usa un URL https://github.com/proprietario/repository, senza percorsi aggiuntivi.' : 'Inserisci l’URL GitHub della repository pubblica.';
    render();
    document.getElementById('repository-url').focus();
    return;
  }
  if (repositoryBusy) return;
  repositoryBusy = true;
  button.disabled = true;
  button.innerHTML = icon('spinner') + 'Verifica…';
  await new Promise(resolve => setTimeout(resolve, 550));
  if (state.repositoryUrl.trim() !== value || state.repositoryVisibility !== 'public') {
    repositoryBusy = false;
    render();
    return;
  }
  const slug = match[1] + '/' + repoName;
  const known = slug.toLowerCase() === 'acaprino/daodan';
  setRepository({ slug, visibility: 'public', branches: known ? ['main', 'engine-audit-20261113'] : ['sviluppo-demo', 'rilascio-demo'], defaultBranch: known ? 'main' : 'sviluppo-demo', branchSource: known ? 'cache' : 'demo' });
  repositoryError = '';
  repositoryBusy = false;
  render();
  toast('URL valido nella forma. Nessuna verifica remota eseguita.');
}

function analysisWorkspace() {
  const stage = state.analysisStage || 'repository';
  const titles = {
    repository: ['Da GitHub all’analisi', 'Scegli repository e branch.', 'Un repository pubblico o un accesso GitHub simulato per provare il percorso privato.'],
    premap: ['Prima dell’analisi', 'Conosci il punto di partenza.', 'Tecnologie dichiarate, file e unità tecniche: una vista del repository prima di interpretarne il comportamento.'],
    analysis: ['Pipeline di analisi', 'Il grafo prende forma.', 'Segui fasi, avanzamento ed eventi della simulazione.'],
    synthesis: ['Risultati della demo', 'Dalla mappa alla comprensione.', 'Componenti, responsabilità e lacune dello snapshot storico usato nella simulazione.'],
  };
  const [eyebrow, title, description] = titles[stage];
  const action = stage === 'repository' ? '' : stage === 'premap'
    ? `<button class="primary" data-action="new-run">${icon('play')}Avvia analisi demo</button>`
    : stage === 'synthesis'
      ? `<button class="primary" data-action="open-full-graph">${icon('graph')}Esplora il grafo completo</button>`
      : `<button data-action="new-run">${icon('plus')}Nuova demo</button>`;
  return heading(eyebrow, title, description, action) + analysisStageNav() +
    (stage === 'repository' ? repositoryScreen() : repositoryContext() + (stage === 'premap' ? premapScreen() : stage === 'synthesis' ? synthesisScreen() : analysisRunScreen()));
}

function analysisStageNav() {
  return `<nav class="analysis-journey" aria-label="Percorso di analisi">
    ${[['repository', 'Repository', 'GitHub e branch'], ['premap', 'Pre-mappa', 'Inventario e tecnologie'], ['analysis', 'Analisi', 'Pipeline e costruzione'], ['synthesis', 'Sintesi e grafo', 'Risultati e lacune']].map(([id, title, sub], i) => `
      <button data-analysis-stage="${id}" id="stage-${id}" ${state.analysisStage === id ? 'aria-current="step"' : ''} ${(id !== 'repository' && !state.repository) || (id === 'synthesis' && state.runStatus !== 'complete') ? 'disabled' : ''}>
        <span class="journey-number">${state.analysisStage === id ? icon(id === 'premap' ? 'layers' : id === 'analysis' ? 'analysis' : 'graph') : String(i + 1).padStart(2, '0')}</span>
        <span><strong>${title}</strong><small>${sub}</small></span>${i < 3 ? icon('chevron') : ''}
      </button>`).join('')}
  </nav>`;
}

function premapSourceLine() {
  return `<div class="source-strip"><span>${icon('branch')}<strong>Dataset locale Daodan · ${repositoryUsesLocalDataset() ? 'stessa origine, nessun checkout remoto' : 'esempio, non risultato del repository selezionato'}</strong><code>${esc(PREMAP.source.commit.slice(0, 12))}</code></span><span>${esc(PREMAP.source.generatedAt)} · preview dichiarativa da manifest</span><button class="textbutton small" data-action="premap-provenance">Provenienza ${icon('info')}</button></div>`;
}

function premapScreen() {
  const languages = PREMAP.languages;
  return premapSourceLine() + `<div class="premap-summary metrics">
    <div class="metric"><div class="value">${PREMAP.files.length.toLocaleString('it-IT')}</div><p>File del dataset locale</p><small>Inventario Daodan incorporato</small></div>
    <div class="metric"><div class="value">${languages.length}</div><p>Linguaggi rilevati</p><small>Dallo snapshot di Daodan</small></div>
    <div class="metric"><div class="value">${PREMAP.units.length}</div><p>Unità tecniche</p><small>Confermate dai manifest</small></div>
    <div class="metric"><div class="value">${PREMAP.dependencies.length}</div><p>Dichiarazioni di dipendenza</p><small>Manifest, non risoluzione</small></div>
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
      <section class="panel"><div class="panel-head"><h2>Linguaggi</h2><span class="badge">Inventario</span></div><div class="language-list">${languages.map(l => `<div class="language-row"><span><i style="background:${languageColor(l.name)}"></i>${esc(l.name)}</span><strong>${l.count.toLocaleString('it-IT')}<small> file</small></strong></div>`).join('')}</div><p class="aside-note">File della cartella plugins, come li classifica lo snapshot di Daodan.</p></section>
      <section class="panel"><div class="panel-head"><h2>Tecnologie e framework</h2><span class="badge">Riconosciuti</span></div><div class="technology-list">${PREMAP.technologies.map(t => `<div class="technology-row"><div><strong>${esc(t.name)}</strong><span class="badge">${esc(t.kind)}</span></div><p>${esc(t.note || t.version || 'Versione non dichiarata')}</p><code>${esc(t.source)}</code></div>`).join('') || '<p class="muted small" style="padding:16px">Nessuna tecnologia dichiarata nei manifest acquisiti.</p>'}</div></section>
    </aside>
  </div>
  <section class="panel dependency-panel" aria-labelledby="dependency-title"><div class="panel-head"><div><h2 id="dependency-title">Librerie prima dell’analisi</h2><p class="muted small">Dichiarazioni dei manifest, esposte dalla UI accanto alla pre-mappa.</p></div><span class="badge">Dipendenze dichiarate</span></div><div class="dependency-table-wrap"><table class="dependency-table"><thead><tr><th>Dipendenza</th><th>Versione dichiarata</th><th>Ruolo</th><th>Fonte</th></tr></thead><tbody>${PREMAP.dependencies.map(d => `<tr><td><strong>${esc(d.name)}</strong></td><td><code>${esc(d.version || 'Non separata nel manifest')}</code></td><td><span class="badge">${esc(d.kind)}</span></td><td><code>${esc(d.source)}</code></td></tr>`).join('')}</tbody></table></div><p class="aside-note">Le dipendenze di libreria sono fuori dal contratto della pre-mappa. Questa sezione legge i manifest: non dimostra che una libreria sia installata, risolta o chiamata. Gli strumenti che analizzano Vue/Svelte non provano che il repository usi quei framework.</p></section>`;
}

function languageColor(name) {
  const colors = { Python: '#64748b', TypeScript: '#a78bba', JavaScript: '#c9a65d', CSS: '#859eab', HTML: '#bd8c78' };
  return colors[name] || '#a1a1aa';
}

function directoryTree() {
  const query = state.treeSearch.trim().toLowerCase();
  const paths = PREMAP.files.filter(p => !query || p.toLowerCase().includes(query));
  if (!paths.length) return '<div class="empty"><p>Nessun percorso corrisponde alla ricerca.</p><button class="textbutton" data-action="clear-tree-search">Azzera ricerca</button></div>';
  const root = { children: {}, count: paths.length };
  for (const path of paths) {
    let node = root;
    const parts = path.split('/');
    parts.forEach((part, i) => {
      node.children[part] ||= { children: {}, count: 0, path: parts.slice(0, i + 1).join('/'), file: i === parts.length - 1 };
      node = node.children[part];
      node.count++;
    });
  }
  function draw(node, depth) {
    return Object.entries(node.children).sort(([a, x], [b, y]) => Number(x.file) - Number(y.file) || a.localeCompare(b, 'it')).map(([name, child]) => {
      const selected = state.treeSelected === child.path;
      if (child.file) return `<button class="tree-file ${selected ? 'selected' : ''}" data-tree-select="${esc(child.path)}" style="--depth:${depth}" ${selected ? 'aria-pressed="true"' : 'aria-pressed="false"'}>${icon('file')}<span>${esc(name)}</span></button>`;
      const id = 'directory:' + child.path;
      const open = query || state.treeOpen[id] || (depth === 0 && state.treeOpen[id] !== false);
      return `<details class="tree-directory" data-tree-id="${esc(id)}" ${open ? 'open' : ''}><summary style="--depth:${depth}"><span class="tree-caret">${icon('chevron')}</span>${icon('layers')}<span>${esc(name)}</span><small>${child.count}</small></summary><div>${draw(child, depth + 1)}</div></details>`;
    }).join('');
  }
  return `<div class="tree-root">${icon('code')}<strong>daodan</strong><span>${paths.length} file${query ? ' trovati' : ''}</span></div>${draw(root, 0)}`;
}

function technicalTree() {
  const query = state.treeSearch.trim().toLowerCase();
  const matched = PREMAP.units.filter(u => !query || [u.name, u.kind, u.path, u.manifest].join(' ').toLowerCase().includes(query));
  if (!matched.length) return '<div class="empty"><p>Nessuna unità tecnica corrisponde alla ricerca.</p><button class="textbutton" data-action="clear-tree-search">Azzera ricerca</button></div>';
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
      return `<details class="technical-unit" data-tree-id="${esc(id)}" ${query || state.treeOpen[id] || (parent === null && state.treeOpen[id] !== false) ? 'open' : ''}><summary><span class="tree-caret">${icon('chevron')}</span>${icon('code')}<span>${esc(u.name)}<small>${esc(u.kind)}</small></span><span class="badge">Confermata</span></summary><div class="unit-members"><button class="tree-file ${selected ? 'selected' : ''}" data-tree-select="${esc(id)}">${icon('info')}<span>Confine tecnico e fonte</span></button><button class="tree-file" data-tree-select="${esc(u.manifest)}">${icon('file')}<span>${esc(u.manifest)}</span></button><p><code>${esc(u.path || '.')}</code></p>${draw(u.id)}</div></details>`;
    }).join('');
  }
  return `<div class="tree-root">${icon('code')}<strong>Unità da manifest</strong><span>${PREMAP.units.length} confermate</span></div>${draw(null)}`;
}

function premapSelection() {
  const selected = state.treeSelected;
  if (!selected) return `<span class="muted">${icon('info')}Seleziona un file o apri un’unità per leggerne la provenienza.</span>`;
  if (selected.startsWith('unit:')) {
    const unit = PREMAP.units.find(u => 'unit:' + u.id === selected);
    if (unit) return `<p class="eyebrow">Unità tecnica confermata</p><h3>${esc(unit.name)}</h3><p>${esc(unit.kind)} · <code>${esc(unit.path || '.')}</code></p><code>${esc(unit.manifest)}</code><p class="muted">Il manifest ne conferma il confine tecnico. Non è una responsabilità semantica inferita.</p>`;
  }
  const extension = selected.includes('.') ? selected.split('.').pop() : 'senza estensione';
  return `<p class="eyebrow">File dell’inventario attuale</p><h3>${esc(selected.split('/').pop())}</h3><code>${esc(selected)}</code><p class="muted">Tipo: ${esc(extension)} · fonte: inventario Git ${esc(PREMAP.source.commit.slice(0, 12))}. Il contenuto non viene eseguito né analizzato dalla demo.</p>`;
}

const BUILD_ORDER = ['servizio-mcp', 'ricerca', 'lettore-delle-sorgenti', 'snapshot-e-inventario', 'indice-semantico', 'adattatori-dei-linguaggi', 'confinamento-del-progetto'];
function buildingGraphData(full = false) {
  const ordered = [...BUILD_ORDER, ...NODES.map(n => n.id).filter(id => !BUILD_ORDER.includes(id))].map(id => nodeById(id));
  const count = full ? ordered.length : state.progress < 20 ? 0 : Math.min(ordered.length, Math.max(1, Math.floor((state.progress - 18) / 82 * ordered.length)));
  const nodes = ordered.slice(0, count), ids = new Set(nodes.map(n => n.id));
  return { nodes, edges: EDGES.filter(e => ids.has(e.source) && ids.has(e.target)) };
}

function buildPreview(full = false) {
  const g = buildingGraphData(full);
  if (!g.nodes.length) return `<div class="build-empty">${icon('graph')}<h3>Prima l’inventario, poi le relazioni.</h3><p>I nodi della demo appariranno durante Analyze.<br>La visualizzazione usa uno snapshot storico, non una nuova scansione.</p></div>`;
  const width = 624, cols = 3, height = Math.max(300, Math.ceil(g.nodes.length / cols) * 92 + 46);
  const position = new Map(g.nodes.map((n, i) => [n.id, { x: 22 + (i % cols) * 201, y: 24 + Math.floor(i / cols) * 92 }]));
  return `<div class="build-world" style="width:${width}px;height:${height}px"><svg class="build-connections" width="${width}" height="${height}" aria-hidden="true">${g.edges.map(e => { const a = position.get(e.source), b = position.get(e.target); return `<path d="M${a.x + 88},${a.y + 59} C${a.x + 88},${a.y + 79} ${b.x + 88},${b.y - 20} ${b.x + 88},${b.y}"></path>`; }).join('')}</svg>${g.nodes.map(n => { const p = position.get(n.id); return `<button class="build-node" data-build-node="${n.id}" style="left:${p.x}px;top:${p.y}px">${icon(n.location === 'external' ? 'external' : 'layers')}<span>${esc(n.name)}<small>${n.files.length} file · ${n.location === 'external' ? 'esterno' : 'inferito'}</small></span></button>`; }).join('')}</div>`;
}

function runPhaseLabel() {
  return state.progress < 20 ? 'Scan · inventario e pre-mappa' : state.progress < 65 ? 'Analyze · tecnologie e collegamenti' : state.progress < 75 ? 'Dynamic · escluso dalla demo' : state.progress < 100 ? 'Union · unione dei grafi' : 'Pipeline completata · demo';
}

function analysisRunScreen() {
  const g = buildingGraphData();
  return `<div class="demo-source-note">${icon('info')}<div><strong>Costruzione dimostrativa, non una nuova analisi.</strong><p>Inventario iniziale: ${esc(PREMAP.source.commit.slice(0, 12))}. Grafo visualizzato: snapshot storico ${esc(SNAPSHOT.source.git.commit)}. Fonti e conteggi restano separati.</p></div></div>
  <div class="run-build-layout"><section class="panel" aria-labelledby="run-title"><div class="panel-body"><div class="run-status"><div><p class="eyebrow">Esecuzione dimostrativa</p><h2 id="run-title">${runPhaseLabel()}</h2><div class="row"><span class="badge ${state.runStatus === 'error' ? 'bad' : 'cyan'}" id="run-badge"><span class="dot"></span>${statusLabel()}</span></div></div><div class="progress-number"><span id="progress-value">${state.progress}</span><small>%</small></div></div><div class="progress" role="progressbar" aria-label="Avanzamento della demo" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${state.progress}" id="run-progress"><span id="progress-fill" style="width:${state.progress}%"></span></div><p class="run-help" id="run-help">Nessuna chiamata a modelli, analyzer o container.</p><div id="smooth-analysis-tasks"></div><div id="run-error" class="alert error" style="margin-top:16px" ${state.runStatus === 'error' ? '' : 'hidden'}><strong>Errore dimostrativo: indice non disponibile.</strong><br>Progresso e nodi già mostrati sono conservati. Riprova per riprendere.</div></div><div class="run-footer"><span class="muted">Repository: <code>${esc(state.repository.slug)}</code> · <code>${esc(state.repositoryBranch)}</code> · intero progetto</span><span id="run-button-wrap">${runButton()}</span></div></section>
  <section class="panel building-panel" aria-labelledby="building-title"><div class="panel-head"><div><h2 id="building-title">Costruzione del grafo</h2><p class="muted small">Nodi e archi dello snapshot appaiono progressivamente.</p></div><span class="badge orange">Demo</span></div><div class="build-viewport" id="build-viewport">${buildPreview()}</div><div class="build-foot"><span id="build-counts">${g.nodes.length} / ${NODES.length} nodi · ${g.edges.length} / ${EDGES.length} relazioni</span><span id="build-status">${state.runStatus === 'paused' ? 'Crescita in pausa' : state.runStatus === 'error' ? 'In attesa di ripristino' : state.runStatus === 'complete' ? 'Costruzione conclusa' : state.runStatus === 'idle' ? 'In attesa di avvio' : 'Costruzione simulata'}</span></div></section></div>
  <section class="panel run-activity" aria-labelledby="activity-title"><div class="panel-head"><h2 id="activity-title">Eventi e feedback</h2><button class="textbutton small" data-action="simulate-error" id="simulate-error" ${['complete', 'error', 'idle'].includes(state.runStatus) ? 'disabled' : ''}>${icon('warning')}Prova un errore</button></div><div class="logs" id="logs" aria-live="polite" aria-relevant="additions">${renderLogs()}</div></section>`;
}

function synthesisScreen() {
  return `<div class="demo-source-note">${icon('info')}<div><strong>Sintesi illustrata dallo snapshot storico ${esc(SNAPSHOT.source.git.commit)}.</strong><p>Le responsabilità qui sotto erano già inferite nello snapshot. Non sono nuove conclusioni sull’inventario attuale.</p></div></div><div class="metrics"><div class="metric"><div class="value">${NODES.length}</div><p>Componenti inferiti</p><small>Da confermare</small></div><div class="metric"><div class="value">${EDGES.length}</div><p>Relazioni statiche</p><small>Non tracce runtime</small></div><div class="metric"><div class="value">${SNAPSHOT.source.files}</div><p>File nello snapshot storico</p><small>Fonte distinta dalla pre-mappa</small></div><div class="metric"><div class="value">${SNAPSHOT.unassigned.count}</div><p>File senza componente</p><small>Lacuna esplicita dello snapshot</small></div></div>
  <div class="synthesis-layout"><section class="panel"><div class="panel-head"><h2>Responsabilità da esplorare</h2><span class="badge">Inferite</span></div><div class="synthesis-components">${['servizio-mcp', 'ricerca', 'lettore-delle-sorgenti'].map(id => { const n = nodeById(id); return `<button data-preview-node="${n.id}"><span class="synthesis-icon">${icon('layers')}</span><span><strong>${esc(n.name)}</strong><p>${esc(n.responsibility)}</p><small>${n.files.length} file · proposta nello snapshot</small></span>${icon('arrow')}</button>`; }).join('')}</div></section><aside class="stack"><section class="panel"><div class="panel-head"><h2>Dipendenze dopo l’analisi</h2></div><div class="panel-body"><span class="badge orange">Risoluzione non disponibile</span><p class="synthesis-note">La demo conserva le librerie dichiarate nei manifest. Lo snapshot storico espone riferimenti statici, ma non prova quali versioni delle librerie siano installate o risolte.</p></div></section><section class="panel"><div class="panel-head"><h2>Cosa manca al quadro</h2></div><div class="panel-body"><ul class="synthesis-gaps"><li>${SNAPSHOT.unassigned.count} file non assegnati a componenti nello snapshot.</li><li>Nessuna traccia runtime acquisita da questa demo.</li><li>Copertura dei riferimenti non misurabile: manca il denominatore risolvibile.</li><li>${esc(SNAPSHOT.absent.physical)}</li></ul><button class="textbutton" data-action="snapshot">${icon('file')}Provenienza e lacune</button></div></section></aside></div>`;
}

function updateAnalysisRun() {
  const stageButton = document.getElementById('stage-synthesis');
  if (stageButton) stageButton.disabled = state.runStatus !== 'complete';
  if (state.screen !== 'analysis' || state.analysisStage !== 'analysis') return;
  document.getElementById('run-title').textContent = runPhaseLabel();
  document.getElementById('progress-value').textContent = state.progress;
  document.getElementById('progress-fill').style.width = state.progress + '%';
  document.getElementById('run-progress').setAttribute('aria-valuenow', state.progress);
  const badge = document.getElementById('run-badge');
  badge.className = 'badge ' + (state.runStatus === 'error' ? 'bad' : 'cyan');
  badge.innerHTML = '<span class="dot"></span>' + statusLabel();
  window.DaodanSmoothUI?.mount(state);
  const hadFocus = document.activeElement?.id === 'run-toggle';
  document.getElementById('run-button-wrap').innerHTML = runButton();
  if (hadFocus) document.getElementById('run-toggle').focus({ preventScroll: true });
  document.getElementById('simulate-error').disabled = ['error', 'complete', 'idle'].includes(state.runStatus) || runLoading;
  document.getElementById('run-error').hidden = state.runStatus !== 'error';
  document.getElementById('logs').innerHTML = renderLogs();
  const viewport = document.getElementById('build-viewport');
  const lastCount = viewport.dataset.nodeCount;
  const g = buildingGraphData();
  if (lastCount !== String(g.nodes.length)) {
    const scrollLeft = viewport.scrollLeft, scrollTop = viewport.scrollTop;
    viewport.innerHTML = buildPreview();
    viewport.dataset.nodeCount = g.nodes.length;
    viewport.scrollLeft = scrollLeft;
    viewport.scrollTop = scrollTop;
  }
  document.getElementById('build-counts').textContent = `${g.nodes.length} / ${NODES.length} nodi · ${g.edges.length} / ${EDGES.length} relazioni`;
  document.getElementById('build-status').textContent = state.runStatus === 'paused' ? 'Crescita in pausa' : state.runStatus === 'error' ? 'In attesa di ripristino' : state.runStatus === 'complete' ? 'Costruzione conclusa' : 'Costruzione simulata';
  document.getElementById('run-help').textContent = state.runStatus === 'complete' ? 'Demo completata. La sintesi è pronta da leggere.' : 'Nessuna chiamata a modelli, analyzer o container.';
}

document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if (button.dataset.analysisStage) {
    state.analysisStage = button.dataset.analysisStage;
    render();
    return;
  }
  if (button.dataset.treeMode) {
    state.treeMode = button.dataset.treeMode;
    render();
    return;
  }
  if (button.dataset.treeSelect) {
    state.treeSelected = button.dataset.treeSelect;
    document.querySelectorAll('[data-tree-select]').forEach(b => {
      const selected = b.dataset.treeSelect === state.treeSelected;
      b.classList.toggle('selected', selected);
      b.setAttribute('aria-pressed', String(selected));
    });
    document.getElementById('tree-selection').innerHTML = premapSelection();
    save();
    return;
  }
  if (button.dataset.buildNode) {
    const n = nodeById(button.dataset.buildNode);
    modal(esc(n.name), 'Componente inferito nello snapshot storico, non risultato di questa esecuzione.', `<p>${esc(n.responsibility || n.description)}</p><p class="muted small" style="margin-top:16px">${n.files.length} file · snapshot ${esc(SNAPSHOT.source.git.commit)}</p>`, `<button class="primary" data-action="close-modal">Chiudi dettaglio</button>`);
    return;
  }
  if (button.dataset.action === 'open-full-graph') {
    state.graphDepth = 'all';
    state.graphSearch = '';
    state.graphMode = 'structure';
    navigate('graph');
  }
  if (button.dataset.action === 'clear-tree-search') {
    state.treeSearch = '';
    render();
  }
  if (button.dataset.action === 'premap-provenance') {
    modal('Provenienza della pre-mappa UI', 'Inventario e manifesti attuali, senza esecuzione della pipeline.', `<p>${esc(PREMAP.source.notice)}</p><dl class="facts"><dt>Commit</dt><dd><code>${esc(PREMAP.source.commit)}</code></dd><dt>Acquisito</dt><dd>${esc(PREMAP.source.generatedAt)}</dd><dt>File Git</dt><dd>${PREMAP.files.length.toLocaleString('it-IT')}</dd><dt>Unità da manifest</dt><dd>${PREMAP.units.length}</dd><dt>Dichiarazioni di dipendenza</dt><dd>${PREMAP.dependencies.length}</dd></dl><ul class="checked-list">${PREMAP_RAW.gaps.map(gap => `<li>${icon('info')}<span>${esc(gap)}</span></li>`).join('')}</ul><p class="muted small" style="margin-top:16px">Fonte incorporata: <code>assets/premap-preview.json</code>. Il contratto canonico della pre-mappa non viene modificato.</p>`, `<button class="primary" data-action="close-modal">Chiudi provenienza</button>`);
  }
});

document.addEventListener('input', event => {
  if (event.target.id === 'premap-search') {
    state.treeSearch = event.target.value;
    render();
  }
});

document.addEventListener('toggle', event => {
  if (event.target.dataset.treeId && document.contains(event.target)) {
    state.treeOpen[event.target.dataset.treeId] = event.target.open;
    save();
  }
}, true);

const HISTORICAL_REVIEW_FOCUS = 'Verifica la modifica di compute_total nel commit 109c1d7 e i suoi effetti sul checkout.';

function reviewScopePanel() {
  return `<section class="panel review-scope-panel" aria-labelledby="review-scope-title"><div class="panel-head"><div><h2 id="review-scope-title">Contesto e perimetro della review</h2><p class="muted small">L’obiettivo è facoltativo e appartiene alla review. Nessuna nuova review viene avviata.</p></div><span class="badge">Contesto</span></div><div class="panel-body"><div class="review-focus-row"><div class="field"><label for="review-focus">Obiettivo della review <span class="muted">(facoltativo)</span></label><textarea id="review-focus" aria-describedby="review-focus-help" placeholder="Quale cambiamento o comportamento vuoi verificare?">${esc(state.reviewFocus)}</textarea><p id="review-focus-help" class="muted small">Il motore, quando collegato, proporrà moduli, funzioni/simboli e file/cartelle da verificare.</p></div><div class="review-focus-actions"><button data-action="use-historical-review-focus">${icon('file')}Usa esempio storico</button><button class="quiet" data-action="clear-review-focus">Svuota obiettivo</button></div></div><div id="review-scope-preview" aria-live="polite">${reviewScopeContent()}</div></div></section>`;
}

function reviewScopeContent() {
  const focus = (state.reviewFocus || '').trim();
  if (focus && focus !== HISTORICAL_REVIEW_FOCUS) {
    return `<div class="review-scope-heading"><span class="badge orange">Perimetro da calcolare</span><p>Il motore non è collegato. Questo testo resta una bozza: non viene applicato il perimetro dell’esempio storico.</p></div><div class="review-scope-grid">${[['Moduli', 'Da inferire e verificare.'], ['Funzioni / simboli', 'Da individuare in base al contesto.'], ['File / cartelle', 'Da proporre con evidenze del repository.']].map(([title, copy]) => `<div><h3>${title}</h3><p class="muted">${copy}</p></div>`).join('')}</div><p class="review-scope-source">Il finding e la spiegazione sotto restano quelli del report storico 109c1d7. Nessuna nuova analisi o review eseguita.</p>`;
  }
  return `<div class="review-scope-heading"><span class="badge">Perimetro storico documentato</span><p>${focus ? 'Esempio selezionato: ambito già descritto dal report, non inferito ora dal testo.' : 'Nessun obiettivo impostato. Mostriamo il contesto del report storico già disponibile.'}</p></div><div class="review-scope-grid"><div><h3>Moduli</h3><strong>orders</strong><p>Unità tecnica del benchmark. Ambito di contesto proposto dalla UI; le conclusioni del report restano su <code>pricing.py</code>.</p></div><div><h3>Funzioni / simboli</h3><ul><li><code>compute_total</code>: riga modificata</li><li><code>compute_discount</code>: regola dello sconto</li><li><code>OrderService.checkout</code>: unico chiamante trovato</li><li><code>ledger.record</code>: importo persistito</li></ul></div><div><h3>File / cartelle</h3><p><code>app/packages/orders/</code></p><ul><li><code>pricing.py:19</code>: conclusioni</li><li><code>service.py:26</code>: lettura a un salto</li><li><code>test_app_structures.py</code> e <code>app/pyproject.toml</code>: letti nel report</li></ul></div></div><p class="review-scope-source">Fonte verificabile: <code>${esc(REPORT.source_report)}</code>, sezioni «Target and basis» e «Findings and verification». Perimetro proposto da confermare, non una nuova inferenza del prototipo.</p>`;
}

document.addEventListener('input', event => {
  if (event.target.id === 'review-focus') {
    state.reviewFocus = event.target.value;
    save();
    document.getElementById('review-scope-preview').innerHTML = reviewScopeContent();
  }
});

document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button || !['use-historical-review-focus', 'clear-review-focus'].includes(button.dataset.action)) return;
  state.reviewFocus = button.dataset.action === 'use-historical-review-focus' ? HISTORICAL_REVIEW_FOCUS : '';
  document.getElementById('review-focus').value = state.reviewFocus;
  document.getElementById('review-scope-preview').innerHTML = reviewScopeContent();
  save();
});

document.addEventListener('submit', async event => {
  if (event.target.id !== 'repository-form') return;
  event.preventDefault();
  await verifyRepositoryUrl(document.getElementById('verify-repository'));
});

document.addEventListener('input', event => {
  if (event.target.id !== 'repository-url') return;
  state.repositoryUrl = event.target.value;
  repositoryError = '';
  if (state.repository) {
    state.repository = null;
    state.repositoryBranch = '';
    invalidateRepositoryRun();
    const branch = document.getElementById('repository-branch');
    branch.disabled = true;
    branch.innerHTML = '<option>Seleziona prima una repository</option>';
    document.getElementById('use-repository').disabled = true;
    document.querySelectorAll('[data-analysis-stage]').forEach(b => b.disabled = b.dataset.analysisStage !== 'repository');
  }
  event.target.removeAttribute('aria-invalid');
  document.getElementById('repository-error').textContent = '';
  save();
});

document.addEventListener('change', event => {
  if (event.target.id !== 'repository-branch') return;
  if (state.repositoryBranch !== event.target.value) invalidateRepositoryRun();
  state.repositoryBranch = event.target.value;
  save();
  render();
  toast('Branch cambiato. Avanzamento e sintesi precedenti azzerati.');
});

document.addEventListener('click', async event => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if (button.dataset.repositoryKind) {
    if (state.repositoryVisibility === button.dataset.repositoryKind) return;
    state.repositoryVisibility = button.dataset.repositoryKind;
    state.repository = null;
    state.repositoryBranch = '';
    repositoryError = '';
    invalidateRepositoryRun();
    if (state.repositoryVisibility === 'private' && state.mockGithubLogin) setRepository(PRIVATE_REPOSITORY_DEMO);
    render();
    return;
  }
  if (button.dataset.action === 'mock-github-login') {
    if (repositoryBusy) return;
    repositoryBusy = true;
    button.disabled = true;
    button.innerHTML = icon('spinner') + 'Accesso simulato…';
    await new Promise(resolve => setTimeout(resolve, 600));
    state.mockGithubLogin = true;
    repositoryBusy = false;
    if (state.repositoryVisibility === 'private') setRepository(PRIVATE_REPOSITORY_DEMO);
    render();
    toast('Accesso GitHub simulato. Nessun account o token collegato.');
  }
  if (button.dataset.action === 'mock-github-logout') {
    state.mockGithubLogin = false;
    if (state.repository?.visibility === 'private') {
      state.repository = null;
      state.repositoryBranch = '';
      invalidateRepositoryRun();
    }
    render();
    toast('Accesso simulato scollegato.');
  }
  if (button.dataset.action === 'use-repository') {
    if (!state.repository || (state.repository.visibility === 'private' && !state.mockGithubLogin)) return;
    button.disabled = true;
    button.innerHTML = icon('spinner') + 'Preparazione anteprima…';
    await new Promise(resolve => setTimeout(resolve, 450));
    if (!state.repository || (state.repository.visibility === 'private' && !state.mockGithubLogin)) {
      state.analysisStage = 'repository';
      render();
      return;
    }
    state.analysisStage = 'premap';
    render();
    window.scrollTo({ top: 0, behavior: 'instant' });
    toast('Contesto selezionato: ' + state.repository.slug + ' · ' + state.repositoryBranch);
  }
});
