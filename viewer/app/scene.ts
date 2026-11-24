// What the canvas draws of the graph of the run: its things, the groups open in place around what they hold, its lines and the key of
// the lines.
import type { IconName } from '@acaprino/sigrid/primitives';
import type { GraphEdge as Line, GraphLegendEntry, GraphNode as Drawn } from '@acaprino/sigrid/graph';
import { iconFor } from '../src/icons.ts';
import { legendOf, LINES } from '../src/lines.ts';
import type { LineKind } from '../src/lines.ts';
import type { ImageOf } from '../src/scene.ts';
import { isOpenGroup, markOf, nodeFacts, nodeName, opens, outside, relationWords } from './graph.ts';
import type { Graph, GraphEdge, GraphNode, OpenGroup, Thing } from './graph.ts';

// `key` is the name of what is laid out: the canvas fits its view again when it changes.
export type Scene = { nodes: Drawn[]; edges: Line[]; legend: GraphLegendEntry[]; key: string };

const kindOf = (edge: GraphEdge): LineKind => (edge.conflict || edge.status === 'uncertain' ? 'uncertain'
  : edge.status === 'observed' || edge.status === 'sampled' ? edge.status : 'relation');

// What a thing is, by its kind; a group of any other kind is layers.
export const iconOf = (thing: Pick<OpenGroup, 'kind'> & Partial<Pick<GraphNode, 'location' | 'node_type'>>): IconName =>
  iconFor({ nodeType: thing.node_type ?? undefined, type: thing.location === 'external' ? 'external' : thing.kind ?? '' }) || 'layers';

// The order the arrows go through: the project before what is outside it, by name, and an open group before what it holds.
function inOrder(nodes: readonly GraphNode[], open: readonly OpenGroup[]): Thing[] {
  const groups = new Set(open.map(group => group.id)), held = new Map<string | null, Thing[]>();
  for (const thing of [...nodes, ...open]) {
    const holder = isOpenGroup(thing) ? thing.parent : thing.group;
    const place = holder !== null && groups.has(holder) ? holder : null, beside = held.get(place);
    if (beside) beside.push(thing);
    else held.set(place, [thing]);
  }
  const far = (thing: Thing) => (isOpenGroup(thing) ? 0 : outside(thing));
  const within = (place: string | null): Thing[] => (held.get(place) ?? []).sort((a, b) => far(a) - far(b) || a.name.localeCompare(b.name, 'it'))
    .flatMap(thing => (isOpenGroup(thing) ? [thing, ...within(thing.id)] : [thing]));
  return within(null);
}

function drawn(thing: Thing, imageOf: ImageOf): Drawn {
  const face = { id: thing.id, label: nodeName(thing), icon: iconOf(thing), image: imageOf(markOf(thing)) };
  if (isOpenGroup(thing)) return { ...face, open: true, group: thing.parent ?? undefined };
  const external = thing.location === 'external';
  return {
    ...face,
    external, detail: external ? thing.node_type || undefined : nodeFacts(thing),  // «esterno» is the canvas's own word
    open: opens(thing) ? false : undefined, group: thing.group ?? undefined,
  };
}

// Each relation is a line of its own, also between the same two things. Its words are drawn on a choice, and always heard.
function lineOf(edge: GraphEdge, index: number): Line {
  const { style, tone } = LINES[kindOf(edge)];
  return { id: String(index), from: edge.source, to: edge.target, directed: true, style, tone, label: relationWords(edge), labelShown: 'chosen' };
}

export function sceneOf({ nodes, edges, open = [] }: Pick<Graph, 'nodes' | 'edges'> & Partial<Pick<Graph, 'open'>>, imageOf: ImageOf): Scene {
  const things = inOrder(nodes, open);
  return {
    nodes: things.map(thing => drawn(thing, imageOf)), edges: edges.map(lineOf),
    legend: legendOf(edges.map(kindOf)),
    key: `${things.map(thing => (isOpenGroup(thing) ? `+${thing.id}` : thing.id)).join(',')}|${edges.map(edge => `${edge.source}→${edge.target}`).join(',')}`,
  };
}
