// What the canvas draws of the graph of the run: its things, the groups open in place around what they hold, its lines and the key of
// the lines.
import type { IconName } from '@acaprino/sigrid/primitives';
import type { GraphEdge as Line, GraphLegendEntry, GraphNode as Drawn } from '@acaprino/sigrid/graph';
import { iconFor } from '../src/icons.ts';
import { isOpenGroup, nodeFacts, nodeName, opens, outside, relationWords } from './graph.ts';
import type { Graph, GraphEdge, GraphNode, OpenGroup, Thing } from './graph.ts';

// `key` is the name of what is laid out: the canvas fits its view again when it changes.
export type Scene = { nodes: Drawn[]; edges: Line[]; legend: GraphLegendEntry[]; key: string };

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

function drawn(thing: Thing, imageOf: (mark: string) => string): Drawn {
  if (isOpenGroup(thing)) return { id: thing.id, label: nodeName(thing), icon: iconOf(thing), open: true, group: thing.parent ?? undefined };
  const external = thing.location === 'external';
  return {
    id: thing.id, label: nodeName(thing), icon: iconOf(thing), image: thing.mark ? imageOf(thing.mark) : undefined,
    external, detail: external ? thing.node_type || undefined : nodeFacts(thing),  // «esterno» is the canvas's own word
    open: opens(thing) ? false : undefined, group: thing.group ?? undefined,
  };
}

// Each relation is a line of its own, also between the same two things. Its words are drawn on a choice, and always heard.
function lineOf(edge: GraphEdge, index: number): Line {
  const { style, tone } = LINES[kindOf(edge)];
  return { id: String(index), from: edge.source, to: edge.target, directed: true, style, tone, label: relationWords(edge), labelShown: 'chosen' };
}

// `imageOf`: the address of the logo of a thing that has one.
export function sceneOf({ nodes, edges, open = [] }: Pick<Graph, 'nodes' | 'edges'> & Partial<Pick<Graph, 'open'>>, imageOf: (mark: string) => string): Scene {
  const things = inOrder(nodes, open), kinds = edges.map(kindOf);
  return {
    nodes: things.map(thing => drawn(thing, imageOf)), edges: edges.map(lineOf),
    legend: KINDS.map(kind => ({ ...LINES[kind], count: kinds.filter(item => item === kind).length })).filter(entry => entry.count > 0),
    key: `${things.map(thing => (isOpenGroup(thing) ? `+${thing.id}` : thing.id)).join(',')}|${edges.map(edge => `${edge.source}→${edge.target}`).join(',')}`,
  };
}
