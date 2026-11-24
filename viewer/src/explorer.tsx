// The content: one panel, with where the person is, its controls and filters, and the canvas as its body. The controls are
// there in every state and never move: those that do nothing now are disabled (R14).
import { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode, RefObject } from 'react';
import { Button, Cluster, Column, Empty, Icon, Note, Panel, Progress, SearchField, Select, Text, useMedia } from '@acaprino/sigrid';
import { GraphCanvas, GraphLegend } from '@acaprino/sigrid/graph';
import type { GraphCanvasHandle } from '@acaprino/sigrid/graph';
import { createLayoutClient } from './layoutClient.ts';
import type { Layout } from './layoutClient.ts';
import type { Model } from './model.ts';
import { typesIn } from './projection.ts';
import { graphOf, layoutKeyOf, sceneOf } from './scene.ts';
import type { Drawing } from './scene.ts';
import { placeOf, shownDetails } from './state.ts';
import { TYPE_LABEL } from './icons.ts';
import { counted } from './names.ts';

type ExplorerProps = {
  model: Model; title: string; search: RefObject<HTMLInputElement | null>; canvas: RefObject<GraphCanvasHandle | null>;
  ready: boolean;       // the map is shown: without it the body is `children` alone
  runs: ReactNode;      // the choice of the run, where there is one
  children: ReactNode;  // over the canvas, or in its place
};

// The places of what is in view, from ELK in its worker. A drawing is of one layout: until the answer for a new one comes, the
// last one stays on the canvas.
function useLayout(drawing: Drawing, ready: boolean) {
  const [placed, setPlaced] = useState<{ key: string; drawing: Drawing; layout: Layout } | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const client = useRef<ReturnType<typeof createLayoutClient> | null>(null);
  const key = layoutKeyOf(drawing);
  const wanted = ready && drawing.projection.nodes.length > 0;
  const current = placed?.key === key;
  useEffect(() => {
    client.current = createLayoutClient(() => new Worker(new URL('./layout.worker.ts', import.meta.url), { type: 'module' }) as never);
    return () => client.current?.dispose();
  }, []);
  useEffect(() => {
    setFailure(null);
    if (!ready) setPlaced(null);  // another run starts with nothing of the last one
    if (!wanted || current) return;
    let left = false;
    client.current!.request(graphOf(drawing), drawing.direction === 'down' ? 'DOWN' : 'RIGHT')
      .then(layout => { if (!left) setPlaced({ key, drawing, layout }); })
      .catch(reason => { if (!left) setFailure(String(reason?.message ?? reason)); });
    return () => { left = true; };
  }, [key, ready, attempt]);
  return {
    layout: placed?.layout, drawing: placed && !current ? placed.drawing : drawing,
    waiting: wanted && !current && failure === null, failure, retry: () => setAttempt(count => count + 1),
  };
}

export function Explorer({ model, title, search, canvas, ready, runs, children }: ExplorerProps) {
  const { state, dispatch, projection, edges } = model;
  const { envelope, view, scope, open } = state;
  // Beside a docked inspector, and on a phone, the header has no room for the run: it goes with the filters, which wrap.
  const tight = useMedia('(width < 1200px)');
  const direction = useMedia('(width < 850px)') ? 'down' : 'right';
  const graph = useLayout(useMemo<Drawing>(() => ({ projection, edges, direction }), [projection, edges, direction]), ready);
  const scene = useMemo(() => graph.layout && sceneOf(graph.drawing, graph.layout, state.selected, envelope.flows.find(flow => flow.ref === state.flow)),
    [graph.drawing, graph.layout, state.selected, envelope, state.flow]);
  const chosen = state.filters.types?.[0] ?? '';
  const types = useMemo(() => typesIn(envelope, view, scope, open, chosen), [envelope, view, scope, open, chosen]);
  const filtered = ready ? projection.counts.filtered : 0;
  const reset = () => dispatch({ type: 'resetFilters' });
  const info = ready && shownDetails(state) === 'project';
  const message = state.error ?? state.warning;
  const filters = <>
    <SearchField ref={search} disabled={!ready} aria-label="Cerca per nome" placeholder="Cerca per nome" value={state.filters.text ?? ''}
      onValueChange={text => dispatch({ type: 'filter', filters: { text } })} />
    <Select size="sm" aria-label="Tipo di entità" disabled={!ready} value={chosen} onValueChange={type => dispatch({ type: 'filter', filters: { types: type ? [type] : [] } })}
      options={[{ value: '', label: 'Tutti i tipi' }, ...types.map(type => ({ value: type, label: TYPE_LABEL[type] ?? type }))]} />
    {tight && runs}
    <Button variant="ghost" size="sm" disabled={filtered === 0} onClick={reset}><Icon name="clearFilter" />Azzera filtri ({counted(filtered, 'nascosto', 'nascosti')})</Button>
  </>;
  const inView = graph.waiting ? ['Dispongo il grafo…']
    : [counted(projection.nodes.length, 'nodo', 'nodi'), counted(projection.edges.length, 'relazione visibile', 'relazioni visibili')];
  return <Panel title={title}
    subtitle={ready ? [placeOf(state).join(' / '), ...inView].join(' · ') : undefined}
    actions={<>
      <Button variant="ghost" size="sm" disabled={!ready || scope === null} onClick={() => dispatch({ type: 'up' })}><Icon name="back" />Su</Button>
      {!tight && runs}
      <Button variant={info ? 'secondary' : 'ghost'} size="sm" aria-label="Informazioni sul progetto" aria-pressed={info} disabled={!ready}
        onClick={() => dispatch({ type: info ? 'close' : 'info' })}>{tight ? 'Informazioni' : 'Informazioni sul progetto'}</Button>
    </>}
    tools={tight ? filters : <Cluster wrap={false}>{filters}</Cluster>}>
    <Column fill>
      {children}
      {ready && <Column fill pad="lg" aria-busy={graph.waiting || undefined}>
        {message && <Note tone={state.error ? 'error' : 'warning'} title={<Text data-selectable="">{message}</Text>} />}
        {!projection.nodes.length
          ? <Empty fill title="Nessun elemento visibile." action={filtered > 0 && <Button variant="outline" size="sm" onClick={reset}>Azzera filtri</Button>} />
          : graph.failure !== null
          ? <Note tone="error" title="Impossibile disporre il grafo" actions={<Button variant="outline" onClick={graph.retry}><Icon name="refresh" />Riprova</Button>}>
              <Text data-selectable="">{graph.failure}</Text></Note>
          : !scene
          ? <Progress aria-label="Dispongo il grafo…" valueText="Dispongo il grafo…" value={null} />
          : <>
              <GraphCanvas ref={canvas} aria-label="Naviga il grafo" model="graph" fill nodes={scene.nodes} edges={scene.edges} direction={scene.direction}
                layoutKey={scene.layoutKey} selected={scene.selected} steps={scene.steps}
                onSelect={id => dispatch({ type: 'select', ref: id === null ? null : scene.refs.get(id) ?? null })}
                onOpen={id => { const ref = scene.refs.get(id); if (ref !== undefined) dispatch({ type: 'open', ref }); }} />
              <GraphLegend aria-label="Tipi di linea" entries={scene.legend} />
            </>}
      </Column>}
    </Column>
  </Panel>;
}
