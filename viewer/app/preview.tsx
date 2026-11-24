// The graph as it takes shape: its groups and relations on the canvas, which lays them out, and the details of the one chosen.
import { useMemo } from 'react';
import { Badge, Button, Column, Empty, Icon, Section, Split, Text, useMedia } from '@acaprino/sigrid';
import { GraphCanvas, GraphLegend } from '@acaprino/sigrid/graph';
import { useFrame } from './frame.tsx';
import type { Detail } from './frame.tsx';
import { buildCounts, levelLabel, levelsName, nodeFacts, nodeName, responsibilityOf } from './graph.ts';
import type { Graph } from './graph.ts';
import { short } from './repository.ts';
import { buildStatus } from './run.ts';
import { sceneOf } from './scene.ts';
import { ctx } from './snapshot.ts';
import { GraphFailed, Loading } from './states.tsx';
import { model, useModel } from './use-model.ts';

// The details of a node say which one they are of, so the canvas marks it as long as they are shown.
type NodeDetail = Detail & { node: string };
const nodeShown = (detail: Detail | null) => (detail as Partial<NodeDetail> | null)?.node ?? null;

function NodeFacts({ id }: { id: string }) {
  const s = useModel();
  const c = ctx(s), n = s.graph?.nodes.find(item => item.id === id);
  if (!c || !n) return <Text as="p" variant="muted">Non è più nel grafo di questo run.</Text>;
  return <Column>
    <Text as="p" variant="muted">{s.graph?.grouping === 'modules' ? 'Modulo' : 'Directory'} del grafo di questo run.</Text>
    <Text as="p">{responsibilityOf(n)}</Text>
    <Text as="p" variant="note">{nodeFacts(n)} · commit {short(c.commit)}</Text>
  </Column>;
}

function Drawing({ graph }: { graph: Graph }) {
  const { detail, show, close } = useFrame();
  const direction = useMedia('(width < 850px)') ? 'down' : 'right';
  const scene = useMemo(() => sceneOf(graph), [graph]);  // an event changes the snapshot, not the graph: nothing is laid out again
  const selected = nodeShown(detail);
  const choose = (id: string | null) => {
    const n = graph.nodes.find(item => item.id === id);
    if (!n) { if (selected !== null) close(); return; }
    const chosen: NodeDetail = {
      node: n.id, title: nodeName(n), content: <NodeFacts id={n.id} />,
      footer: <Button variant="outline" size="sm" onClick={() => { close(); model.showNode(n.id); }}><Icon name="graph" />Apri nel grafo</Button>,
    };
    show(chosen);
  };
  return <>
    <GraphCanvas aria-label="Costruzione del grafo" model="graph" nodes={scene.nodes} edges={scene.edges} direction={direction}
      layoutKey={`${direction}|${scene.key}`} selected={selected} onSelect={choose} />
    <GraphLegend aria-label="Tipi di linea" entries={scene.legend} />
  </>;
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
      : <Empty title="Prima l’inventario, poi le relazioni."
          description="Il grafo del run non ha ancora gruppi di file. I nodi compaiono quando la pipeline scrive un artefatto." />}
    <Split>
      <Text variant="note">{buildCounts(graph)}</Text>
      <Text variant="note">{buildStatus(s)}</Text>
    </Split>
  </Section>;
}
