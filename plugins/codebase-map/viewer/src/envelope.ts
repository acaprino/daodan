// The export the viewer draws (`daodan/visual@1`, written by visual.py). Nothing is inferred here.

export const SCHEMA = 'daodan/visual@1';
export const NODE_TYPES = ['attore', 'schermata', 'funzionalità', 'servizio o API', 'gateway', 'database', 'coda',
  'autenticazione', 'dispositivo', 'altro'] as const;

export type Evidence = { path?: string | null; line?: number | null };
export type Entity = {
  ref: string; type: string; name: string; technical: string; description: string;
  provenance?: string; status?: string; freshness?: string; path?: string; lines?: number | number[];
  address?: string; location?: 'internal' | 'external'; node_type?: string; evidence: Evidence[]; gaps: unknown[];
};
export type Relation = {
  ref: string; kind: string; source: string; target: string; status: string;
  counts?: Record<string, number>; evidence: Evidence[];
};
export type View = 'logical' | 'physical';
export type Membership = { member: string; group: string; view: View };
export type FlowStep = { source: string; target: string; type: string; origin: string; site: string; route?: string[] };
export type Flow = { ref: string; entry: string; entry_kind: string; complete: boolean; nodes: string[]; steps: FlowStep[] };
export type Gap = { refs: string[]; reason: string };
export type Envelope = {
  schema: typeof SCHEMA; meta: Record<string, unknown>; entities: Entity[]; relations: Relation[];
  memberships: Membership[]; gaps: Gap[]; flows: Flow[];
};

export class EnvelopeError extends Error {}

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

function list(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new EnvelopeError(`${field} is not a list`);
  return value;
}

// The envelope, or EnvelopeError with the reason: a wrong schema, a missing list, or a reference to no entity.
export function parseEnvelope(json: unknown): Envelope {
  if (!isObject(json)) throw new EnvelopeError('the export is not a JSON object');
  if (json.schema !== SCHEMA) throw new EnvelopeError(`unknown schema: ${String(json.schema)}`);
  const entities = list(json.entities, 'entities') as Entity[];
  const known = new Set<string>();
  for (const entity of entities) {
    if (!isObject(entity) || typeof entity.ref !== 'string' || typeof entity.type !== 'string')
      throw new EnvelopeError('an entity has no ref or type');
    known.add(entity.ref);
  }
  const relations = list(json.relations, 'relations') as Relation[];
  const memberships = list(json.memberships, 'memberships') as Membership[];
  const flows = list(json.flows ?? [], 'flows') as Flow[];
  const check = (ref: unknown, owner: string) => {
    if (typeof ref !== 'string' || !known.has(ref)) throw new EnvelopeError(`${owner} names an unknown entity: ${String(ref)}`);
  };
  for (const relation of relations) { check(relation.source, relation.ref); check(relation.target, relation.ref); }
  for (const item of memberships) {
    if (item.view !== 'logical' && item.view !== 'physical') throw new EnvelopeError(`unknown view: ${String(item.view)}`);
    check(item.member, 'a membership'); check(item.group, 'a membership');
  }
  for (const flow of flows) {
    for (const node of list(flow.nodes, `${flow.ref} nodes`)) check(node, flow.ref);
    for (const step of list(flow.steps, `${flow.ref} steps`) as FlowStep[]) { check(step.source, flow.ref); check(step.target, flow.ref); }
  }
  return {
    schema: SCHEMA, meta: isObject(json.meta) ? json.meta : {}, entities, relations, memberships,
    gaps: list(json.gaps ?? [], 'gaps') as Gap[], flows,
  };
}
