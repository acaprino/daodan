import React, { useLayoutEffect, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { graphView } from '@acaprino/imago/graph';
import { roving } from '@acaprino/imago/ui';
import type { GraphScene } from '@acaprino/imago/graph';
import { graphControls } from './appearance';
import { ArrowLeft, ChevronRight, FolderOpen, Route, Search, X } from 'lucide-react';
import './style.css';
import { getJson, POLL_MS, Session } from './session';
import { parseEnvelope } from './envelope.ts';
import type { Entity, Envelope, Flow } from './envelope.ts';
import { childrenOf, dataLinks, flowFocus, flowsThrough, indexOf, project } from './projection.ts';
import type { ProjectedEdge, ProjectedNode } from './projection.ts';
import { initialState, reduce } from './state.ts';
import type { Action, ExplorerState } from './state.ts';
import { createLayoutClient, LayoutError } from './layoutClient.ts';
import type { Layout } from './layoutClient.ts';
import { ENTRY_LABEL, FRESHNESS_LABEL, iconFor, LINK_LABEL, STATUS_LABEL, TYPE_LABEL } from './icons.ts';

const SIZE = { width: 224, height: 64 };

const join = (...names: (string | false | null | undefined)[]) => names.filter(Boolean).join(' ');


function nodeMeta(node: ProjectedNode): string {
  return [
    node.nodeType ?? TYPE_LABEL[node.type] ?? node.type,
    node.location === 'external' ? 'esterno' : null,
    node.status && node.status !== 'confirmed' ? STATUS_LABEL[node.status] ?? node.status : null,
    node.freshness && !['fresh', 'uncovered'].includes(node.freshness) ? 'scheda da rileggere' : null,
  ].filter(Boolean).join(' · ');
}

function Diagram({ scene, layoutKey, onSelect, onOpen, onClear }: {
  scene: GraphScene; layoutKey: string; onSelect: (id: string) => void; onOpen: (id: string) => void; onClear: () => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const controller = useRef<ReturnType<typeof graphView> | null>(null);
  const actions = useRef({ onSelect, onOpen, onClear });
  const previous = useRef('');
  useLayoutEffect(() => {
    actions.current = { onSelect, onOpen, onClear };
  }, [onSelect, onOpen, onClear]);
  useLayoutEffect(() => {
    controller.current = graphView(host.current!, { label: 'Naviga il grafo', controls: graphControls,
      onSelect: id => actions.current.onSelect(id), onOpen: id => actions.current.onOpen(id), onClear: () => actions.current.onClear() });
    return () => { controller.current?.dispose(); controller.current = null; };
  }, []);
  useLayoutEffect(() => {
    controller.current?.draw(scene, previous.current !== layoutKey);
    previous.current = layoutKey;
  }, [scene, layoutKey]);
  return <div ref={host} className="diagram-host" />;
}

function entityName(envelope: Envelope, ref: string): string {
  return indexOf(envelope).byRef.get(ref)?.name ?? ref;
}

// The technologies of the project, or those of one build unit (`ids`); each names the files that show it.
function Technologies({ envelope, ids }: { envelope: Envelope; ids?: string[] }) {
  const shown = envelope.technologies.filter(item => !ids || ids.includes(item.id));
  if (!shown.length) return null;
  return <div className="block"><h3>Tecnologie</h3><ul className="links">{shown.map(item =>
    <li key={item.id} title={item.paths.join('\n')}>{item.name} <span className="muted">{item.type}</span></li>)}</ul></div>;
}

function Inspector({ state, dispatch, edges }: { state: ExplorerState; dispatch: (action: Action) => void; edges: ProjectedEdge[] }) {
  const envelope = state.envelope;
  const entity: Entity | undefined = state.selected ? indexOf(envelope).byRef.get(state.selected) : undefined;
  if (!entity) {
    const meta = envelope.meta as Record<string, unknown>;
    return <section className="inspector" aria-live="polite">
      <p className="eyebrow">Come leggere la mappa</p>
      <h2>{String(meta.project_root ?? 'Progetto').split(/[\\/]/).filter(Boolean).pop()}</h2>
      <p>Seleziona un nodo per vederne il ruolo, i collegamenti e i flussi che lo attraversano. Doppio clic su un nodo con un numero per entrarci.</p>
      <ul className="facts">
        <li>{envelope.entities.length} entità, {envelope.relations.length} relazioni</li>
        <li>{envelope.flows.length} flussi dai punti d'ingresso</li>
        <li>{envelope.gaps.length} lacune dichiarate</li>
      </ul>
      <p className="muted">Collegamenti e flussi sono statici: dicono cosa il codice rende possibile, non cosa accade in esecuzione.</p>
      <Technologies envelope={envelope} />
    </section>;
  }
  const Icon = iconFor({ nodeType: entity.node_type, type: entity.type });
  const flows = flowsThrough(envelope, entity.ref, state.view);
  const canOpen = entity.type !== 'feature' && childrenOf(envelope, entity.ref, state.view).length > 0;
  const gaps = envelope.gaps.filter(gap => gap.refs.includes(entity.ref));
  const lines = Array.isArray(entity.lines) ? entity.lines.filter(Boolean).join('–') : entity.lines;
  const related = edges.filter(edge => edge.source.startsWith(`${entity.ref}@`) || edge.target.startsWith(`${entity.ref}@`));
  return <section className="inspector" aria-live="polite">
    <p className="eyebrow"><Icon size={14} aria-hidden="true" /> {entity.node_type ?? TYPE_LABEL[entity.type] ?? entity.type} · {entity.location === 'external' ? 'esterno' : 'interno'}</p>
    <h2>{entity.name}</h2>
    {entity.path && <code className="path">{entity.path}{lines ? `:${lines}` : ''}</code>}
    {entity.description && <p>{entity.description}</p>}
    <ul className="facts">
      {entity.provenance && <li>Provenienza: {entity.provenance}</li>}
      {entity.status && <li>Stato: {STATUS_LABEL[entity.status] ?? entity.status}</li>}
      {entity.freshness && <li>{FRESHNESS_LABEL[entity.freshness] ?? entity.freshness}</li>}
    </ul>
    {canOpen && <button type="button" className="im-btn im-btn--primary" onClick={() => dispatch({ type: 'open', ref: entity.ref })}><FolderOpen size={15} />Entra in {entity.name}</button>}
    {entity.technologies && <Technologies envelope={envelope} ids={entity.technologies} />}
    {flows.length > 0 && <div className="block"><h3>Flussi che lo attraversano</h3>{flows.map(flow =>
      <button type="button" key={flow.ref} className={join('im-btn im-btn--sm', state.flow === flow.ref && 'on')} onClick={() => dispatch({ type: 'flow', ref: flow.ref })}>
        <Route size={12} />{entityName(envelope, flow.entry)}</button>)}</div>}
    {related.length > 0 && <div className="block"><h3>Collegamenti visibili</h3><ul className="links">{related.slice(0, 20).map(edge => {
      const outgoing = edge.source.startsWith(`${entity.ref}@`);
      const other = (outgoing ? edge.target : edge.source).split('@')[0];
      return <li key={edge.id}>{outgoing ? '→' : '←'} {entityName(envelope, other)} <span className="muted">{edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ')}</span></li>;
    })}</ul></div>}
    {entity.evidence.length > 0 && <div className="block"><h3>Evidenze</h3><ul className="links">{entity.evidence.slice(0, 8).map((item, index) =>
      <li key={index}><code>{item.path}{item.line ? `:${item.line}` : ''}</code></li>)}</ul></div>}
    {gaps.length > 0 && <div className="block warn"><h3>Lacune</h3>{gaps.map((gap, index) => <p key={index}>{gap.reason}</p>)}</div>}
  </section>;
}

function FlowPanel({ state, dispatch }: { state: ExplorerState; dispatch: (action: Action) => void }) {
  const envelope = state.envelope;
  if (!envelope.flows.length) return <p className="muted">Nessun flusso: questo run non ha regole di collegamento (<code>codebase_map_flows</code>).</p>;
  const current: Flow | undefined = envelope.flows.find(flow => flow.ref === state.flow);
  return <>
    <ul className="flow-list">{envelope.flows.map(flow =>
      <li key={flow.ref}><button type="button" className="im-row flow-item" aria-pressed={state.flow === flow.ref}
        onClick={() => dispatch({ type: 'flow', ref: state.flow === flow.ref ? null : flow.ref })}>
        <span className="flow-name">{entityName(envelope, flow.entry)}</span>
        <span className="muted">{ENTRY_LABEL[flow.entry_kind] ?? flow.entry_kind} · {flow.steps.length} passi{flow.complete ? '' : ' · incompleto'}</span>
      </button></li>)}</ul>
    {current && <ol className="steps">{current.steps.slice(0, 40).map((step, index) =>
      <li key={index}><span>{entityName(envelope, step.source)} <strong>{LINK_LABEL[step.type] ?? step.type}</strong> {entityName(envelope, step.target)}</span>
        <code>{step.route ? `${step.route.slice(1).join(' ')} · ` : ''}{step.site}</code></li>)}</ol>}
  </>;
}

// A finding names a project-relative file; the envelope's refs are relative to the run's target.
function fileRef(envelope: Envelope, file: string): string | null {
  const target = String(envelope.meta.target ?? '.').replace(/\/+$/, '');
  if (target === '.' || target === '') return `file:${file}`;
  return file.startsWith(`${target}/`) ? `file:${file.slice(target.length + 1)}` : null;
}

function Explorer({ envelope, pick }: { envelope: Envelope; pick?: { file: string } | null }) {
  const [state, dispatch] = useReducer(reduce, envelope, initialState);
  const tabs = useRef<HTMLDivElement>(null);
  useEffect(() => roving(tabs.current!, {
    item: '[role="tab"]', orientation: 'horizontal', onSelect: tab => tab.click(),
  }), []);
  const shown = useRef(envelope);
  useEffect(() => {
    if (envelope !== shown.current) { shown.current = envelope; dispatch({ type: 'replaceEnvelope', json: envelope }); }
  }, [envelope]);
  useEffect(() => {
    const ref = pick && fileRef(envelope, pick.file);
    if (ref) dispatch({ type: 'select', ref });
  }, [pick]);
  const [layout, setLayout] = useState<{ key: string; value: Layout } | null>(null);
  const [error, setError] = useState('');
  const [vertical, setVertical] = useState(() => window.matchMedia('(max-width: 899px)').matches);
  const client = useRef<ReturnType<typeof createLayoutClient> | null>(null);
  const projection = useMemo(() => project(state.envelope, state.view, state.scope, state.filters, state.open, state.selected),
    [state.envelope, state.view, state.scope, state.filters, state.open, state.selected]);
  const focus = useMemo(() => (state.flow ? flowFocus(state.envelope, state.flow, projection) : null), [state.flow, projection]);
  const data = useMemo(() => (focus ? [] : dataLinks(state.envelope, projection)), [focus, projection]);
  const edges = useMemo(() => [...projection.edges, ...data, ...(focus?.edges ?? [])], [projection, data, focus]);
  const direction = vertical ? 'DOWN' : 'RIGHT';
  const key = `${direction}|${projection.nodes.map(node => node.id).join(',')}|${edges.map(edge => edge.id).join(',')}`;

  useEffect(() => {
    const media = window.matchMedia('(max-width: 899px)');
    const changed = (event: MediaQueryListEvent) => setVertical(event.matches);
    media.addEventListener('change', changed);
    client.current = createLayoutClient(() => new Worker(new URL('./layout.worker.ts', import.meta.url), { type: 'module' }) as never);
    return () => { media.removeEventListener('change', changed); client.current?.dispose(); };
  }, []);

  useEffect(() => {
    if (!client.current) return;
    setError('');
    const graph = { nodes: projection.nodes.map(node => ({ id: node.id, ...SIZE })), edges: edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target })) };
    client.current.request(graph, direction).then(value => setLayout({ key, value })).catch(reason => {
      if (!(reason instanceof LayoutError && reason.reason === 'superseded')) setError(String(reason?.message ?? reason));
    });
  }, [key]);


  const selectedIds = new Set(state.selected ? projection.owners[state.selected] ?? [] : []);
  const neighbours = new Set(projection.edges.filter(edge => selectedIds.has(edge.source) || selectedIds.has(edge.target)).flatMap(edge => [edge.source, edge.target]));
  const flowNodes = new Set(focus?.nodes ?? []);
  const busy = !layout || layout.key !== key;
  const select = (ref: string) => dispatch({ type: 'select', ref });
  const open = (ref: string) => dispatch({ type: 'open', ref });
  const byId = new Map(projection.nodes.map(node => [node.id, node]));
  const scene: GraphScene = {
    nodes: busy ? [] : projection.nodes.map(node => ({
      ...SIZE, ...layout!.value.nodes[node.id], id: node.id, label: node.label, detail: nodeMeta(node),
      selected: selectedIds.has(node.id), highlighted: flowNodes.has(node.id), external: node.location === 'external',
      dimmed: focus ? !flowNodes.has(node.id) : selectedIds.size > 0 && !neighbours.has(node.id) && !selectedIds.has(node.id),
      count: node.collapsed ? node.count : undefined, openLabel: node.collapsed ? 'Apri ' + node.label : undefined,
    })),
    edges: busy ? [] : edges.map(edge => {
      const active = selectedIds.has(edge.source) || selectedIds.has(edge.target);
      return { source: edge.source, target: edge.target, points: layout!.value.edges[edge.id],
        label: edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', '), showLabel: !!edge.flow || active,
        dashed: edge.id.startsWith('data:'), tone: edge.flow ? 'warn' : active ? 'accent' : undefined,
        dimmed: focus ? !edge.flow : selectedIds.size > 0 && !active };
    }),
  };

  const index = indexOf(state.envelope);
  const scopeName = state.scope ? index.byRef.get(state.scope)?.name ?? state.scope : null;
  const types = [...new Set(projection.nodes.map(node => node.type))].sort();
  const filtered = projection.counts.filtered;
  const meta = state.envelope.meta as Record<string, unknown>;
  const project_name = String(meta.project_root ?? '').split(/[\\/]/).filter(Boolean).pop() ?? '';
  const openFile = async (file: File | undefined) => {
    if (!file) return;
    try { dispatch({ type: 'replaceEnvelope', json: JSON.parse(await file.text()) }); }
    catch (reason) { dispatch({ type: 'replaceEnvelope', json: { error: String(reason) } }); }
  };

  return <div className="app">
    <header className="topbar">
      <strong>Codebase Map</strong>
      <span className="muted">{project_name}{meta.target && meta.target !== '.' ? ` / ${String(meta.target)}` : ''} · run {String(meta.run_id ?? '')}</span>
      <label className="open-export">Apri altro export<input className="im-file-selector" type="file" accept=".json,application/json" onChange={event => openFile(event.target.files?.[0])} /></label>
    </header>
    {(state.error || state.warning) && <p className={join('notice', state.error && 'bad')} role="status">{state.error ?? state.warning}</p>}
    <div className="toolbar">
      <div className="im-tabs" ref={tabs} role="tablist" aria-label="Vista">
        {(['logical', 'physical'] as const).map(view => <button key={view} type="button" role="tab" aria-selected={state.view === view}
          className="im-tab" onClick={() => dispatch({ type: 'view', view })}>{view === 'logical' ? 'Logica' : 'Fisica'}</button>)}
      </div>
      <nav className="crumbs" aria-label="Posizione">
        <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'root' })}>Sistema</button>
        {scopeName && <><ChevronRight size={13} aria-hidden="true" /><span aria-current="page">{scopeName}</span>
          <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'up' })}><ArrowLeft size={13} />Su</button></>}
      </nav>
      <label className="im-input"><Search size={14} aria-hidden="true" /><input type="search" placeholder="Cerca per nome" value={state.filters.text ?? ''}
        onChange={event => dispatch({ type: 'filter', filters: { text: event.target.value } })} aria-label="Cerca per nome" /></label>
      <select className="im-select" aria-label="Tipo di entità" value={state.filters.types?.[0] ?? ''} onChange={event => dispatch({ type: 'filter', filters: { types: event.target.value ? [event.target.value] : [] } })}>
        <option value="">Tutti i tipi</option>{types.map(type => <option key={type} value={type}>{TYPE_LABEL[type] ?? type}</option>)}
      </select>
      {filtered > 0 && <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'resetFilters' })}><X size={13} />Azzera filtri ({filtered} nascosti)</button>}
    </div>
    <main className="workspace">
      <aside className="navigator">
        <h3>Flussi</h3>
        <FlowPanel state={state} dispatch={dispatch} />
        <h3>Elementi visibili</h3>
        <ul className="element-list">{projection.nodes.map(node => {
          const Icon = iconFor(node);
          return <li key={node.id}><button type="button" className="im-row element" aria-pressed={selectedIds.has(node.id)} onClick={() => select(node.ref)}
            onDoubleClick={() => node.collapsed && dispatch({ type: 'open', ref: node.ref })}><Icon size={14} aria-hidden="true" />{node.label}
            <span className="muted">{nodeMeta(node)}</span></button></li>;
        })}</ul>
      </aside>
      <section className="canvas" aria-label="Grafo">
        <Diagram scene={scene} layoutKey={busy ? '' : key}
          onSelect={id => { const n = byId.get(id); if (n) select(n.ref); }}
          onOpen={id => { const n = byId.get(id); if (n?.collapsed) open(n.ref); }}
          onClear={() => dispatch({ type: 'select', ref: null })} />
        {busy && !error && projection.nodes.length > 0 && <div className="canvas-state" role="status"><span className="im-spinner" aria-hidden="true" /> Dispongo il grafo…</div>}
        {!projection.nodes.length && <div className="canvas-state" role="status">Nessun elemento visibile.{filtered > 0 && <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'resetFilters' })}>Azzera filtri</button>}</div>}
        {error && <div className="canvas-state bad" role="alert">Impossibile disporre il grafo: {error}</div>}
        <p className="canvas-foot">{projection.nodes.length} nodi · {projection.edges.length} relazioni · {data.length} collegamenti di dati (tratteggiati) · {projection.counts.aggregated} dentro i gruppi{focus ? ` · flusso su ${focus.nodes.length} nodi` : ''}</p>
      </section>
      <Inspector state={state} dispatch={dispatch} edges={projection.edges} />
    </main>
  </div>;
}

