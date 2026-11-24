// What the canvas draws of the graph of the run: its things, its lines and the key of the lines.
import type { IconName } from '@acaprino/sigrid';
import type { GraphEdge as Line, GraphLegendEntry, GraphNode as Thing } from '@acaprino/sigrid/graph';
import { iconFor } from '../src/icons.ts';
import { nodeFacts, nodeName, proofLabel } from './graph.ts';
import type { Graph, GraphEdge, GraphNode } from './graph.ts';

// `key` is the name of what is laid out: the canvas fits its view again when it changes.
export type Scene = { nodes: Thing[]; edges: Line[]; legend: GraphLegendEntry[]; key: string };

// The kinds of line, in the order of their key: a kind has one look, on the canvas and in the key.
const KINDS = ['relation', 'observed', 'sampled', 'doubtful'] as const;
type Kind = (typeof KINDS)[number];
const LINES: Record<Kind, Pick<GraphLegendEntry, 'label' | 'style' | 'tone'>> = {
  relation: { label: 'Relazioni', style: 'solid', tone: 'default' },
  observed: { label: 'Osservata in esecuzione', style: 'solid', tone: 'accent' },
  sampled: { label: 'Campionata dal profiler', style: 'dashed', tone: 'accent' },
  doubtful: { label: 'Incerta o in conflitto', style: 'dashed', tone: 'warning' },
};
const kindOf = (edge: GraphEdge): Kind => (edge.conflict || edge.status === 'uncertain' ? 'doubtful'
  : edge.status === 'observed' || edge.status === 'sampled' ? edge.status : 'relation');

// What a thing is, by its kind; a group of any other kind is layers.
export const iconOf = (n: GraphNode): IconName =>
  iconFor({ nodeType: n.node_type ?? undefined, type: n.location === 'external' ? 'external' : n.kind }) || 'layers';

function thingOf(n: GraphNode): Thing {
  const external = n.location === 'external';
  // «esterno» is the canvas's own word.
  return { id: n.id, label: nodeName(n), icon: iconOf(n), external, detail: external ? n.node_type || undefined : nodeFacts(n) };
}

// Each relation is a line of its own, also between the same two things. Its words are drawn on a choice, and always heard.
function lineOf(edge: GraphEdge, index: number): Line {
  const { style, tone } = LINES[kindOf(edge)];
  const counts = Object.entries(edge.counts).map(([kind, count]) => `${kind}: ${count}`).join(', ');
  return {
    id: String(index), from: edge.source, to: edge.target, directed: true, style, tone,
    label: [counts, proofLabel(edge.status, edge.conflict)].filter(Boolean).join(' · '), labelShown: 'chosen',
  };
}

export function sceneOf({ nodes, edges }: Pick<Graph, 'nodes' | 'edges'>): Scene {
  const kinds = edges.map(kindOf);
  return {
    nodes: nodes.map(thingOf), edges: edges.map(lineOf),
    legend: KINDS.map(kind => ({ ...LINES[kind], count: kinds.filter(item => item === kind).length })).filter(entry => entry.count > 0),
    key: `${nodes.map(n => n.id).join(',')}|${edges.map(edge => `${edge.source}→${edge.target}`).join(',')}`,
  };
}
