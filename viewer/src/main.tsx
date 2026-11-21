import React, { useLayoutEffect, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { graphView } from '@acaprino/imago/graph';
import type { GraphScene } from '@acaprino/imago/graph';
import '@acaprino/imago/css/imago.css';
import { createRegistry, footerKeys, formatKeys, notify, openMenu, PALETTE_COMMAND, SEARCH_COMMAND } from '@acaprino/imago/ui';
import type { Registry } from '@acaprino/imago/ui';
import { Icon, Note, PanelState, resetHtml, retryHtml, useSlow } from './parts.tsx';
import { applyStored, graphControls, mountPage, storageOrNull } from './page.ts';
import { Disclosure, ListAction, Shell, TabList, Timeline, Workbench } from '@acaprino/imago/react';
import { getJson, POLL_MS, Session } from './session';
import { parseEnvelope, SCHEMA } from './envelope.ts';
import type { Entity, Envelope, Flow, View } from './envelope.ts';
import { childrenOf, dataLinks, flowFocus, flowsThrough, indexOf, project } from './projection.ts';
import type { ProjectedEdge, ProjectedNode } from './projection.ts';
import { initialState, reduce } from './state.ts';
import type { Action, ExplorerState } from './state.ts';
import { createLayoutClient, LayoutError } from './layoutClient.ts';
import type { Layout } from './layoutClient.ts';
import { ENTRY_LABEL, FRESHNESS_LABEL, iconFor, LINK_LABEL, STATUS_LABEL, TYPE_LABEL } from './icons.ts';

const SIZE = { width: 224, height: 64 };
const viewTabs = [
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

function Details({ state, dispatch, edges, close }: { state: ExplorerState; dispatch: (action: Action) => void; edges: ProjectedEdge[]; close: () => void }) {
  const envelope = state.envelope;
  const header = (title: string) => <header className="im-panel-header"><h4 className="im-panel-title">{title}</h4><span className="im-spacer" />
    <button type="button" className="im-icon-btn" aria-label="Chiudi dettaglio" title="Chiudi dettaglio" onClick={close}><Icon name="close" /></button></header>;
  const entity: Entity | undefined = state.selected ? indexOf(envelope).byRef.get(state.selected) : undefined;
  if (!entity) {
    const meta = envelope.meta as Record<string, unknown>;
    return <>{header('Informazioni sul progetto')}<div className="im-panel-body im-content-text" aria-live="polite">
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
    </div></>;
  }
  const EntityIcon = iconFor({ nodeType: entity.node_type, type: entity.type });
  const flows = flowsThrough(envelope, entity.ref, state.view);
  const canOpen = entity.type !== 'feature' && childrenOf(envelope, entity.ref, state.view).length > 0;
  const gaps = envelope.gaps.filter(gap => gap.refs.includes(entity.ref));
  const lines = Array.isArray(entity.lines) ? entity.lines.filter(Boolean).join('–') : entity.lines;
  const related = edges.filter(edge => edge.source.startsWith(`${entity.ref}@`) || edge.target.startsWith(`${entity.ref}@`));
  return <>{header('Dettaglio')}<div className="im-panel-body im-content-text" aria-live="polite">
    <p className="im-kicker"><EntityIcon className="im-icon" aria-hidden="true" /> {entity.node_type ?? TYPE_LABEL[entity.type] ?? entity.type} · {entity.location === 'external' ? 'esterno' : 'interno'}</p>
    <h2>{entity.name}</h2>
    {entity.path && <code className="im-caption">{entity.path}{lines ? `:${lines}` : ''}</code>}
    {entity.description && <p>{entity.description}</p>}
    <ul className="im-detail-list">
      {entity.provenance && <li>Provenienza: {entity.provenance}</li>}
      {entity.status && <li>Stato: {STATUS_LABEL[entity.status] ?? entity.status}</li>}
      {entity.freshness && <li>{FRESHNESS_LABEL[entity.freshness] ?? entity.freshness}</li>}
    </ul>
    {canOpen && <button type="button" className="im-btn im-btn--primary" onClick={() => dispatch({ type: 'open', ref: entity.ref })}><Icon name="folder" />Entra in {entity.name}</button>}
    {entity.technologies && <Technologies envelope={envelope} ids={entity.technologies} />}
    {flows.length > 0 && <div className="im-section"><h3>Flussi che lo attraversano</h3>{flows.map(flow =>
      <button type="button" key={flow.ref} className="im-btn im-btn--sm" aria-pressed={state.flow === flow.ref} onClick={() => dispatch({ type: 'flow', ref: flow.ref })}>
        <Icon name="branch" />{flowTitle(envelope, flow)}</button>)}</div>}
    {related.length > 0 && <div className="im-section"><h3>Collegamenti visibili</h3><ul className="im-detail-list">{related.slice(0, 20).map(edge => {
      const outgoing = edge.source.startsWith(`${entity.ref}@`);
      const other = (outgoing ? edge.target : edge.source).split('@')[0];
      return <li key={edge.id}>{outgoing ? '→' : '←'} {entityName(envelope, other)} <span className="im-muted">{edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ')}</span></li>;
    })}</ul></div>}
    {entity.evidence.length > 0 && <div className="im-section"><h3>Evidenze</h3><ul className="im-detail-list">{entity.evidence.slice(0, 8).map((item, index) =>
      <li key={index}><code>{item.path}{item.line ? `:${item.line}` : ''}</code></li>)}</ul></div>}
    {gaps.length > 0 && <Note tone="warn" title="Lacune" message={gaps.map(gap => gap.reason).join(' · ')} />}
  </div></>;
}

function bindingSite(flow: Flow): string | undefined {
  return flow.site && flow.column != null ? `${flow.site}:${flow.column}` : flow.site;
}

function flowTitle(envelope: Envelope, flow: Flow): string {
  return flow.label || [flow.event || flow.shape || entityName(envelope, flow.entry), bindingSite(flow)].filter(Boolean).join(' · ');
}

function RunFlows({ state, dispatch }: { state: ExplorerState; dispatch: (action: Action) => void }) {
  const envelope = state.envelope;
  if (!envelope.flows.length) return <p className="im-muted" data-im-rail-detail>Nessun flusso: questo run non ha regole di collegamento (<code>codebase_map_flows</code>).</p>;
  const current: Flow | undefined = envelope.flows.find(flow => flow.ref === state.flow);
  return <>
    <ul className="im-detail-list">{envelope.flows.map(flow =>
      <li key={flow.ref}><ListAction pressed={state.flow === flow.ref} icon={<Icon name="branch" />} rail={<Icon name="branch" />}
        tooltip={flowTitle(envelope, flow)}
        onClick={() => dispatch({ type: 'flow', ref: state.flow === flow.ref ? null : flow.ref })}
        title={flowTitle(envelope, flow)}
        detail={[`${ENTRY_LABEL[flow.entry_kind] ?? flow.entry_kind}`, flow.label ? bindingSite(flow) : null,
          `${flow.steps.length} passi`, flow.complete ? null : 'incompleto'].filter(Boolean).join(' · ')} /></li>)}</ul>
    {current && <div className="im-content-text" data-im-rail-detail><Timeline items={current.steps.slice(0, 40).map((step, index) => ({
      id: index,
      title: <>{entityName(envelope, step.source)} <strong>{LINK_LABEL[step.type] ?? step.type}</strong> {entityName(envelope, step.target)}</>,
      detail: <code>{[step.route?.slice(1).join(' '), step.site, step.origin,
        step.confidence === 'sampled' ? 'campionata dal profiler' : step.confidence === 'observed' ? 'osservata in esecuzione' : null,
        step.conflict ? 'destinazioni in conflitto' : null].filter(Boolean).join(' · ')}</code>,
    }))} /></div>}
    {!!current?.gaps?.length && <div className="im-section" data-im-rail-detail><h3>Dove si ferma la prova</h3>
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

function Navigation({ model, ready }: { model: Model; ready: boolean }) {
  const { state, dispatch, projection, selectedIds } = model;
  if (!ready) return <p className="im-muted im-caption" data-im-rail-detail>In attesa dell'export.</p>;
  return <>
    <h3 data-im-rail-detail>Flussi</h3>
    <RunFlows state={state} dispatch={dispatch} />
    <h3 data-im-rail-detail>Elementi visibili</h3>
    <ul className="im-detail-list">{projection.nodes.map(node => {
      const NodeIcon = iconFor(node);
      return <li key={node.id}><ListAction title={node.label} detail={nodeMeta(node)} tooltip={node.label}
        icon={<NodeIcon className="im-icon" aria-hidden="true" />} rail={<NodeIcon className="im-icon" aria-hidden="true" />} pressed={selectedIds.has(node.id)} onClick={() => dispatch({ type: 'select', ref: node.ref })}
        onDoubleClick={() => node.collapsed && dispatch({ type: 'open', ref: node.ref })} /></li>;
    })}</ul>
  </>;
}

function Explorer({ model }: { model: Model }) {
  const { state, dispatch, projection, focus, data, edges, selectedIds } = model;
  const [layout, setLayout] = useState<{ key: string; value: Layout } | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [vertical, setVertical] = useState(() => (document.querySelector('.im-shell')?.clientWidth ?? window.innerWidth) < 850);
  const client = useRef<ReturnType<typeof createLayoutClient> | null>(null);
  const direction = vertical ? 'DOWN' : 'RIGHT';
  const key = `${direction}|${projection.nodes.map(node => node.id).join(',')}|${edges.map(edge => edge.id).join(',')}`;

  useEffect(() => {
    // A container query cannot reach the layout in the worker: the shell's own width does, as the breakpoints do.
    const shell = document.querySelector('.im-shell');
    const watch = shell && new ResizeObserver(([entry]) => setVertical(entry.contentRect.width < 850));
    if (shell) watch?.observe(shell);
    client.current = createLayoutClient(() => new Worker(new URL('./layout.worker.ts', import.meta.url), { type: 'module' }) as never);
    return () => { watch?.disconnect(); client.current?.dispose(); };
  }, []);

  useEffect(() => {
    if (!client.current) return;
    setError('');
    const graph = { nodes: projection.nodes.map(node => ({ id: node.id, ...SIZE })), edges: edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target })) };
    client.current.request(graph, direction).then(value => setLayout({ key, value })).catch(reason => {
      if (!(reason instanceof LayoutError && reason.reason === 'superseded')) setError(String(reason?.message ?? reason));
    });
  }, [key, attempt]);


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
  const reset = () => dispatch({ type: 'resetFilters' });
  return <>
    {(state.error || state.warning) && <Note tone={state.error ? 'err' : 'warn'} message={state.error ?? state.warning ?? ''} />}
    <div className="im-content-toolbar">
      <nav className="im-cluster" aria-label="Posizione">
        <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'root' })}>Sistema</button>
        {scopeName && <><Icon name="chevron" /><span aria-current="page">{scopeName}</span>
          <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={() => dispatch({ type: 'up' })}><Icon name="back" />Su</button></>}
      </nav>
      <div className="im-field"><label className="im-field-label" htmlFor="map-search">Cerca per nome</label>
        <span className="im-input"><Icon name="search" /><input id="map-search" type="search" placeholder="Nome di un elemento" value={state.filters.text ?? ''}
          onChange={event => dispatch({ type: 'filter', filters: { text: event.target.value } })} /></span></div>
      <div className="im-field"><label className="im-field-label" htmlFor="map-type">Tipo di entità</label>
        <select id="map-type" className="im-select" value={state.filters.types?.[0] ?? ''} onChange={event => dispatch({ type: 'filter', filters: { types: event.target.value ? [event.target.value] : [] } })}>
          <option value="">Tutti i tipi</option>{types.map(type => <option key={type} value={type}>{TYPE_LABEL[type] ?? type}</option>)}
        </select></div>
      {filtered > 0 && <button type="button" className="im-btn im-btn--ghost im-btn--sm" onClick={reset}><Icon name="close" />Azzera filtri ({filtered} nascosti)</button>}
    </div>
    <section className="im-canvas-panel" id="graph-view" role="tabpanel" aria-labelledby={state.view + '-tab'}>
      <div className="im-canvas-frame"><Diagram scene={scene} layoutKey={busy ? '' : key}
        onSelect={id => { const n = byId.get(id); if (n) select(n.ref); }}
        onOpen={id => { const n = byId.get(id); if (n?.collapsed) open(n.ref); }}
        onClear={() => dispatch({ type: 'select', ref: null })} /></div>
      {busy && !error && projection.nodes.length > 0 && <span className="im-loader im-canvas-message" role="status"><span className="im-spinner" aria-hidden="true" />Dispongo il grafo…</span>}
      {!projection.nodes.length && <div className="im-canvas-message"><PanelState state={{ kind: 'empty', text: 'Nessun elemento visibile.', actionHtml: filtered > 0 ? resetHtml : '' }} onAction={reset} /></div>}
      {error && <div className="im-canvas-message"><PanelState state={{ kind: 'error', text: 'Impossibile disporre il grafo: ' + error, retryHtml, errorWord: 'Errore' }} onAction={() => setAttempt(count => count + 1)} /></div>}
    </section>
  </>;
}

