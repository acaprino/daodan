import React, { memo, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Background, BackgroundVariant, BaseEdge, Controls, getSmoothStepPath, Handle, MarkerType, Position, ReactFlow,
  ReactFlowProvider, useReactFlow } from '@xyflow/react';
import type { EdgeProps, NodeProps } from '@xyflow/react';
import { ArrowLeft, ChevronRight, FolderOpen, Route, Search, X } from 'lucide-react';
import '@xyflow/react/dist/style.css';
import './style.css';
import { parseEnvelope } from './envelope.ts';
import type { Entity, Envelope, Flow } from './envelope.ts';
import { childrenOf, dataLinks, flowFocus, flowsThrough, indexOf, project } from './projection.ts';
import type { ProjectedEdge, ProjectedNode } from './projection.ts';
import { initialState, reduce } from './state.ts';
import type { Action, ExplorerState } from './state.ts';
import { createLayoutClient, LayoutError } from './layoutClient.ts';
import type { Layout, Point } from './layoutClient.ts';
import { ENTRY_LABEL, FRESHNESS_LABEL, iconFor, LINK_LABEL, STATUS_LABEL, TYPE_LABEL } from './icons.ts';

const SIZE = { width: 224, height: 64 };
const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const join = (...names: (string | false | null | undefined)[]) => names.filter(Boolean).join(' ');

function routePath(points: Point[], radius = 10) {
  const sign = (value: number) => (Math.abs(value) < 0.5 ? 0 : Math.sign(value));
  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length - 1; i++) {
    const p = points[i - 1], c = points[i], n = points[i + 1];
    const r = Math.min(radius, Math.hypot(c.x - p.x, c.y - p.y) / 2, Math.hypot(n.x - c.x, n.y - c.y) / 2);
    d += ` L ${c.x - sign(c.x - p.x) * r} ${c.y - sign(c.y - p.y) * r} Q ${c.x} ${c.y} ${c.x + sign(n.x - c.x) * r} ${c.y + sign(n.y - c.y) * r}`;
  }
  const last = points[points.length - 1];
  let best = 0, label = points[0];
  for (let i = 1; i < points.length; i++) {
    const length = Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y);
    if (length > best) { best = length; label = { x: (points[i].x + points[i - 1].x) / 2, y: (points[i].y + points[i - 1].y) / 2 }; }
  }
  return { d: `${d} L ${last.x} ${last.y}`, label };
}

function nodeMeta(node: ProjectedNode): string {
  return [
    node.nodeType ?? TYPE_LABEL[node.type] ?? node.type,
    node.location === 'external' ? 'esterno' : null,
    node.status && node.status !== 'confirmed' ? STATUS_LABEL[node.status] ?? node.status : null,
    node.freshness && !['fresh', 'uncovered'].includes(node.freshness) ? 'scheda da rileggere' : null,
  ].filter(Boolean).join(' · ');
}

type NodeData = { node: ProjectedNode; selected: boolean; dimmed: boolean; inFlow: boolean; select: (ref: string) => void; open: (ref: string) => void };

const MapNode = memo(function MapNode({ data }: NodeProps) {
  const { node, selected, dimmed, inFlow, select, open } = data as unknown as NodeData;
  const Icon = iconFor(node);
  const meta = nodeMeta(node);
  return <div className={join('node', node.location === 'external' && 'external', selected && 'selected', dimmed && 'dimmed', inFlow && 'in-flow')}>
    <Handle type="target" position={Position.Left} isConnectable={false} />
    <button type="button" className="node-button nodrag" aria-label={`${node.label}. ${meta}`} title={node.ref}
      onClick={event => { event.stopPropagation(); select(node.ref); }}
      onDoubleClick={event => { event.stopPropagation(); if (node.collapsed) open(node.ref); }}>
      <span className="node-icon" aria-hidden="true"><Icon size={16} strokeWidth={1.8} /></span>
      <span className="node-text"><span className="node-name">{node.label}</span><span className="node-meta">{meta}</span></span>
      {node.collapsed && <span className="node-count" aria-label={`${node.count} elementi dentro`}>{node.count}</span>}
    </button>
    <Handle type="source" position={Position.Right} isConnectable={false} />
  </div>;
});

function RoutedEdge({ id, data, markerEnd, style, label, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition }: EdgeProps) {
  const route = (data as { route?: Point[] | null } | undefined)?.route;
  let path: string, labelX: number, labelY: number;
  if (route && route.length > 1) ({ d: path, label: { x: labelX, y: labelY } } = routePath(route));
  else [path, labelX, labelY] = getSmoothStepPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition });
  return <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} label={label} labelX={labelX} labelY={labelY}
    labelShowBg labelBgPadding={[5, 3]} labelBgBorderRadius={4} labelStyle={{ fontSize: 11, fontWeight: 550 }}
    labelBgStyle={{ fill: 'var(--canvas)', fillOpacity: 0.95 }} interactionWidth={18} />;
}

