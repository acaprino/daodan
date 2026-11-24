// What one view of the envelope shows: nodes with their occurrences, edges lifted to what is visible, flows on top.
import type { Entity, Envelope, Flow, View } from './envelope.ts';

export type Filters = { text?: string; types?: string[] };
// `parent` is the open group a node is drawn in; `open` says whether a group is (a node that holds nothing is no group).
export type ProjectedNode = {
  id: string; ref: string; type: string; label: string; parent: string | null; open?: boolean; count: number;
  nodeType?: string; location?: string; status?: string; freshness?: string; mark?: string;
};
export type ProjectedEdge = { id: string; source: string; target: string; kinds: string[]; flow?: boolean; uncertain?: boolean };
export type Projection = {
  nodes: ProjectedNode[]; edges: ProjectedEdge[];
  counts: { filtered: number; aggregated: number };  // what the filters hide, and the relations inside one node
  owners: Record<string, string[]>;  // entity ref -> the visible nodes that stand for it
};

const STRUCTURE = new Set(['contains', 'defines']);
const DATA = new Set(['scrive', 'legge', 'usa']);
// The files no component holds stay reachable in the logical view, without an owner invented for them.
export const UNASSIGNED = 'unassigned:logical';

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
  const loose = env.entities.filter(e => e.type === 'file' && !index.groups.logical.has(e.ref)).map(e => e.ref);
  if (loose.length) {
    index.byRef.set(UNASSIGNED, { ref: UNASSIGNED, type: 'group', name: 'Fuori dai componenti', technical: '',
      description: 'File che nessun componente dichiarato o proposto contiene.', evidence: [], gaps: [] });
    index.members.logical.set(UNASSIGNED, loose);
  }
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
  if (view === 'logical') {
    const top = env.entities.filter(e => ['component', 'external', 'store'].includes(e.type)).map(e => e.ref);
    return index.members.logical.has(UNASSIGNED) ? [...top, UNASSIGNED] : top;
  }
  const groups = [...index.members.physical.keys()].filter(group => !index.groups.physical.has(group));
  const loose = env.entities.filter(e => e.type === 'file' && !index.groups.physical.has(e.ref)).map(e => e.ref);
  return [...groups, ...loose];
}

const topOf = (env: Envelope, view: View, scope: string | null) => (scope === null ? rootsOf(env, view) : childrenOf(env, scope, view));

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
  return true;
}

// The choice the filters would hide, which stays in sight, or null: all that a choice changes in the projection.
export function keptBy(env: Envelope, filters: Filters, selected: string | null): string | null {
  const entity = selected === null ? undefined : indexOf(env).byRef.get(selected);
  return entity && !matches(entity, filters) ? selected : null;
}

// `open` are the groups opened in place, wherever each is drawn; `kept` is in sight whatever the filters say.
export function project(env: Envelope, view: View, scope: string | null, filters: Filters = {},
  open: string[] = [], kept: string | null = null): Projection {
  const index = indexOf(env);
  const nodes: ProjectedNode[] = [];
  const stands = new Map<string, Set<string>>();  // node id -> refs it stands for
  let filtered = 0;
  // Whether the node is in sight. An open group the filters would hide stays while something in it does: it is the frame of that.
  // A group inside itself is not opened again.
  const visit = (ref: string, parent: string | null, container: string, inside: string[]): boolean => {
    const entity = index.byRef.get(ref);
    if (!entity) return false;
    const id = `${ref}@${container}`;
    const kids = childrenOf(env, ref, view);
    const expanded = kids.length > 0 && open.includes(ref) && !inside.includes(ref);
    nodes.push({
      id, ref, type: entity.type, label: entity.name, parent, open: kids.length > 0 ? expanded : undefined,
      count: new Set(kids).size, nodeType: entity.node_type, location: entity.location, status: entity.status,
      freshness: entity.freshness, mark: entity.mark,
    });
    let shown = matches(entity, filters) || ref === kept;
    if (expanded) for (const kid of kids) shown = visit(kid, id, id, [...inside, ref]) || shown;
    if (shown) stands.set(id, expanded ? new Set([ref]) : descendants(env, ref, view));
    else { nodes.pop(); filtered += 1; }  // nothing in it is in sight either, so it is the last one
    return shown;
  };
  for (const ref of topOf(env, view, scope)) visit(ref, null, scope ?? 'root', []);

  const owners: Record<string, string[]> = {};
  for (const [id, refs] of stands) for (const ref of refs) (owners[ref] ??= []).push(id);
  const edges = new Map<string, ProjectedEdge>();
  let aggregated = 0;
  for (const relation of env.relations) {
    if (STRUCTURE.has(relation.kind)) continue;
    for (const source of owners[relation.source] ?? []) for (const target of owners[relation.target] ?? []) {
      if (source === target) { aggregated += 1; continue; }
      const uncertain = relation.conflict || relation.status === 'sampled' || relation.status === 'uncertain';
      const id = `${source}->${target}${uncertain ? ' uncertain' : ''}`;
      const edge = edges.get(id) ?? { id, source, target, kinds: [], uncertain };
      if (!edge.kinds.includes(relation.kind)) edge.kinds.push(relation.kind);
      edges.set(id, edge);
    }
  }
  return { nodes, edges: [...edges.values()], counts: { filtered, aggregated }, owners };
}

// The types to choose from: of all the view holds in the scope, whatever the filters hide, and the chosen one with them.
export function typesIn(env: Envelope, view: View, scope: string | null, open: string[] = [], chosen = ''): string[] {
  const index = indexOf(env);
  const types = new Set<string>(chosen ? [chosen] : []);
  const visit = (ref: string, inside: string[]) => {
    const entity = index.byRef.get(ref);
    if (!entity) return;
    types.add(entity.type);
    if (open.includes(ref) && !inside.includes(ref)) for (const kid of childrenOf(env, ref, view)) visit(kid, [...inside, ref]);
  };
  for (const ref of topOf(env, view, scope)) visit(ref, []);
  return [...types].sort();
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
    const uncertain = step.conflict || step.confidence === 'sampled';
    const id = `flow:${source}->${target}${uncertain ? ' uncertain' : ''}`;
    const edge = edges.get(id) ?? { id, source, target, kinds: [], flow: true, uncertain };
    if (!edge.kinds.includes(step.type)) edge.kinds.push(step.type);
    edges.set(id, edge);
  }
  return { nodes, edges: [...edges.values()] };
}

// Who writes, reads or uses a node, over all flows, lifted to the visible nodes: the data links shown at rest.
export function dataLinks(env: Envelope, projection: Projection): ProjectedEdge[] {
  const edges = new Map<string, ProjectedEdge>();
  for (const flow of env.flows) for (const step of flow.steps) {
    if (!DATA.has(step.type)) continue;
    for (const source of projection.owners[step.source] ?? []) for (const target of projection.owners[step.target] ?? []) {
      if (source === target) continue;
      const uncertain = step.conflict || step.confidence === 'sampled';
      const id = `data:${source}->${target}${uncertain ? ' uncertain' : ''}`;
      const edge = edges.get(id) ?? { id, source, target, kinds: [], uncertain };
      if (!edge.kinds.includes(step.type)) edge.kinds.push(step.type);
      edges.set(id, edge);
    }
  }
  return [...edges.values()];
}

// The flows a node takes part in: its own ref, or anything it holds in the view.
export function flowsThrough(env: Envelope, ref: string, view: View): Flow[] {
  const held = descendants(env, ref, view);
  return env.flows.filter(flow => flow.nodes.some(node => held.has(node)));
}
