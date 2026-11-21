import React, { useLayoutEffect, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { graphView } from '@acaprino/imago/graph';
import type { GraphScene } from '@acaprino/imago/graph';
import { graphControls } from './appearance';
import { ArrowLeft, ChevronRight, FolderOpen, Route, Search, X } from 'lucide-react';
import { Disclosure, ListAction, Shell, TabList, Timeline, Workbench } from '@acaprino/imago/react';
import { getJson, POLL_MS, Session } from './session';
import { parseEnvelope, SCHEMA } from './envelope.ts';
import type { Entity, Envelope, Flow } from './envelope.ts';
import { childrenOf, dataLinks, flowFocus, flowsThrough, indexOf, project } from './projection.ts';
import type { ProjectedEdge, ProjectedNode } from './projection.ts';
import { initialState, reduce } from './state.ts';
import type { Action, ExplorerState } from './state.ts';
import { createLayoutClient, LayoutError } from './layoutClient.ts';
import type { Layout } from './layoutClient.ts';
import { ENTRY_LABEL, FRESHNESS_LABEL, iconFor, LINK_LABEL, STATUS_LABEL, TYPE_LABEL } from './icons.ts';

const SIZE = { width: 224, height: 64 };
const views = [
  { value: 'logical', label: 'Logica', id: 'logical-tab', panel: 'graph-view' },
  { value: 'physical', label: 'Fisica', id: 'physical-tab', panel: 'graph-view' },
] as const;



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
  return <div ref={host} className="im-fill" />;
}

function entityName(envelope: Envelope, ref: string): string {
  return indexOf(envelope).byRef.get(ref)?.name ?? ref;
}

// The technologies of the project, or those of one build unit (`ids`); each names the files that show it.
function Technologies({ envelope, ids }: { envelope: Envelope; ids?: string[] }) {
  const shown = envelope.technologies.filter(item => !ids || ids.includes(item.id));
  if (!shown.length) return null;
  return <div className="im-section"><h3>Tecnologie</h3><ul className="im-detail-list">{shown.map(item =>
    <li key={item.id} title={item.paths.join('\n')}>{item.name} <span className="im-muted">{item.type}</span></li>)}</ul></div>;
}