const nodeTypes = { mapNode: MapNode };
const edgeTypes = { routed: RoutedEdge };

function entityName(envelope: Envelope, ref: string): string {
  return indexOf(envelope).byRef.get(ref)?.name ?? ref;
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
    {canOpen && <button type="button" className="primary" onClick={() => dispatch({ type: 'open', ref: entity.ref })}><FolderOpen size={15} />Entra in {entity.name}</button>}
    {flows.length > 0 && <div className="block"><h3>Flussi che lo attraversano</h3>{flows.map(flow =>
      <button type="button" key={flow.ref} className={join('chip', state.flow === flow.ref && 'on')} onClick={() => dispatch({ type: 'flow', ref: flow.ref })}>
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
      <li key={flow.ref}><button type="button" className={join('flow-item', state.flow === flow.ref && 'on')} aria-pressed={state.flow === flow.ref}
        onClick={() => dispatch({ type: 'flow', ref: state.flow === flow.ref ? null : flow.ref })}>
        <span className="flow-name">{entityName(envelope, flow.entry)}</span>
        <span className="muted">{ENTRY_LABEL[flow.entry_kind] ?? flow.entry_kind} · {flow.steps.length} passi{flow.complete ? '' : ' · incompleto'}</span>
      </button></li>)}</ul>
    {current && <ol className="steps">{current.steps.slice(0, 40).map((step, index) =>
      <li key={index}><span>{entityName(envelope, step.source)} <strong>{LINK_LABEL[step.type] ?? step.type}</strong> {entityName(envelope, step.target)}</span>
        <code>{step.route ? `${step.route.slice(1).join(' ')} · ` : ''}{step.site}</code></li>)}</ol>}
  </>;
}

function Explorer({ envelope }: { envelope: Envelope }) {
  const [state, dispatch] = useReducer(reduce, envelope, initialState);
  const [layout, setLayout] = useState<{ key: string; value: Layout } | null>(null);
  const [error, setError] = useState('');
  const [vertical, setVertical] = useState(() => window.matchMedia('(max-width: 899px)').matches);
  const client = useRef<ReturnType<typeof createLayoutClient> | null>(null);
  const flow = useReactFlow();
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

  useEffect(() => {
    if (!layout || layout.key !== key) return;
    const frame = requestAnimationFrame(() => flow.fitView({ padding: 0.12, maxZoom: 1.1, duration: reducedMotion() ? 0 : 200 }));
    return () => cancelAnimationFrame(frame);
  }, [layout?.key]);

  const selectedIds = new Set(state.selected ? projection.owners[state.selected] ?? [] : []);
  const neighbours = new Set(projection.edges.filter(edge => selectedIds.has(edge.source) || selectedIds.has(edge.target)).flatMap(edge => [edge.source, edge.target]));
  const flowNodes = new Set(focus?.nodes ?? []);
  const busy = !layout || layout.key !== key;
  const select = (ref: string) => dispatch({ type: 'select', ref });
  const open = (ref: string) => dispatch({ type: 'open', ref });
  const nodes = busy ? [] : projection.nodes.map(node => {
    const place = layout!.value.nodes[node.id] ?? { x: 0, y: 0 };
    const dimmed = focus ? !flowNodes.has(node.id) : selectedIds.size > 0 && !neighbours.has(node.id) && !selectedIds.has(node.id);
    return { id: node.id, type: 'mapNode', position: { x: place.x, y: place.y }, width: SIZE.width, height: SIZE.height,
      draggable: false, connectable: false, focusable: false,
      data: { node, selected: selectedIds.has(node.id), dimmed, inFlow: flowNodes.has(node.id), select, open } as unknown as Record<string, unknown> };
  });
  const viewEdges = busy ? [] : edges.map(edge => {
    const active = edge.flow || selectedIds.has(edge.source) || selectedIds.has(edge.target);
    const dimmed = (focus && !edge.flow) || (!focus && selectedIds.size > 0 && !active);
    const color = edge.flow ? 'var(--flow)' : active ? 'var(--accent)' : 'var(--edge)';
    const dashed = edge.id.startsWith('data:');
    return { id: edge.id, source: edge.source, target: edge.target, type: 'routed', data: { route: layout!.value.edges[edge.id] },
      label: edge.flow || active ? edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ') : undefined,
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color },
      style: { stroke: color, strokeWidth: edge.flow ? 2.4 : active ? 1.8 : 1.2, opacity: dimmed ? 0.25 : 1,
        strokeDasharray: dashed ? '5 4' : undefined } };
  });

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
      <label className="open-export">Apri altro export<input type="file" accept=".json,application/json" onChange={event => openFile(event.target.files?.[0])} /></label>
    </header>
    {(state.error || state.warning) && <p className={join('notice', state.error && 'bad')} role="status">{state.error ?? state.warning}</p>}
    <div className="toolbar">
      <div className="tabs" role="tablist" aria-label="Vista">
        {(['logical', 'physical'] as const).map(view => <button key={view} type="button" role="tab" aria-selected={state.view === view}
          className={join('tab', state.view === view && 'on')} onClick={() => dispatch({ type: 'view', view })}>{view === 'logical' ? 'Logica' : 'Fisica'}</button>)}
      </div>
      <nav className="crumbs" aria-label="Posizione">
        <button type="button" className="link" onClick={() => dispatch({ type: 'root' })}>Sistema</button>
        {scopeName && <><ChevronRight size={13} aria-hidden="true" /><span aria-current="page">{scopeName}</span>
          <button type="button" className="link" onClick={() => dispatch({ type: 'up' })}><ArrowLeft size={13} />Su</button></>}
      </nav>
      <label className="search"><Search size={14} aria-hidden="true" /><input type="search" placeholder="Cerca per nome" value={state.filters.text ?? ''}
        onChange={event => dispatch({ type: 'filter', filters: { text: event.target.value } })} aria-label="Cerca per nome" /></label>
      <select aria-label="Tipo di entità" value={state.filters.types?.[0] ?? ''} onChange={event => dispatch({ type: 'filter', filters: { types: event.target.value ? [event.target.value] : [] } })}>
        <option value="">Tutti i tipi</option>{types.map(type => <option key={type} value={type}>{TYPE_LABEL[type] ?? type}</option>)}
      </select>
      {filtered > 0 && <button type="button" className="link" onClick={() => dispatch({ type: 'resetFilters' })}><X size={13} />Azzera filtri ({filtered} nascosti)</button>}
    </div>
    <main className="workspace">
      <aside className="navigator">
        <h3>Flussi</h3>
        <FlowPanel state={state} dispatch={dispatch} />
        <h3>Elementi visibili</h3>
        <ul className="element-list">{projection.nodes.map(node => {
          const Icon = iconFor(node);
          return <li key={node.id}><button type="button" className={join('element', selectedIds.has(node.id) && 'on')} onClick={() => select(node.ref)}
            onDoubleClick={() => node.collapsed && dispatch({ type: 'open', ref: node.ref })}><Icon size={14} aria-hidden="true" />{node.label}
            <span className="muted">{nodeMeta(node)}</span></button></li>;
        })}</ul>
      </aside>
      <section className="canvas" aria-label="Grafo">
        <ReactFlow nodes={nodes} edges={viewEdges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} nodesDraggable={false} nodesConnectable={false}
          edgesReconnectable={false} deleteKeyCode={null} minZoom={0.15} maxZoom={1.8} fitView zoomOnDoubleClick={false}
          onNodeClick={(_, node) => select((node.data as unknown as NodeData).node.ref)}
          onNodeDoubleClick={(_, node) => { const item = (node.data as unknown as NodeData).node; if (item.collapsed) dispatch({ type: 'open', ref: item.ref }); }}
          onPaneClick={() => dispatch({ type: 'select', ref: null })}>
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="var(--grid)" />
          <Controls showInteractive={false} position="bottom-left" />
        </ReactFlow>
        {busy && !error && projection.nodes.length > 0 && <div className="canvas-state" role="status">Dispongo il grafo…</div>}
        {!projection.nodes.length && <div className="canvas-state" role="status">Nessun elemento visibile.{filtered > 0 && <button type="button" className="link" onClick={() => dispatch({ type: 'resetFilters' })}>Azzera filtri</button>}</div>}
        {error && <div className="canvas-state bad" role="alert">Impossibile disporre il grafo: {error}</div>}
        <p className="canvas-foot">{projection.nodes.length} nodi · {projection.edges.length} relazioni · {data.length} collegamenti di dati (tratteggiati) · {projection.counts.aggregated} dentro i gruppi{focus ? ` · flusso su ${focus.nodes.length} nodi` : ''}</p>
      </section>
      <Inspector state={state} dispatch={dispatch} edges={projection.edges} />
    </main>
  </div>;
}

function App() {
  const [envelope, setEnvelope] = useState<Envelope | null>(null);
  const [failure, setFailure] = useState('');
  useEffect(() => {
    fetch('./data/visual.json').then(response => (response.ok ? response.json() : Promise.reject(new Error(`HTTP ${response.status}`))))
      .then(json => setEnvelope(parseEnvelope(json))).catch(reason => setFailure(String(reason?.message ?? reason)));
  }, []);
  if (failure) return <main className="state"><h1>Export non leggibile</h1><p>{failure}</p></main>;
  if (!envelope) return <main className="state" role="status">Carico l'export…</main>;
  return <ReactFlowProvider><Explorer envelope={envelope} /></ReactFlowProvider>;
}

createRoot(document.getElementById('app')!).render(<React.StrictMode><App /></React.StrictMode>);
