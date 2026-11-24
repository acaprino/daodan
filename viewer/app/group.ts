// The details of a group of the graph, in words: what it is, its relations and what proves them, its files and its symbols.
import { FRESHNESS_LABEL } from '../src/icons.ts';
import { endName, isOpenGroup, nodeState, proofLabel, relationWords } from './graph.ts';
import type { Evidence, Graph, GraphEdge, Thing } from './graph.ts';
import { number } from './snapshot.ts';
import type { Symbols } from './snapshot.ts';

export type Row = { name: string; about: string };  // a line of a list, and the note under it

const KIND: Record<string, string> = { directory: 'Directory selezionata', file: 'File selezionato', symbol: 'Simbolo selezionato' };
export const whatIs = (thing: Thing) =>
  (!isOpenGroup(thing) && thing.location === 'external' ? 'Nodo esterno selezionato' : KIND[thing.kind ?? ''] ?? 'Modulo selezionato');
export function stateOf(thing: Thing): string {
  if (isOpenGroup(thing)) return 'aperto sul posto';
  return thing.location === 'external' ? ['Dipendenza esterna', thing.node_type].filter(Boolean).join(' · ') : nodeState(thing);
}

export const relationsOf = (graph: Graph, id: string) => graph.edges.filter(edge => edge.source === id || edge.target === id);
export const isProven = (edge: Pick<GraphEdge, 'status' | 'conflict'>) =>
  Boolean(edge.conflict) || edge.status === 'observed' || edge.status === 'sampled';

const span = (lines?: readonly (number | null)[] | null) => (lines ?? []).filter(Boolean).join('–');
export const siteOf = (at: Evidence) => `${at.path}${at.line ? `:${at.line}` : ''}`;
export const shortPath = (path: string) => path.split('/').slice(-2).join('/');

const ORIGIN: Record<string, string> = { directory: 'Directory del checkout', file: 'File del checkout', symbol: 'Outline del file' };
export function perimeter(graph: Graph, thing: Thing): { name: string; value: string }[] {
  const fact = (name: string, count: number) => ({ name, value: number(count) });
  const relations = fact('Relazioni nel grafo', relationsOf(graph, thing.id).length);
  if (isOpenGroup(thing)) {
    const held = graph.nodes.filter(n => n.group === thing.id).length + graph.open.filter(group => group.parent === thing.id).length;
    return [fact('Elementi dentro', held), relations];
  }
  const size = thing.kind !== 'symbol' ? [fact('File assegnati', thing.files.length)]
    : [{ name: 'Righe', value: span(thing.lines) || '—' }, ...(thing.members ? [fact('Simboli dentro', thing.members.length)] : [])];
  return [...size, relations, { name: 'Provenienza', value: thing.provenance || ORIGIN[thing.kind] || 'Non registrata' }];
}

// A relation, from where the group is.
export function relationRow(graph: Graph, id: string, edge: GraphEdge): Row {
  const name = edge.source === id ? `→ ${endName(graph, edge.target)}` : `← ${endName(graph, edge.source)}`;
  return { name, about: relationWords(edge) };
}
const ends = (graph: Graph, edge: GraphEdge) => `${endName(graph, edge.source)} → ${endName(graph, edge.target)}`;
export const proofRow = (graph: Graph, edge: GraphEdge): Row =>
  ({ name: [ends(graph, edge), proofLabel(edge.status, edge.conflict)].join(' · '), about: '' });

// The relations between groups whose evidence is in a file, or names it.
export function recordedIn(graph: Graph, path: string): Row[] {
  return graph.edges.flatMap(edge => edge.evidence.filter(at => at.path === path || at.target === path).map(at => ({
    name: ends(graph, edge),
    about: [at.kind, at.key, proofLabel(edge.status, edge.conflict), at.line ? `riga ${at.line}` : '', at.path === path ? at.target : '']
      .filter(Boolean).join(' · '),
  })));
}

export const symbolRows = ({ symbols = [] }: Symbols): Row[] => symbols.map(symbol => ({
  name: symbol.name,
  about: [span(symbol.lines) && `righe ${span(symbol.lines)}`, symbol.freshness && (FRESHNESS_LABEL[symbol.freshness] ?? symbol.freshness)]
    .filter(Boolean).join(' · '),
}));
export function callRows({ symbols = [], calls = [] }: Symbols): Row[] {
  const name = (ref: string) => symbols.find(symbol => symbol.id === ref)?.name ?? ref.replace(/^file:/, '');
  const sites = (evidence: Evidence[]) => evidence.map(at => siteOf({ ...at, path: at.path.split('/').pop() ?? at.path })).join(', ');
  return calls.map(call => ({
    name: `${name(call.source)} → ${name(call.target)}`,
    about: [sites(call.evidence), proofLabel(call.status, call.conflict)].filter(Boolean).join(' · '),
  }));
}