// The keys that work now, from the registry: the footer's key list is written, not watched.
function FooterKeys({ registry, mounted }: { registry: Registry; mounted: boolean }) {
  const host = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (mounted) host.current!.replaceChildren(...footerKeys(document, registry, [PALETTE_COMMAND, SEARCH_COMMAND, { keys: 'F6', title: 'Area successiva' }]).childNodes);
  }, [mounted]);
  return <span className="im-footer-keys" ref={host} />;
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
  const shell = useRef<HTMLDivElement>(null);
  const registry = useMemo(() => createRegistry(), []);
  const [overview, setOverview] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { state, dispatch } = model;
  const ready = !(runs && !runs.length) && !failure && model.ready;
  const detailsOpen = ready && (state.selected !== null || overview);
  // What the commands, which live as long as the page, ask of its latest state.
  const now = useRef({ view: (view: View) => dispatch({ type: 'view', view }), info: () => {}, close: () => {}, open: false, ready: false });
  now.current = {
    view: view => dispatch({ type: 'view', view }), open: detailsOpen, ready,
    info: () => { dispatch({ type: 'select', ref: null }); setOverview(true); },
    close: () => { dispatch({ type: 'select', ref: null }); setOverview(false); },
  };
  // Ctrl+F: the search of the map in view; a page that shows no map has none.
  useEffect(() => {
    const unmount = mountPage(shell.current!, registry, { search: () => {
      const field = shell.current!.querySelector<HTMLInputElement>('input[type="search"]');
      if (field) field.focus(); else notify(shell.current!, 'Questa vista non ha una ricerca.');
    } });
    const off = [
      registry.register({ id: 'daodan.view.logical', title: 'Vista logica', group: 'Vista', run: () => now.current.view('logical') }),
      registry.register({ id: 'daodan.view.physical', title: 'Vista fisica', group: 'Vista', run: () => now.current.view('physical') }),
      registry.register({ id: 'daodan.project.info', title: 'Informazioni sul progetto', group: 'Vista', when: () => now.current.ready, run: () => now.current.info() }),
      registry.register({ id: 'daodan.details.close', title: 'Chiudi dettaglio', group: 'Vista', keys: 'Escape', when: () => now.current.open, run: () => now.current.close() }),
    ];
    setMounted(true);
    return () => { setMounted(false); off.forEach(unregister => unregister()); unmount(); };
  }, []);
  useEffect(() => {
    const ref = pick && envelope && fileRef(envelope, pick.file);
    if (ref) model.dispatch({ type: 'select', ref });
  }, [pick]);
  const addressOf = (id: string) => `./data/visual.json?run=${encodeURIComponent(id)}`;
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
    const address = addressOf(run);
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
  const meta = state.envelope.meta as Record<string, unknown>;
  const projectName = String(meta.project_root ?? '').split(/[\\/]/).filter(Boolean).pop() ?? '';
  const openFile = async (file: File | undefined) => {
    if (!file) return;
    try { dispatch({ type: 'replaceEnvelope', json: JSON.parse(await file.text()) }); }
    catch (reason) { dispatch({ type: 'replaceEnvelope', json: { error: String(reason) } }); }
  };
  const noRuns = runs && !runs.length;
  const slow = useSlow(!noRuns && !failure && !envelope);
  const views = [{ value: 'logical', label: 'Logica' }, { value: 'physical', label: 'Fisica' }] as const;
  const viewsMenu = (anchor: HTMLElement) => {
    const close = openMenu(anchor, views.map(view => ({ label: view.label, checked: () => state.view === view.value, run: () => { close(); dispatch({ type: 'view', view: view.value }); } })));
  };
  // Written in JSX as using-imago.md section 4 shows it: titlebarHtml is a string frame and cannot be written from React.
  const titlebar = <header className="im-titlebar">
    <div className="im-brand"><span className="im-mark" aria-hidden="true">D</span><span className="im-wordmark">Daodan</span></div>
    <button type="button" className="im-icon-btn im-sidebar-toggle" aria-label="Mappa" title="Mappa" aria-expanded="false" aria-controls="sidebar"><Icon name="sidebar" /></button>
    <TabList label="Vista" tabs={viewTabs} value={state.view} onSelect={view => dispatch({ type: 'view', view })} />
    <button type="button" className="im-btn im-btn--ghost im-btn--sm im-views-menu" aria-haspopup="menu" aria-expanded="false" onClick={event => viewsMenu(event.currentTarget)}>Viste<Icon name="chevron" /></button>
    <span className="im-spacer" />
    <button type="button" className="im-titlebar-command" aria-label="Comandi" onClick={() => registry.get(PALETTE_COMMAND)?.run()}><Icon name="search" /><b>Comandi</b><kbd className="im-key">{formatKeys('Ctrl+K').join(' ')}</kbd></button>
  </header>;
  // The live event line is the run's, so it shows while its export is loading or unreadable too.
  const status = <>
    <span className="im-status-text im-content-text">{ready ? `${projectName}${meta.target && meta.target !== '.' ? ` / ${String(meta.target)}` : ''} · run ${String(meta.run_id ?? '')}`
      : noRuns ? 'Nessun run' : failure ? 'Export non leggibile' : "Carico l'export…"}</span>
    <span className="im-spacer" />
    {(ready || (runs && !noRuns)) && <span className="im-status-end im-content-text" role="status">{last ? `${last.timestamp} · ${last.event}${last.phase == null ? '' : ` · fase ${last.phase}`}${last.message ? ` · ${last.message}` : ''}` : 'Nessun evento'}</span>}
  </>;
  const footer = <>
    <span className="im-footer-text" data-graph-counts>{ready
      ? `${state.envelope.entities.length} entità · ${state.envelope.relations.length} relazioni · ${state.envelope.flows.length} flussi · ${state.envelope.gaps.length} lacune · ${model.projection.nodes.length} nodi · ${model.projection.edges.length} relazioni visibili · ${model.data.length} collegamenti di dati (tratteggiati) · ${model.projection.counts.aggregated} dentro i gruppi${model.focus ? ` · flusso su ${model.focus.nodes.length} nodi` : ''}`
      : 'Nessuna mappa'}</span>
    <span className="im-spacer" /><FooterKeys registry={registry} mounted={mounted} />
  </>;
  const toolbar = <div className="im-content-toolbar">
    {runs && <div className="im-field"><label className="im-field-label" htmlFor="run-select">Run</label>
      <select id="run-select" className="im-select" value={run} onChange={event => setRun(event.target.value)}>{runs.map(id => <option key={id}>{id}</option>)}</select></div>}
    {ready && <>
      <button type="button" className="im-btn im-btn--sm" onClick={() => now.current.info()}><Icon name="info" />Informazioni sul progetto</button>
      <label className="im-end im-cluster">Apri altro export<input className="im-file-selector" type="file" accept=".json,application/json" onChange={event => openFile(event.target.files?.[0])} /></label></>}
  </div>;
  const content = noRuns ? <><PanelState state={{ kind: 'empty', text: 'Nessun run: creane uno qui sotto, o avvia una mappa nella sessione.' }} />
      <Session onPick={() => undefined} onRun={id => { listRuns(id).catch(() => undefined); }} /></>
    : <>{toolbar}{runs && <Disclosure label="Sessione e review">
      <Session onPick={file => setPick({ file })} onRun={id => { listRuns(id).catch(() => undefined); }} />
    </Disclosure>}{failure ? <PanelState state={{ kind: 'error', text: failure, retryHtml, errorWord: 'Errore' }} onAction={() => { setFailure(''); load(runs && run ? addressOf(run) : './data/visual.json'); }} />
      : !envelope ? slow && <PanelState state={{ kind: 'loading', rows: 3 }} />
      : ready && <Explorer key={run} model={model} />}</>;
  return <Shell ref={shell} sidebar skipLabel="Vai al contenuto" titlebar={titlebar}>
    <Workbench aria-label="Codebase Map" aria-busy={!noRuns && !failure && !envelope} detailsLabel="Dettaglio" navigationLabel="Mappa" status={status} footer={footer}
      navigation={<Navigation model={model} ready={ready} />}
      details={detailsOpen ? <Details state={state} dispatch={dispatch} edges={model.projection.edges} close={() => now.current.close()} /> : null}>{content}</Workbench>
  </Shell>;
}

applyStored(document.documentElement, storageOrNull());
createRoot(document.getElementById('app')!).render(<React.StrictMode><App /></React.StrictMode>);
