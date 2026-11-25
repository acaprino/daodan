// The graph of the code: its filters, the canvas with its groups opened in place, and the details of the one chosen in the inspector.
import { memo, useCallback, useEffect, useMemo, useRef } from 'react';
import type { ReactNode } from 'react';
import { useFocusKept } from '@acaprino/imago';
import { Button, Cluster, Column, Icon, Select, Split, Text } from '@acaprino/sigrid/primitives';
import { Empty, SearchField } from '@acaprino/sigrid/components';
import { useMedia } from '@acaprino/sigrid';
import { GraphCanvas, GraphLegend } from '@acaprino/sigrid/graph';
import type { GraphCanvasHandle } from '@acaprino/sigrid/graph';
import { onceDrawn } from '../src/sight.ts';
import { Loading } from '../src/states.tsx';
import { plural } from '../src/words.ts';
import { ExplorerLink } from './explorer-link.tsx';
import { ScreenPanel, useFrame } from './frame.tsx';
import { filtersOn, isOpenGroup, levelsName, thingById, toggledGroup, visibleGraph } from './graph.ts';
import type { Graph } from './graph.ts';
import { graphDetail, groupOf } from './group-details.tsx';
import { PROVENANCE } from './provenance.tsx';
import { sceneOf } from './scene.ts';
import { ctx } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';
import { GraphFailed, NoGroups } from './states.tsx';
import type { Kept } from './storage.ts';
import { model, useModelSlice } from './use-model.ts';

const CANVAS = 'Grafo interattivo';

// In the window's action bar, where the run has the same link.
export const graphActions = (s: Snapshot): ReactNode => ctx(s) && <ExplorerLink />;

// The details of the group the graph is read from, when the person has just come to the screen or chosen it: as soon as the graph has it.
function useWantedGroup() {
  const { show } = useFrame();
  const graph = useModelSlice(s => s.graph), root = useModelSlice(s => s.kept.graphRoot), wanted = useModelSlice(s => s.groupWanted);
  useEffect(() => {
    const n = wanted ? graph?.nodes.find(item => item.id === root) : undefined;
    if (!n) return;
    show(graphDetail(n));
    model.groupShown();
  }, [graph, root, wanted]);
}

// The search takes the focus: what was pressed is disabled or gone.
function useClear() {
  const { field } = useFrame();
  return () => {
    model.clearGraphFilters();
    field?.focus();
  };
}

const DIRECTIONS = [{ value: 'out', label: 'Dipendenze →' }, { value: 'in', label: '← Chiamanti' }, { value: 'both', label: 'Entrambe le direzioni' }];
const DEPTHS = [{ value: '1', label: '1 livello' }, { value: '2', label: '2 livelli' }, { value: 'all', label: 'Tutto il grafo' }];
const KINDS = [{ value: 'all', label: 'Tutte le relazioni' }, { value: 'calls', label: 'Chiamate' }, { value: 'imports', label: 'Import' }, { value: 'uses', label: 'Utilizzi' }];

// They keep their place in every state: without a graph to filter they are disabled (R14).
function Filters({ ready }: { ready: boolean }) {
  const kept = useModelSlice(s => s.kept);
  const { search } = useFrame();
  const clear = useClear();
  const tight = useMedia('(width < 1200px)');  // as on the map: the search has a row of its own, and the others wrap
  const filters = <>
    <SearchField ref={ready ? search : null} disabled={!ready} aria-label="Cerca un gruppo o un file" placeholder="Cerca gruppo o file…" value={kept.graphSearch}
      onValueChange={graphSearch => model.keep({ graphSearch })} />
    <Select size="sm" aria-label="Direzione" disabled={!ready} value={kept.graphDirection} options={DIRECTIONS}
      onValueChange={value => model.keep({ graphDirection: value as Kept['graphDirection'] })} />
    <Select size="sm" aria-label="Profondità" disabled={!ready} value={kept.graphDepth} options={DEPTHS}
      onValueChange={value => model.keep({ graphDepth: value as Kept['graphDepth'] })} />
    <Select size="sm" aria-label="Relazioni" disabled={!ready} value={kept.graphKind} options={KINDS}
      onValueChange={value => model.keep({ graphKind: value as Kept['graphKind'] })} />
    <Button variant="ghost" size="sm" disabled={!ready || !filtersOn(kept)} onClick={clear}><Icon name="clearFilter" />Azzera filtri</Button>
  </>;
  return tight ? filters : <Cluster wrap={false}>{filters}</Cluster>;
}

type Visible = Pick<Graph, 'nodes' | 'edges'>;

// What is in view, or that another graph is being read while this one stays.
function InView({ relations }: { relations: number }) {
  const loading = useModelSlice(s => s.graphLoading);
  return <Text variant="note">
    <Text aria-live="polite">{loading ? 'Lettura del grafo…' : plural(relations, 'relazione visibile', 'relazioni visibili')}</Text> · seleziona un nodo, apri un gruppo sul posto
  </Text>;
}

