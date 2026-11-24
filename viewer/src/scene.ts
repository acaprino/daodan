// What the canvas draws of the map: its nodes and lines at ELK's places, the choice, the steps of a flow and the key of the lines.
import type { GraphEdge, GraphLegendEntry, GraphNode } from '@acaprino/sigrid/graph';
import type { Flow } from './envelope.ts';
import type { Layout, LayoutGraph } from './layoutClient.ts';
import type { ProjectedEdge, ProjectedNode, Projection } from './projection.ts';
import { iconFor, LINK_LABEL } from './icons.ts';
import { nodeMeta } from './names.ts';

// What is laid out: the nodes in view, the lines on them, and the way their ranks go.
export type Drawing = { projection: Projection; edges: ProjectedEdge[]; direction: 'right' | 'down' };
export type Scene = {
  nodes: GraphNode[]; edges: GraphEdge[]; direction: Drawing['direction']; layoutKey: string; selected: string[];
  steps: ReadonlyMap<string, readonly number[]> | undefined;
  legend: GraphLegendEntry[];
  refs: ReadonlyMap<string, string>;  // node id -> entity ref
};

const SIZE = { width: 224, height: 64 };

// The kinds of line, in the order of their key: a kind has one look, on the canvas and in the key.
const KINDS = ['relation', 'data', 'flow', 'uncertain'] as const;
const LINES: Record<(typeof KINDS)[number], Pick<GraphLegendEntry, 'label' | 'style' | 'tone'>> = {
  relation: { label: 'Relazioni', style: 'solid', tone: 'default' },
  data: { label: 'Collegamenti di dati', style: 'dashed', tone: 'default' },
  flow: { label: 'Linee del flusso', style: 'solid', tone: 'accent' },
  uncertain: { label: 'Prova insufficiente', style: 'dashed', tone: 'warning' },
};
const kindOf = (edge: ProjectedEdge) => (edge.uncertain ? 'uncertain' : edge.flow ? 'flow' : edge.id.startsWith('data:') ? 'data' : 'relation');

// The name of a layout: what it lays out, and which way.
export function layoutKeyOf({ projection, edges, direction }: Drawing): string {
  return `${direction}|${projection.nodes.map(node => node.id).join(',')}|${edges.map(edge => edge.id).join(',')}`;
}

// What ELK is asked to lay out.
export function graphOf({ projection, edges }: Drawing): LayoutGraph {
  return {
    nodes: projection.nodes.map(node => ({ id: node.id, ...SIZE })),
    edges: edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target })),
  };
}

function nodeOf(node: ProjectedNode, layout: Layout): GraphNode {
  return {
    ...SIZE, ...layout.nodes[node.id], id: node.id, label: node.label, icon: iconFor(node) || undefined,
    detail: nodeMeta({ ...node, location: undefined }),  // «esterno» is the canvas's own word
    external: node.location === 'external',
    openLabel: node.collapsed ? `Apri ${node.label}` : undefined, hiddenCount: node.collapsed ? node.count : undefined,
  };
}

// Every line is of the kind the arrows follow (`child`, the canvas's own), with an arrowhead for the way it goes.
function edgeOf(edge: ProjectedEdge, layout: Layout): GraphEdge {
  const { style, tone } = LINES[kindOf(edge)];
  return {
    id: edge.id, from: edge.source, to: edge.target, points: layout.edges[edge.id], directed: true, style, tone,
    label: [edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', '), edge.uncertain ? 'prova insufficiente' : null].filter(Boolean).join(' · '),
    labelShown: edge.flow ? 'always' : 'chosen',
  };
}

// The number of each node of a flow, as the details number the steps: the first step that reaches it from another node, and 1
// where the flow starts. One number each: a node that many steps reach would have no room for its name.
function stepsOf(flow: Flow, owners: Projection['owners']): Map<string, readonly number[]> {
  const steps = new Map<string, readonly number[]>();
  const at = (ref: string) => owners[ref] ?? [];
  for (const id of at(flow.entry)) steps.set(id, [1]);
  flow.steps.forEach((step, index) => {
    const from = at(step.source);
    for (const id of at(step.target)) if (!steps.has(id) && !from.includes(id)) steps.set(id, [index + 1]);
  });
  // Reached from no other node in view: the first step it has a part in.
  for (const id of flow.nodes.flatMap(at)) {
    const first = flow.steps.findIndex(step => at(step.source).includes(id) || at(step.target).includes(id));
    if (first >= 0 && !steps.has(id)) steps.set(id, [first + 1]);
  }
  return steps;
}

// `selected` is an entity: every node that stands for it is chosen.
export function sceneOf(drawing: Drawing, layout: Layout, selected: string | null = null, flow?: Flow): Scene {
  const { projection, edges, direction } = drawing;
  // A flow's lines first: of those between two of its nodes the first is the path's, and the one the arrows follow.
  const ordered = [...edges.filter(edge => edge.flow), ...edges.filter(edge => !edge.flow)];
  const kinds = edges.map(kindOf);
  return {
    nodes: projection.nodes.map(node => nodeOf(node, layout)),
    edges: ordered.map(edge => edgeOf(edge, layout)),
    direction, layoutKey: layoutKeyOf(drawing),
    selected: selected === null ? [] : projection.owners[selected] ?? [],
    steps: flow && stepsOf(flow, projection.owners),
    legend: KINDS.map(kind => ({ ...LINES[kind], count: kinds.filter(item => item === kind).length })).filter(entry => entry.count > 0),
    refs: new Map(projection.nodes.map(node => [node.id, node.ref])),
  };
}
