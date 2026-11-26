// What the canvas draws of the map: its nodes and lines at ELK's places, the open groups and what they hold, the choice, the steps
// of a flow and the key of the lines.
import type { GraphEdge, GraphLegendEntry, GraphNode } from '@acaprino/sigrid/graph';
import type { Flow } from './envelope.ts';
import type { Layout, LayoutGraph } from './layoutClient.ts';
import { legendOf, LINES } from './lines.ts';
import type { LineKind } from './lines.ts';
import type { ProjectedEdge, ProjectedNode, Projection } from './projection.ts';
import { iconFor } from './icons.ts';
import { nodeMeta } from './names.ts';
import { LINK_LABEL } from './words.ts';

// What is laid out: the nodes in view, the lines on them, and the way their ranks go; with the flow that is followed on them.
export type Drawing = { projection: Projection; edges: ProjectedEdge[]; direction: 'right' | 'down'; flow?: Flow };
export type Scene = {
  nodes: GraphNode[]; edges: GraphEdge[]; direction: Drawing['direction']; layoutKey: string;
  steps: ReadonlyMap<string, readonly number[]> | undefined;
  legend: GraphLegendEntry[];
  refs: ReadonlyMap<string, string>;  // node id -> entity ref
};

// The address of the logo of a thing, where it has one.
export type ImageOf = (mark: string | undefined) => string | undefined;

// Wide enough for the name of a group beside its count, its steps and its two arrows.
const SIZE = { width: 256, height: 64 };

const kindOf = (edge: ProjectedEdge): LineKind => (edge.uncertain ? 'uncertain' : edge.flow ? 'flow' : edge.id.startsWith('data:') ? 'data' : 'relation');

// The name of a layout: what it lays out, which groups are open, and which way. A group whose things are all hidden has the nodes of
// a closed one, and is drawn open.
export function layoutKeyOf({ projection, edges, direction }: Drawing): string {
  return `${direction}|${projection.nodes.map(node => (node.open ? `${node.id} open` : node.id)).join(',')}|${edges.map(edge => edge.id).join(',')}`;
}

// What ELK is asked to lay out.
export function graphOf({ projection, edges }: Drawing): LayoutGraph {
  return {
    nodes: projection.nodes.map(node => ({ id: node.id, ...SIZE, parent: node.parent ?? undefined })),
    edges: edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target })),
  };
}

// A closed group has the two ways in: its arrow opens it in place (`open`, the canvas's «Apri»), and a double press, or the → beside
// it, goes into it. An open one is closed by its arrow; the way into it is the «Entra» of the details, of its row or of the palette.
function nodeOf(node: ProjectedNode, layout: Layout, imageOf: ImageOf): GraphNode {
  const closed = node.open === false;
  return {
    ...SIZE, ...layout.nodes[node.id], id: node.id, label: node.label, icon: iconFor(node) || undefined, image: imageOf(node.mark),
    detail: nodeMeta({ ...node, location: undefined }),  // «esterno» is the canvas's own word
    external: node.location === 'external',
    open: node.open, group: node.parent ?? undefined,
    openLabel: closed ? `Entra in ${node.label}` : undefined, hiddenCount: closed ? node.count : undefined,
  };
}

// Every line is of the kind the arrows follow (`child`, the canvas's own), with an arrowhead for the way it goes. A flow's lines, and
// no other, are its path.
function edgeOf(edge: ProjectedEdge, layout: Layout): GraphEdge {
  const { style, tone } = LINES[kindOf(edge)];
  return {
    id: edge.id, from: edge.source, to: edge.target, points: layout.edges[edge.id], directed: true, style, tone, path: edge.flow === true,
    label: [edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', '), edge.uncertain ? 'prova insufficiente' : null].filter(Boolean).join(' · '),
    labelShown: edge.flow ? 'always' : 'chosen',
  };
}

// The numbers of each node of a flow, as the details number the steps: every step it has a part in, from or to it. Where the flow
// starts is 1, also with no step from there.
function stepsOf(flow: Flow, owners: Projection['owners']): Map<string, readonly number[]> {
  const steps = new Map<string, number[]>();
  const add = (ref: string, step: number) => {
    for (const id of owners[ref] ?? []) {
      const numbers = steps.get(id) ?? [];
      if (!numbers.includes(step)) steps.set(id, [...numbers, step]);
    }
  };
  flow.steps.forEach((step, index) => { add(step.source, index + 1); add(step.target, index + 1); });
  for (const id of owners[flow.entry] ?? []) if (!steps.has(id)) steps.set(id, [1]);
  return steps;
}

// The nodes that stand for what is chosen: an entity may be in several places.
export const chosenIn = (projection: Projection, selected: string | null): string[] => (selected === null ? [] : projection.owners[selected] ?? []);

// Without the choice, which changes nothing of it: choosing draws again only what is chosen and what was.
export function sceneOf(drawing: Drawing, layout: Layout, imageOf: ImageOf = () => undefined): Scene {
  const { projection, edges, direction, flow } = drawing;
  // A flow's lines first: of the lines of a node the arrows follow the first.
  const ordered = [...edges.filter(edge => edge.flow), ...edges.filter(edge => !edge.flow)];
  return {
    nodes: projection.nodes.map(node => nodeOf(node, layout, imageOf)),
    edges: ordered.map(edge => edgeOf(edge, layout)),
    direction, layoutKey: layoutKeyOf(drawing),
    steps: flow && stepsOf(flow, projection.owners),
    legend: legendOf(edges.map(kindOf)),
    refs: new Map(projection.nodes.map(node => [node.id, node.ref])),
  };
}
