// What one view of the envelope shows: nodes with their occurrences, edges lifted to what is visible, flows on top.
import type { Entity, Envelope, Flow, View } from './envelope.ts';

export type Filters = { text?: string; types?: string[]; kinds?: string[]; status?: string[] };
export type ProjectedNode = {
  id: string; ref: string; type: string; label: string; parent: string | null; collapsed: boolean; count: number;
  nodeType?: string; location?: string; status?: string; freshness?: string; provenance?: string;
};
export type ProjectedEdge = { id: string; source: string; target: string; relations: string[]; kinds: string[]; flow?: boolean; label?: string };
export type Projection = {
  nodes: ProjectedNode[]; edges: ProjectedEdge[];
  counts: { filtered: number; aggregated: number; unloaded: number; files: number };
  owners: Record<string, string[]>;  // entity ref -> the visible nodes that stand for it
};

const STRUCTURE = new Set(['contains', 'defines']);

export type Index = {
  byRef: Map<string, Entity>;
  members: Record<View, Map<string, string[]>>;
  groups: Record<View, Map<string, string[]>>;
  symbols: Map<string, string[]>;
};

const indexes = new WeakMap<Envelope, Index>();

export function indexOf(env: Envelope): Index {
  const found = indexes.get(env);
  if (found) return found;
  const index: Index = {
    byRef: new Map(env.entities.map(entity => [entity.ref, entity])),
    members: { logical: new Map(), physical: new Map() }, groups: { logical: new Map(), physical: new Map() },
    symbols: new Map(),
  };
  const push = (map: Map<string, string[]>, key: string, value: string) => {
    const list = map.get(key) ?? [];
    if (!list.includes(value)) list.push(value);
    map.set(key, list);
  };
  for (const item of env.memberships) {
    // A feature cuts across components: a highlight of the logical view, never a container.
    if (item.view === 'logical' && index.byRef.get(item.group)?.type === 'feature') continue;
    push(index.members[item.view], item.group, item.member);
    push(index.groups[item.view], item.member, item.group);
  }
  for (const relation of env.relations) if (relation.kind === 'defines') push(index.symbols, relation.source, relation.target);
  indexes.set(env, index);
  return index;
}

export function childrenOf(env: Envelope, ref: string, view: View): string[] {
  const index = indexOf(env);
  if (index.byRef.get(ref)?.type === 'file') return index.symbols.get(ref) ?? [];
  return index.members[view].get(ref) ?? [];
}

export function rootsOf(env: Envelope, view: View): string[] {
  const index = indexOf(env);
  if (view === 'logical') return env.entities.filter(e => ['component', 'external', 'store'].includes(e.type)).map(e => e.ref);
  const groups = [...index.members.physical.keys()].filter(group => !index.groups.physical.has(group));
  const loose = env.entities.filter(e => e.type === 'file' && !index.groups.physical.has(e.ref)).map(e => e.ref);
  return [...groups, ...loose];
}

function descendants(env: Envelope, ref: string, view: View, seen = new Set<string>()): Set<string> {
  if (seen.has(ref)) return seen;
  seen.add(ref);
  for (const child of childrenOf(env, ref, view)) descendants(env, child, view, seen);
  return seen;
}

// Whether a ref has a place in the view: a node of its tree, or something one of its nodes holds.
export function resolves(env: Envelope, ref: string, view: View): boolean {
  return rootsOf(env, view).some(root => descendants(env, root, view).has(ref));
}

function matches(entity: Entity, filters: Filters): boolean {
  const text = filters.text?.trim().toLocaleLowerCase();
  if (text && !`${entity.name} ${entity.technical}`.toLocaleLowerCase().includes(text)) return false;
  if (filters.types?.length && !filters.types.includes(entity.type)) return false;
  if (filters.status?.length && !filters.status.some(state => state === entity.status || state === entity.freshness)) return false;
  return true;
}

export function project(env: Envelope, view: View, scope: string | null, filters: Filters = {},
  open: string[] = [], selected: string | null = null): Projection {
  const index = indexOf(env);
  const nodes: ProjectedNode[] = [];
  const stands = new Map<string, Set<string>>();  // node id -> refs it stands for
  let filtered = 0;
  const visit = (ref: string, parent: string | null, container: string) => {
    const entity = index.byRef.get(ref);
    if (!entity) return;
    const id = `${ref}@${container}`;
    const kids = childrenOf(env, ref, view);
    const expanded = kids.length > 0 && open.includes(ref);
    if (!matches(entity, filters) && ref !== selected) { filtered += 1; return; }
    nodes.push({
      id, ref, type: entity.type, label: entity.name, parent, collapsed: kids.length > 0 && !expanded,
      count: new Set(kids).size, nodeType: entity.node_type, location: entity.location, status: entity.status,
      freshness: entity.freshness, provenance: entity.provenance,
    });
    stands.set(id, expanded ? new Set([ref]) : descendants(env, ref, view));
    if (expanded) for (const kid of kids) visit(kid, id, id);
  };
  const top = scope === null ? rootsOf(env, view) : childrenOf(env, scope, view);
  for (const ref of top) visit(ref, null, scope ?? 'root');

  const owners: Record<string, string[]> = {};
  for (const [id, refs] of stands) for (const ref of refs) (owners[ref] ??= []).push(id);
  const edges = new Map<string, ProjectedEdge>();
  let aggregated = 0, unloaded = 0;
  for (const relation of env.relations) {
    if (STRUCTURE.has(relation.kind)) continue;
    if (filters.kinds?.length && !filters.kinds.includes(relation.kind)) continue;
    const sources = owners[relation.source] ?? [], targets = owners[relation.target] ?? [];
    if (!sources.length || !targets.length) { unloaded += 1; continue; }
    for (const source of sources) for (const target of targets) {
      if (source === target) { aggregated += 1; continue; }
      const id = `${source}->${target}`;
      const edge = edges.get(id) ?? { id, source, target, relations: [], kinds: [] };
      edge.relations.push(relation.ref);
      if (!edge.kinds.includes(relation.kind)) edge.kinds.push(relation.kind);
      edges.set(id, edge);
    }
  }
  const files = new Set(nodes.flatMap(node => [...(stands.get(node.id) ?? [])]).filter(ref => index.byRef.get(ref)?.type === 'file'));
  return { nodes, edges: [...edges.values()], counts: { filtered, aggregated, unloaded, files: files.size }, owners };
}

// A flow seen on the current projection: the visible nodes that stand for its nodes, and its steps between them.
export function flowFocus(env: Envelope, flowRef: string, projection: Projection): { nodes: string[]; edges: ProjectedEdge[] } {
  const flow = env.flows.find(item => item.ref === flowRef);
  if (!flow) return { nodes: [], edges: [] };
  const lift = (ref: string) => projection.owners[ref] ?? [];
  const nodes = [...new Set(flow.nodes.flatMap(lift))];
  const edges = new Map<string, ProjectedEdge>();
  for (const step of flow.steps) for (const source of lift(step.source)) for (const target of lift(step.target)) {
    if (source === target) continue;
    const id = `flow:${source}->${target}`;
    const edge = edges.get(id) ?? { id, source, target, relations: [], kinds: [], flow: true, label: step.type };
    if (!edge.kinds.includes(step.type)) edge.kinds.push(step.type);
    edges.set(id, edge);
  }
  return { nodes, edges: [...edges.values()] };
}

// The flows a node takes part in: its own ref, or anything it holds in the view.
export function flowsThrough(env: Envelope, ref: string, view: View): Flow[] {
  const held = descendants(env, ref, view);
  return env.flows.filter(flow => flow.nodes.some(node => held.has(node)));
}
