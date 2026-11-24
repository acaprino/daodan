// The content: one panel, with where the person is, its controls and filters, and the canvas as its body. The controls are
// there in every state and never move: those that do nothing now are disabled (R14).
import { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode, RefObject } from 'react';
import { Button, Cluster, Column, Icon, Progress, Select, Text } from '@acaprino/sigrid/primitives';
import { Empty, Note, SearchField } from '@acaprino/sigrid/components';
import { Panel, useAppShell } from '@acaprino/sigrid/layout';
import { useMedia } from '@acaprino/sigrid';
import { GraphCanvas, GraphLegend } from '@acaprino/sigrid/graph';
import type { GraphCanvasHandle } from '@acaprino/sigrid/graph';
import { createLayoutClient } from './layoutClient.ts';
import type { Layout } from './layoutClient.ts';
import type { Model, Shown } from './model.ts';
import { typesIn } from './projection.ts';
import { chosenIn, graphOf, layoutKeyOf, sceneOf } from './scene.ts';
import type { Drawing, Scene } from './scene.ts';
import { inSight, onceDrawn } from './sight.ts';
import { placeOf, shownDetails } from './state.ts';
import { TOKEN } from './token.ts';
import { TYPE_LABEL } from './icons.ts';
import { counted } from './names.ts';

const CANVAS = 'Naviga il grafo';

type ExplorerProps = {
  model: Model; title: string; search: RefObject<HTMLInputElement | null>;
  toShow: Shown | null;            // what was last asked for outside the canvas, to bring into its view
  show: (asked: Shown) => void;
  ready: boolean;                  // the map is shown: without it the body is `children` alone
  runs: ReactNode;                 // the choice of the run, where there are runs: it comes and goes, so it is at the loose end of its row
  openOther: ReactNode;            // the button that opens another export
  children: ReactNode;             // over the canvas, or in its place
};

// The places of what is in view, from ELK in its worker. A drawing is of one layout: until the answer for a new one comes, the
// last one stays on the canvas, with the flow it was drawn for.
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
    layout: placed?.layout, drawing: placed && !current ? placed.drawing : drawing, drawn: current,
    waiting: wanted && !current && failure === null, failure, retry: () => setAttempt(count => count + 1),
  };
}