function EntityDetails({ state, dispatch, edges }: { state: ExplorerState; dispatch: (action: Action) => void; edges: ProjectedEdge[] }) {
  const envelope = state.envelope;
  const entity: Entity | undefined = state.selected ? indexOf(envelope).byRef.get(state.selected) : undefined;
  if (!entity) {
    const meta = envelope.meta as Record<string, unknown>;
    return <div className="im-panel-body im-content-text" aria-live="polite">
      <p className="im-kicker">Come leggere la mappa</p>
      <h2>{String(meta.project_root ?? 'Progetto').split(/[\\/]/).filter(Boolean).pop()}</h2>
      <p>Seleziona un nodo per vederne il ruolo, i collegamenti e i flussi che lo attraversano. Doppio clic su un nodo con un numero per entrarci.</p>
      <ul className="im-detail-list">
        <li>{envelope.entities.length} entità, {envelope.relations.length} relazioni</li>
        <li>{envelope.flows.length} flussi dai punti d'ingresso</li>
        <li>{envelope.gaps.length} lacune dichiarate</li>
      </ul>
      <p className="im-muted">Nei flussi puoi leggere il sito e la provenienza della prova per ogni passaggio.</p>
      <Technologies envelope={envelope} />
    </div>;
  }
  const Icon = iconFor({ nodeType: entity.node_type, type: entity.type });
  const flows = flowsThrough(envelope, entity.ref, state.view);
  const canOpen = entity.type !== 'feature' && childrenOf(envelope, entity.ref, state.view).length > 0;
  const gaps = envelope.gaps.filter(gap => gap.refs.includes(entity.ref));
  const lines = Array.isArray(entity.lines) ? entity.lines.filter(Boolean).join('–') : entity.lines;
  const related = edges.filter(edge => edge.source.startsWith(`${entity.ref}@`) || edge.target.startsWith(`${entity.ref}@`));
  return <div className="im-panel-body im-content-text" aria-live="polite">
    <p className="im-kicker"><Icon size={14} aria-hidden="true" /> {entity.node_type ?? TYPE_LABEL[entity.type] ?? entity.type} · {entity.location === 'external' ? 'esterno' : 'interno'}</p>
    <h2>{entity.name}</h2>
    {entity.path && <code className="im-caption">{entity.path}{lines ? `:${lines}` : ''}</code>}
    {entity.description && <p>{entity.description}</p>}
    <ul className="im-detail-list">
      {entity.provenance && <li>Provenienza: {entity.provenance}</li>}
      {entity.status && <li>Stato: {STATUS_LABEL[entity.status] ?? entity.status}</li>}
      {entity.freshness && <li>{FRESHNESS_LABEL[entity.freshness] ?? entity.freshness}</li>}
    </ul>
    {canOpen && <button type="button" className="im-btn im-btn--primary" onClick={() => dispatch({ type: 'open', ref: entity.ref })}><FolderOpen size={15} />Entra in {entity.name}</button>}
    {entity.technologies && <Technologies envelope={envelope} ids={entity.technologies} />}
    {flows.length > 0 && <div className="im-section"><h3>Flussi che lo attraversano</h3>{flows.map(flow =>
      <button type="button" key={flow.ref} className="im-btn im-btn--sm" aria-pressed={state.flow === flow.ref} onClick={() => dispatch({ type: 'flow', ref: flow.ref })}>
        <Route size={12} />{flowTitle(envelope, flow)}</button>)}</div>}
    {related.length > 0 && <div className="im-section"><h3>Collegamenti visibili</h3><ul className="im-detail-list">{related.slice(0, 20).map(edge => {
      const outgoing = edge.source.startsWith(`${entity.ref}@`);
      const other = (outgoing ? edge.target : edge.source).split('@')[0];
      return <li key={edge.id}>{outgoing ? '→' : '←'} {entityName(envelope, other)} <span className="im-muted">{edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ')}</span></li>;
    })}</ul></div>}
    {entity.evidence.length > 0 && <div className="im-section"><h3>Evidenze</h3><ul className="im-detail-list">{entity.evidence.slice(0, 8).map((item, index) =>
      <li key={index}><code>{item.path}{item.line ? `:${item.line}` : ''}</code></li>)}</ul></div>}
    {gaps.length > 0 && <div className="im-section im-text-warn"><h3>Lacune</h3>{gaps.map((gap, index) => <p key={index}>{gap.reason}</p>)}</div>}
  </div>;
}

function bindingSite(flow: Flow): string | undefined {
  return flow.site && flow.column != null ? `${flow.site}:${flow.column}` : flow.site;
}

function flowTitle(envelope: Envelope, flow: Flow): string {
  return flow.label || [flow.event || flow.shape || entityName(envelope, flow.entry), bindingSite(flow)].filter(Boolean).join(' · ');
}

function RunFlows({ state, dispatch }: { state: ExplorerState; dispatch: (action: Action) => void }) {
  const envelope = state.envelope;
  if (!envelope.flows.length) return <p className="im-muted">Nessun flusso: questo run non ha regole di collegamento (<code>codebase_map_flows</code>).</p>;
  const current: Flow | undefined = envelope.flows.find(flow => flow.ref === state.flow);
  return <>
    <ul className="im-detail-list">{envelope.flows.map(flow =>
      <li key={flow.ref}><ListAction pressed={state.flow === flow.ref}
        onClick={() => dispatch({ type: 'flow', ref: state.flow === flow.ref ? null : flow.ref })}
        title={flowTitle(envelope, flow)}
        detail={[`${ENTRY_LABEL[flow.entry_kind] ?? flow.entry_kind}`, flow.label ? bindingSite(flow) : null,
          `${flow.steps.length} passi`, flow.complete ? null : 'incompleto'].filter(Boolean).join(' · ')} /></li>)}</ul>
    {current && <div className="im-content-text"><Timeline items={current.steps.slice(0, 40).map((step, index) => ({
      id: index,
      title: <>{entityName(envelope, step.source)} <strong>{LINK_LABEL[step.type] ?? step.type}</strong> {entityName(envelope, step.target)}</>,
      detail: <code>{[step.route?.slice(1).join(' '), step.site, step.origin,
        step.confidence === 'sampled' ? 'campionata dal profiler' : step.confidence === 'observed' ? 'osservata in esecuzione' : null,
        step.conflict ? 'destinazioni in conflitto' : null].filter(Boolean).join(' · ')}</code>,
    }))} /></div>}
    {!!current?.gaps?.length && <div className="im-section"><h3>Dove si ferma la prova</h3>
      <ul className="im-detail-list">{current.gaps.map((gap, index) =>
        <li key={index}><code>{gap.site}</code> · {gap.reason}</li>)}</ul></div>}
  </>;
}

// A finding names a project-relative file; the envelope's refs are relative to the run's target.
function fileRef(envelope: Envelope, file: string): string | null {
  const target = String(envelope.meta.target ?? '.').replace(/\/+$/, '');
  if (target === '.' || target === '') return `file:${file}`;
  return file.startsWith(`${target}/`) ? `file:${file.slice(target.length + 1)}` : null;
}

const EMPTY = parseEnvelope({ schema: SCHEMA, entities: [], relations: [], memberships: [] });
type Model = ReturnType<typeof useExplorer>;

// The explorer's state and what is projected from it, for the whole page: the sidebar, the details and the canvas read it.
function useExplorer(envelope: Envelope | null) {
  const [state, dispatch] = useReducer(reduce, EMPTY, initialState);
  const shown = useRef<Envelope | null>(null);
  useEffect(() => {  // the first export of a run starts clean, a later one keeps the person's place
    if (!envelope) { shown.current = null; return; }
    dispatch(shown.current ? { type: 'replaceEnvelope', json: envelope } : { type: 'load', envelope });
    shown.current = envelope;
  }, [envelope]);
  const projection = useMemo(() => project(state.envelope, state.view, state.scope, state.filters, state.open, state.selected),
    [state.envelope, state.view, state.scope, state.filters, state.open, state.selected]);
  const focus = useMemo(() => (state.flow ? flowFocus(state.envelope, state.flow, projection) : null), [state.flow, projection]);
  const data = useMemo(() => (focus ? [] : dataLinks(state.envelope, projection)), [focus, projection]);
  const edges = useMemo(() => [...projection.edges, ...data, ...(focus?.edges ?? [])], [projection, data, focus]);
  const selectedIds = new Set(state.selected ? projection.owners[state.selected] ?? [] : []);
  return { state, dispatch, projection, focus, data, edges, selectedIds, ready: envelope !== null && shown.current !== null && state.envelope !== EMPTY };
}

function Navigation({ model }: { model: Model }) {
  const { state, dispatch, projection, selectedIds } = model;
  return <>
    <h3>Flussi</h3>
    <RunFlows state={state} dispatch={dispatch} />
    <h3>Elementi visibili</h3>
    <ul className="im-detail-list">{projection.nodes.map(node => {
      const Icon = iconFor(node);
      return <li key={node.id}><ListAction title={node.label} detail={nodeMeta(node)}
        icon={<Icon size={14} aria-hidden="true" />} pressed={selectedIds.has(node.id)} onClick={() => dispatch({ type: 'select', ref: node.ref })}
        onDoubleClick={() => node.collapsed && dispatch({ type: 'open', ref: node.ref })} /></li>;
    })}</ul>
  </>;
}

function Explorer({ model }: { model: Model }) {
  const { state, dispatch, projection, focus, data, edges, selectedIds } = model;
  const [layout, setLayout] = useState<{ key: string; value: Layout } | null>(null);
  const [error, setError] = useState('');
  const [vertical, setVertical] = useState(() => window.matchMedia('(max-width: 899px)').matches);
  const client = useRef<ReturnType<typeof createLayoutClient> | null>(null);
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
        label: [edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', '), edge.uncertain ? 'prova insufficiente' : null].filter(Boolean).join(' · '),
        showLabel: !!edge.flow || active,
        dashed: edge.uncertain || edge.id.startsWith('data:'), tone: edge.uncertain || edge.flow ? 'warn' : active ? 'accent' : undefined,
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

  return <>
    <header className="im-content-toolbar">
      <strong>Codebase Map</strong>
      <span className="im-muted">{project_name}{meta.target && meta.target !== '.' ? ` / ${String(meta.target)}` : ''} · run {String(meta.run_id ?? '')}</span>
      <label className="im-end im-cluster">Apri altro export<input className="im-file-selector" type="file" accept=".json,application/json" onChange={event => openFile(event.target.files?.[0])} /></label>
    </header>
    {(state.error || state.warning) && <p className="im-note" data-im-tone={state.error ? 'err' : 'warn'} role="status">{state.error ?? state.warning}</p>}
    <div className="im-content-toolbar">
      <TabList label="Vista" tabs={views} value={state.view} onSelect={view => dispatch({ type: 'view', view })} />
      <nav className="im-cluster" aria-label="Posizione">
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
      <section className="im-canvas-panel" id="graph-view" role="tabpanel" aria-labelledby={state.view + '-tab'}>
        <div className="im-canvas-frame"><Diagram scene={scene} layoutKey={busy ? '' : key}
          onSelect={id => { const n = byId.get(id); if (n) select(n.ref); }}
          onOpen={id => { const n = byId.get(id); if (n?.collapsed) open(n.ref); }}
          onClear={() => dispatch({ type: 'select', ref: null })} /></div>
        {busy && !error && projection.nodes.length > 0 && <div className="im-canvas-message im-note" role="status"><span className="im-spinner" aria-hidden="true" /> Dispongo il grafo…</div>}
        {!projection.nodes.length && <div className="im-canvas-message im-note" role="status">Nessun elemento visibile.{filtered > 0 && <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'resetFilters' })}>Azzera filtri</button>}</div>}
        {error && <div className="im-canvas-message im-note" data-im-tone="err" role="alert">Impossibile disporre il grafo: {error}</div>}
        <p className="im-caption im-content-toolbar" data-graph-counts>{projection.nodes.length} nodi · {projection.edges.length} relazioni · {data.length} collegamenti di dati (tratteggiati) · {projection.counts.aggregated} dentro i gruppi{focus ? ` · flusso su ${focus.nodes.length} nodi` : ''}</p>
      </section>
  </>;
}