type LiveEvent = { cursor: number; timestamp: string; event: string; message: string; phase?: number };
// Served by the MCP server the page lists the runs and follows the chosen run's events; served from an export it draws that file.
function App() {
  const [envelope, setEnvelope] = useState<Envelope | null>(null);
  const [failure, setFailure] = useState('');
  const [runs, setRuns] = useState<string[] | null>(null);
  const [run, setRun] = useState(() => new URLSearchParams(window.location.search).get('run') ?? '');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [session, setSession] = useState(false);
  const [pick, setPick] = useState<{ file: string } | null>(null);
  const load = (url: string, stale = () => false) => getJson(url).then(json => {
    if (!stale()) { setEnvelope(parseEnvelope(json)); setFailure(''); }
  }).catch(reason => { if (!stale()) setFailure(String(reason?.message ?? reason)); });
  const listRuns = (wanted?: string) => getJson('./api/runs').then(json => {
    const ids = (json.runs as { run_id: string; readable?: boolean }[]).filter(item => item.readable).map(item => item.run_id);
    setRuns(ids);
    setRun(current => [wanted, current].find(id => id && ids.includes(id)) ?? ids[ids.length - 1] ?? '');
  });
  useEffect(() => { listRuns().catch(() => load('./data/visual.json')); }, []);
  useEffect(() => {
    if (!runs || !run) return;
    const address = `./data/visual.json?run=${encodeURIComponent(run)}`;
    let cursor = 0, first = true, stopped = false, busy = false;
    const stale = () => stopped;
    setEnvelope(null); setEvents([]); load(address, stale);
    // Reads every page the journal has, so the status line shows the latest event, not the 100th.
    const poll = async () => {
      if (busy) return;
      busy = true;
      try {
        const fresh: LiveEvent[] = [];
        for (let more = true; more && !stopped;) {
          const json = await getJson(`./api/events?run=${encodeURIComponent(run)}&after=${cursor}`);
          fresh.push(...(json.events as LiveEvent[]));
          cursor = json.next_cursor;
          more = json.has_more;
        }
        if (stopped) return;
        if (fresh.length) setEvents(current => [...current, ...fresh].slice(-20));
        if (!first && fresh.some(item => item.event === 'phase_completed')) load(address, stale);
        first = false;
      } catch { /* the next poll retries */ } finally { busy = false; }
    };
    poll();
    const timer = window.setInterval(poll, POLL_MS);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [runs, run]);
  const last = events[events.length - 1];
  const live = runs && <><div className="live">
    <label>Run <select className="im-select" value={run} onChange={event => setRun(event.target.value)}>{runs.map(id => <option key={id}>{id}</option>)}</select></label>
    <span className="muted" role="status">{last ? `${last.timestamp} · ${last.event}${last.phase == null ? '' : ` · fase ${last.phase}`}${last.message ? ` · ${last.message}` : ''}` : 'Nessun evento'}</span>
    <button type="button" className="im-btn im-btn--ghost im-btn--sm" aria-expanded={session} onClick={() => setSession(!session)}>Sessione e review</button>
  </div>{session && <Session onPick={file => setPick({ file })} onRun={id => { listRuns(id).catch(() => undefined); }} />}</>;
  if (runs && !runs.length) return <><main className="state"><h1>Nessun run</h1><p>Crea un run qui sotto, o avvia una mappa nella sessione.</p></main><Session onPick={() => undefined} onRun={id => { listRuns(id).catch(() => undefined); }} /></>;
  if (failure) return <>{live}<main className="state"><h1>Export non leggibile</h1><p>{failure}</p></main></>;
  if (!envelope) return <>{live}<main className="state" role="status"><span className="im-spinner" aria-hidden="true" /> Carico l'export…</main></>;
  return <>{live}<Explorer key={run} envelope={envelope} pick={pick} /></>;
}

createRoot(document.getElementById('app')!).render(<React.StrictMode><App /></React.StrictMode>);