// Drawn again when the graph, what is in view of it or the choice is another: an event of the run does not touch the canvas.
const Canvas = memo(function Canvas({ graph, visible, selected, onSelect }: {
  graph: Graph; visible: Visible; selected: string | null; onSelect: (id: string | null) => void;
}) {
  const direction = useMedia('(width < 850px)') ? 'down' : 'right';
  const scene = useMemo(() => sceneOf({ ...visible, open: graph.open }, model.markUrl), [graph, visible]);
  // A group just opened or closed is brought into the view, which a new layout fits to the whole graph, from its start where it is large.
  const canvas = useRef<GraphCanvasHandle>(null), before = useRef(graph);
  // The details that open with the graph slide in beside it: the whole graph is brought into the view they leave.
  useEffect(() => onceDrawn(CANVAS, () => canvas.current?.fit()), []);
  useEffect(() => {
    const toggled = toggledGroup(before.current, graph);
    before.current = graph;
    if (toggled !== null) canvas.current?.focus([toggled]);
  }, [graph]);
  return <>
    <GraphCanvas ref={canvas} aria-label={CANVAS} model="graph" fill movable animated nodes={scene.nodes} edges={scene.edges} direction={direction}
      layoutKey={`${direction}|${scene.key}`} selected={selected} onSelect={onSelect} onToggle={model.toggleGroup} />
    <Split>
      <GraphLegend aria-label="Tipi di linea" entries={scene.legend} />
      <InView relations={scene.edges.length} />
    </Split>
  </>;
});

function Drawing({ graph, visible }: { graph: Graph; visible: Visible }) {
  const { detail, show, close } = useFrame();
  const shown = groupOf(detail);
  const choose = useCallback((id: string | null) => {
    const thing = id === null ? undefined : thingById(graph, id);
    if (!thing) { if (shown !== null) close(); return; }
    if (isOpenGroup(thing)) show(graphDetail(thing));  // the graph is read from a node, never from an open group
    else model.selectNode(thing.id);
  }, [graph, shown, show, close]);
  return <Canvas graph={graph} visible={visible} selected={shown} onSelect={choose} />;
}

// What is in view of the graph with the filters. Where the whole graph is, a choice alone does not lay it out again: only the depth is
// counted from the group chosen.
function useVisible(graph: Graph | null): Visible | null {
  const { graphSearch, graphRoot, graphDirection, graphDepth, graphKind } = useModelSlice(s => s.kept);
  const root = graphDepth === 'all' ? '' : graphRoot;
  return useMemo(() => graph && visibleGraph(graph, { graphSearch, graphRoot: root, graphDirection, graphDepth, graphKind }),
    [graph, graphSearch, root, graphDirection, graphDepth, graphKind]);
}

export function GraphScreen() {
  const { show, go } = useFrame();
  const clear = useClear();
  const graph = useModelSlice(s => s.graph), error = useModelSlice(s => s.graphError), loading = useModelSlice(s => s.graphLoading);
  const read = useModelSlice(s => s.server !== null), context = useModelSlice(ctx), serverError = useModelSlice(s => s.serverError);
  const visible = useVisible(graph);
  useWantedGroup();
  useFocusKept(error, graph === null, visible?.nodes.length === 0);  // the canvas goes, with the focus that was in it
  const ready = graph !== null && visible !== null && error === '';
  return <ScreenPanel title="Grafo del codice" tools={<Filters ready={ready} />}
    subtitle={ready && [levelsName(graph), `${visible.nodes.length} / ${graph.nodes.length} nodi`].filter(Boolean).join(' · ')}
    actions={<Button variant="ghost" size="sm" disabled={!graph} onClick={() => show(PROVENANCE)}><Icon name="file" />Provenienza e lacune</Button>}>
    {!read ? !serverError && <Column pad="lg"><Loading label="Lettura dello stato del server…" /></Column>
      : !context ? <Empty fill title="Nessun grafo" description="Seleziona prima una repository e un branch."
          action={<Button variant="outline" size="sm" onClick={() => go(() => model.selectStage('repository'))}>Vai al repository</Button>} />
      : <Column fill pad="lg" gap="md" aria-busy={loading || undefined}>
          <Text as="p" variant="soft">Gruppi di file, dipendenze e percorsi del run. Ogni relazione conserva le sue evidenze.</Text>
          {error ? <GraphFailed />
            : !graph || !visible ? <Loading label="Lettura del grafo…" />
            : !graph.nodes.length ? <NoGroups fill />
            : visible.nodes.length ? <Drawing graph={graph} visible={visible} />
            : <Empty fill title="Nessun gruppo trovato" description="Cambia ricerca o amplia il perimetro del grafo."
                action={<Button variant="outline" size="sm" onClick={clear}>Azzera filtri</Button>} />}
        </Column>}
  </ScreenPanel>;
}