export function Explorer({ model, title, search, toShow, show, ready, runs, openOther, children }: ExplorerProps) {
  const { state, dispatch, projection, edges } = model;
  const { envelope, view, scope, open } = state;
  // Beside a docked inspector, and on a phone, the header has no room for the run and the other export: they go with the filters,
  // which wrap.
  const tight = useMedia('(width < 1200px)');
  // Where the sidebar is not whole the content is a column, and the ranks go down it.
  const direction = useAppShell().sidebar === 'full' ? 'right' : 'down';
  const flow = envelope.flows.find(item => item.ref === state.flow);
  const graph = useLayout(useMemo<Drawing>(() => ({ projection, edges, direction, flow }), [projection, edges, direction, flow]), ready);
  const scene = useMemo(() => graph.layout && sceneOf(graph.drawing, graph.layout, TOKEN), [graph.drawing, graph.layout]);
  const selected = chosenIn(graph.drawing.projection, state.selected);
  // What was asked for outside the canvas (an element, the nodes of a flow) is brought into its view once, when the canvas draws it,
  // and only where a part of it is out of sight: a new layout shows the whole map, which is most often enough. Where it draws no node
  // of it (outside the place, or hidden by the filters) the view stays where the person left it.
  const canvas = useRef<GraphCanvasHandle>(null);
  const shown = useRef<Shown | null>(null);
  const drawnFor = (asked: Shown, { steps }: Scene): readonly string[] => ('ref' in asked
    ? (state.selected === asked.ref ? selected : [])
    : (state.flow === asked.flow && steps ? [...steps.keys()] : []));
  useEffect(() => {
    if (!toShow || shown.current === toShow || !graph.drawn || !scene) return;
    return onceDrawn(() => {
      shown.current = toShow;
      const ids = drawnFor(toShow, scene);
      const labels = scene.nodes.filter(node => ids.includes(node.id)).map(node => node.label);
      if (labels.length && !inSight(CANVAS, labels)) canvas.current?.focus(ids);
    });
  }, [toShow, graph.drawn, scene]);
  const chosen = state.filters.types?.[0] ?? '';
  const types = useMemo(() => typesIn(envelope, view, scope, open, chosen), [envelope, view, scope, open, chosen]);
  const filtered = ready ? projection.counts.filtered : 0;
  const reset = () => dispatch({ type: 'resetFilters' });
  const info = ready && shownDetails(state) === 'project';
  const filters = <>
    <SearchField ref={search} disabled={!ready} aria-label="Cerca per nome" placeholder="Cerca per nome" value={state.filters.text ?? ''}
      onValueChange={text => dispatch({ type: 'filter', filters: { text } })} />
    <Select size="sm" aria-label="Tipo di entità" disabled={!ready} value={chosen} onValueChange={type => dispatch({ type: 'filter', filters: { types: type ? [type] : [] } })}
      options={[{ value: '', label: 'Tutti i tipi' }, ...types.map(type => ({ value: type, label: TYPE_LABEL[type] ?? type }))]} />
    {tight && openOther}
    <Button variant="ghost" size="sm" disabled={filtered === 0} onClick={reset}><Icon name="clearFilter" />Azzera filtri ({counted(filtered, 'nascosto', 'nascosti')})</Button>
    {tight && runs}
  </>;
  // Said as it changes, also where the line is cut: that the layout is waited for, then what is in view.
  const inView = graph.waiting ? 'Dispongo il grafo…'
    : `${counted(projection.nodes.length, 'nodo', 'nodi')} · ${counted(projection.edges.length, 'relazione visibile', 'relazioni visibili')}`;
  return <Panel title={title}
    subtitle={ready ? <>{placeOf(state).join(' / ')} · <Text role="status">{inView}</Text></> : undefined}
    actions={<>
      {!tight && runs}
      <Button variant="ghost" size="sm" disabled={!ready || scope === null}
        onClick={() => { if (scope !== null) { dispatch({ type: 'up' }); show({ ref: scope }); } }}><Icon name="back" />Su</Button>
      {!tight && openOther}
      <Button variant={info ? 'secondary' : 'ghost'} size="sm" aria-label="Informazioni sul progetto" aria-pressed={info} disabled={!ready}
        onClick={() => dispatch({ type: info ? 'close' : 'info' })}>{tight ? 'Informazioni' : 'Informazioni sul progetto'}</Button>
    </>}
    tools={tight ? filters : <Cluster wrap={false}>{filters}</Cluster>}>
    <Column fill>
      {children}
      {ready && <Column fill pad="lg" aria-busy={graph.waiting || undefined}>
        {state.warning && <Note tone="warning" title={<Text data-selectable="">{state.warning}</Text>} />}
        {!projection.nodes.length
          ? <Empty fill title="Nessun elemento visibile." action={filtered > 0 && <Button variant="outline" size="sm" onClick={reset}>Azzera filtri</Button>} />
          : graph.failure !== null
          // The canvas is not there to close a group: the groups opened on it are closed here.
          ? <Note tone="error" title="Impossibile disporre il grafo" actions={<>
              <Button variant="outline" onClick={graph.retry}><Icon name="refresh" />Riprova</Button>
              {open.length > 0 && <Button variant="ghost" onClick={() => dispatch({ type: 'closeGroups' })}>Chiudi i gruppi aperti</Button>}
            </>}><Text data-selectable="">{graph.failure}</Text></Note>
          : !scene
          ? <Progress aria-label="Dispongo il grafo…" valueText="Dispongo il grafo…" value={null} />
          : <>
              {/* A map is read whole first (`minFitZoom`); the canvas keeps what was moved, and its «Riordina» puts it back. */}
              <GraphCanvas ref={canvas} aria-label={CANVAS} model="graph" fill nodes={scene.nodes} edges={scene.edges} direction={scene.direction}
                layoutKey={scene.layoutKey} selected={selected} steps={scene.steps} minFitZoom={0} movable animated
                onSelect={id => dispatch({ type: 'select', ref: id === null ? null : scene.refs.get(id) ?? null })}
                onToggle={id => { const ref = scene.refs.get(id); if (ref !== undefined) dispatch({ type: 'toggleGroup', ref }); }}
                onOpen={id => { const ref = scene.refs.get(id); if (ref !== undefined) dispatch({ type: 'open', ref }); }} />
              <GraphLegend aria-label="Tipi di linea" entries={scene.legend} />
            </>}
      </Column>}
    </Column>
  </Panel>;
}