type LiveEvent = { cursor: number; timestamp: string; event: string; message: string; phase?: number };
// Served by the MCP server the page lists the runs and follows the chosen run's events; served from an export it draws that file.
function App() {
  const [envelope, setEnvelope] = useState<Envelope | null>(null);
  const [failure, setFailure] = useState('');
  const [runs, setRuns] = useState<string[] | null>(null);
  const [run, setRun] = useState(() => new URLSearchParams(window.location.search).get('run') ?? '');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [pick, setPick] = useState<{ file: string } | null>(null);
  const model = useExplorer(envelope);
  useEffect(() => {
    const ref = pick && envelope && fileRef(envelope, pick.file);
    if (ref) model.dispatch({ type: 'select', ref });
  }, [pick]);
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
  const live = runs && <><div className="im-content-toolbar">
    <label>Run <select className="im-select" value={run} onChange={event => setRun(event.target.value)}>{runs.map(id => <option key={id}>{id}</option>)}</select></label>
    <span className="im-muted" role="status">{last ? `${last.timestamp} · ${last.event}${last.phase == null ? '' : ` · fase ${last.phase}`}${last.message ? ` · ${last.message}` : ''}` : 'Nessun evento'}</span>
  </div><Disclosure label="Sessione e review">
    <Session onPick={file => setPick({ file })} onRun={id => { listRuns(id).catch(() => undefined); }} />
  </Disclosure></>;
  const empty = (title: string, text: string, status?: boolean) => <div className="im-empty" role={status ? 'status' : undefined}><strong>{title}</strong><p>{text}</p></div>;
  const noRuns = runs && !runs.length;
  const ready = !noRuns && !failure && model.ready;
  const content = noRuns ? <>{empty('Nessun run', 'Crea un run qui sotto, o avvia una mappa nella sessione.')}
      <Session onPick={() => undefined} onRun={id => { listRuns(id).catch(() => undefined); }} /></>
    : <>{live}{failure ? empty('Export non leggibile', failure) : !envelope ? empty("Carico l'export…", '', true)
      : ready && <Explorer key={run} model={model} />}</>;
  return <Shell sidebar={ready} skipLabel="Vai al contenuto" titlebar={titlebar}>
    <Workbench aria-label="Codebase Map" detailsLabel="Dettaglio" navigationLabel="Mappa"
      navigation={ready ? <Navigation model={model} /> : null}
      details={ready ? <EntityDetails state={model.state} dispatch={model.dispatch} edges={model.projection.edges} /> : null}>{content}</Workbench>
  </Shell>;
}

const titlebar = <header className="im-titlebar"><div className="im-brand">
  <span className="im-mark" aria-hidden="true">D</span><span className="im-wordmark">Daodan</span></div></header>;

createRoot(document.getElementById('app')!).render(<React.StrictMode><App /></React.StrictMode>);
