// The graph of the run: what is in view with the person's filters, its groups open in place, and its words.
import { plural, number } from './snapshot.ts';
import type { Kept } from './storage.ts';

export type Evidence = { path: string; line?: number };
export type EdgeEvidence = Evidence & { target?: string; kind?: string; key?: string };
export type Technology = { mark: string; name: string; category: string; evidence: Evidence[] };
export type GraphNode = {
  id: string; name: string; kind: string; files: string[]; location: string; status?: string; group: string | null; level?: string;
  node_type?: string | null; responsibility?: string; provenance?: string; lines?: number[]; members?: string[]; mark?: string;
  evidence?: Evidence[]; projects?: Technology[]; other_dependencies?: number;
};
export type GraphEdge = { source: string; target: string; counts: Record<string, number>; status?: string; conflict?: boolean; evidence: EdgeEvidence[] };
// A group open in place: `parent` is the open group that holds it, which comes before it.
export type OpenGroup = { id: string; name: string; kind?: string; parent: string | null; projects?: Technology[]; other_dependencies?: number };
export type Graph = {
  grouping: string; nodes: GraphNode[]; open: OpenGroup[]; edges: GraphEdge[]; files: number; levels?: string[];
  gaps?: { reason: string }[]; meta?: { created_at?: string; snapshot_digest?: string }; unassigned: { count: number };
};

// The graph opens its groups in place: the graph screen asks with the groups it holds open, the analysis's preview and the
// synthesis with none. The server keeps each answer until the run's data change.
export const shownOpen = (kept: Kept) => (kept.screen === 'graph' ? [...kept.graphOpen].sort() : []);
export const graphKey = (runId: string | undefined, kept: Kept) => `${runId ?? ''} ${JSON.stringify(shownOpen(kept))}`;

export const outside = (n: { location?: string }) => Number(n.location === 'external');  // a group of the project before an external node
export const opens = (n: GraphNode) => n.files.length > 0 || (n.members ?? []).length > 0;  // files, or the projects or symbols it holds
export const nodeById = (graph: Graph, id: string): GraphNode | undefined => graph.nodes.find(n => n.id === id) ?? graph.nodes[0];

// The groups left open when `id` closes: those open inside it close too.
export function openWithout(graphOpen: string[], graph: Graph | null, id: string): string[] {
  const gone = new Set([id]);
  for (const group of graph?.open ?? []) if (group.parent !== null && gone.has(group.parent)) gone.add(group.id);
  return graphOpen.filter(item => !gone.has(item));
}

// The node the graph is read from when the one kept is not in it: the one with most relations, inside a group just opened first.
export function rootOf(graph: Graph, kept: string): string {
  if (graph.nodes.some(n => n.id === kept)) return kept;
  const related = (id: string) => graph.edges.filter(e => e.source === id || e.target === id).length;
  const inside = graph.nodes.filter(n => n.group === kept);
  return [...(inside.length ? inside : graph.nodes)].sort((a, b) =>
    outside(a) - outside(b) || related(b.id) - related(a.id) || b.files.length - a.files.length)[0]?.id ?? '';
}

type Filters = Pick<Kept, 'graphSearch' | 'graphRoot' | 'graphDirection' | 'graphDepth' | 'graphKind'>;
export function visibleGraph(graph: Graph, kept: Filters): { nodes: GraphNode[]; edges: GraphEdge[] } {
  let nodes = graph.nodes;
  const edges = graph.edges.filter(e => kept.graphKind === 'all' || (e.counts[kept.graphKind] || 0) > 0);
  const start = nodeById(graph, kept.graphRoot);
  if (kept.graphDepth !== 'all' && start) {
    const found = new Set([start.id]);
    let frontier = [start.id];
    for (let d = 0; d < Number(kept.graphDepth); d++) {
      const next: string[] = [];
      for (const id of frontier) for (const e of edges) {
        if (kept.graphDirection !== 'in' && e.source === id && !found.has(e.target)) { found.add(e.target); next.push(e.target); }
        if (kept.graphDirection !== 'out' && e.target === id && !found.has(e.source)) { found.add(e.source); next.push(e.source); }
      }
      frontier = next;
    }
    nodes = nodes.filter(n => found.has(n.id));
  }
  const query = kept.graphSearch.trim().toLowerCase();
  if (query) nodes = nodes.filter(n => [n.name, n.id, n.responsibility, ...n.files].join(' ').toLowerCase().includes(query));
  const ids = new Set([...nodes.map(n => n.id), ...graph.open.map(group => group.id)]);  // an open group holds the arrows of its own
  return { nodes, edges: edges.filter(e => ids.has(e.source) && ids.has(e.target)) };
}

export const nodeName = (n: { kind?: string; name: string }) => (n.kind === 'directory' && n.name === '.' ? 'radice del repository' : n.name);
const NODE_STATUS: Record<string, string> = { confirmed: 'confermato', inferred: 'inferito', incomplete: 'incompleto', proposed: 'proposto' };
export const nodeState = (n: GraphNode) => (n.location === 'external' ? 'esterno' : NODE_STATUS[n.status ?? ''] || n.status || 'senza stato');
export function nodeFacts(n: GraphNode): string {
  if (n.location === 'external') return [n.node_type, 'esterno'].filter(Boolean).join(' · ');
  return n.kind === 'symbol' ? ['righe ' + (n.lines ?? []).join('–'), n.members ? `${n.members.length} simboli` : '', n.node_type].filter(Boolean).join(' · ')
    : `${n.files.length} file · ${nodeState(n)}`;
}
export const responsibilityOf = (n: GraphNode) => n.responsibility || 'Responsabilità non descritta nel grafo.';
// The name of a node or of an open group, for a line that ends on either.
export function endName(graph: Graph, id: string): string {
  const n = graph.nodes.find(item => item.id === id);
  return n ? nodeName(n) : graph.open.find(group => group.id === id)?.name || id;
}
export const levelLabel = (graph: Graph | null) => (graph?.grouping === 'modules' ? 'Moduli' : 'Directory');
// The levels of the system map the graph shows, by their own names.
export const levelsName = (graph: Graph | null) => (graph?.levels ?? []).map(level => level[0].toUpperCase() + level.slice(1)).join(' · ');

const PROOF: Record<string, string> = { observed: 'osservata in esecuzione', sampled: 'campionata dal profiler', uncertain: 'incerta' };
export const proofLabel = (status: string | undefined, conflict = false) =>
  [PROOF[status ?? ''] ?? '', conflict && 'destinazioni in conflitto'].filter(Boolean).join(' · ');
export function runtimeSummary(edges: readonly Pick<GraphEdge, 'status' | 'conflict'>[]): string {
  const observed = edges.filter(e => !e.conflict && e.status === 'observed').length;
  const sampled = edges.filter(e => !e.conflict && e.status === 'sampled').length;
  const conflicts = edges.filter(e => e.conflict).length;
  return [observed && plural(observed, 'osservata in esecuzione', 'osservate in esecuzione'),
    sampled && plural(sampled, 'campionata dal profiler', 'campionate dal profiler'),
    conflicts && plural(conflicts, 'in conflitto', 'in conflitto')].filter(Boolean).join(' · ');
}
export const buildCounts = (graph: Graph | null) => (graph
  ? `${graph.nodes.length} ${graph.grouping === 'modules' ? 'moduli' : 'directory'} · ${graph.edges.length} relazioni · ${number(graph.files)} file` : '—');
