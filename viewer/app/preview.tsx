// The graph as it takes shape: its groups and relations on the canvas, which lays them out, and the details of the one chosen.
import { memo, useCallback, useMemo } from 'react';
import { Badge, Button, Icon, Section, Split, Text } from '@acaprino/sigrid/primitives';
import { useMedia } from '@acaprino/sigrid';
import { GraphCanvas, GraphLegend } from '@acaprino/sigrid/graph';
import { Loading } from '../src/states.tsx';
import { useFrame } from './frame.tsx';
import { buildCounts, levelLabel, levelsName } from './graph.ts';
import type { Graph } from './graph.ts';
import { groupDetail, groupOf } from './group-details.tsx';
import { buildStatus } from './notices.ts';
import { sceneOf } from './scene.ts';
import { GraphFailed, NoGroups } from './states.tsx';
import { model, useModel } from './use-model.ts';

// Drawn again when the graph or the choice is another: an event of the run, which draws the screen again, does not touch the canvas.
const Canvas = memo(function Canvas({ graph, selected, onSelect }: { graph: Graph; selected: string | null; onSelect: (id: string | null) => void }) {
  const direction = useMedia('(width < 850px)') ? 'down' : 'right';
  const scene = useMemo(() => sceneOf(graph, model.markUrl), [graph]);
  return <>
    <GraphCanvas aria-label="Costruzione del grafo" model="graph" nodes={scene.nodes} edges={scene.edges} direction={direction}
      layoutKey={`${direction}|${scene.key}`} selected={selected} onSelect={onSelect} />
    <GraphLegend aria-label="Tipi di linea" entries={scene.legend} />
  </>;
});

function Drawing({ graph }: { graph: Graph }) {
  const { detail, show, close, go } = useFrame();
  const selected = groupOf(detail);
  const choose = useCallback((id: string | null) => {
    const n = graph.nodes.find(item => item.id === id);
    if (n) show(groupDetail(n, <Button variant="outline" size="sm" onClick={() => go(() => model.showNode(n.id))}><Icon name="graph" />Apri nel grafo</Button>));
    else if (selected !== null) close();
  }, [graph, selected, show, close, go]);
  return <Canvas graph={graph} selected={selected} onSelect={choose} />;
}

export function Preview() {
  const s = useModel();
  const graph = s.graph;
  return <Section title="Costruzione del grafo" level={3} icon={<Icon name="graph" />} gap="md"
    end={<Badge variant="secondary">{levelsName(graph) || levelLabel(graph)}</Badge>}>
    <Text as="p" variant="muted">Gruppi di file e relazioni dal grafo del run.</Text>
    {s.graphError ? <GraphFailed />
      : !graph ? <Loading label="Lettura del grafo…" />
      : graph.nodes.length ? <Drawing graph={graph} />
      : <NoGroups />}
    <Split>
      <Text variant="note">{buildCounts(graph)}</Text>
      <Text variant="note">{buildStatus(s)}</Text>
    </Split>
  </Section>;
}
