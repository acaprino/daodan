// The export the viewer draws (`daodan/visual@1`, written by visual.py). Nothing is inferred here.
import { NO_EXPORT } from './words.ts';

export const SCHEMA = 'daodan/visual@1';
export const NODE_TYPES = ['attore', 'schermata', 'funzionalità', 'servizio o API', 'gateway', 'database', 'coda',
  'autenticazione', 'dispositivo', 'altro'] as const;

export type Evidence = { path?: string | null; line?: number | null };
export type Entity = {
  ref: string; type: string; name: string; technical: string; description: string;
  provenance?: string; status?: string; freshness?: string; path?: string; lines?: number | number[];
  address?: string; location?: 'internal' | 'external'; node_type?: string; evidence: Evidence[]; gaps: unknown[];
  technologies?: string[]; mark?: string;
};
// A framework, library, tool or service the stack step recognized, with the files that show it. `mark`, here and on an
// entity, is the registry id whose logo the server of the page answers (`./api/mark?id=`, with the page's token if any).
export type Technology = { id: string; name: string; type: string; category?: string; paths: string[]; mark?: string };
export type Relation = {
  ref: string; kind: string; source: string; target: string; status: string;
  counts?: Record<string, number>; evidence: Evidence[]; conflict?: boolean;
};
export type View = 'logical' | 'physical';
export type Membership = { member: string; group: string; view: View };
export type FlowStep = {
  source: string; target: string; type: string; origin: string; site: string;
  route?: string[]; confidence?: string; conflict?: boolean;
};
export type Flow = {
  ref: string; entry: string; entry_kind: string; complete: boolean; nodes: string[]; steps: FlowStep[];
  site?: string; column?: number; label?: string; event?: string; shape?: string;
  gaps?: { site: string; reason: string }[];
};
export type Gap = { refs: string[]; reason: string };
export type Envelope = {
  schema: typeof SCHEMA; meta: Record<string, unknown>; entities: Entity[]; relations: Relation[];
  memberships: Membership[]; gaps: Gap[]; flows: Flow[]; technologies: Technology[];
};

export class EnvelopeError extends Error {}

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

function list(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new EnvelopeError(NO_EXPORT.list(field));
  return value;
}

// The envelope, or EnvelopeError with the reason: a wrong schema, a missing list, or a reference to no entity.
export function parseEnvelope(json: unknown): Envelope {
  if (!isObject(json)) throw new EnvelopeError(NO_EXPORT.object);
  if (json.schema !== SCHEMA) throw new EnvelopeError(NO_EXPORT.schema(json.schema));
  const entities = list(json.entities, 'entities') as Entity[];
  const known = new Set<string>();
  for (const entity of entities) {
    if (!isObject(entity) || typeof entity.ref !== 'string' || typeof entity.type !== 'string')
      throw new EnvelopeError(NO_EXPORT.entity);
    known.add(entity.ref);
  }
  const relations = list(json.relations, 'relations') as Relation[];
  const memberships = list(json.memberships, 'memberships') as Membership[];
  // Older exports assigned the handler's ref to every event bound to it.
  const rawFlows = list(json.flows ?? [], 'flows') as Flow[];
  const used = new Set(rawFlows.map(flow => flow.ref));
  const seen = new Set<string>();
  const flows = rawFlows.map((flow, index) => {
    if (!seen.has(flow.ref)) { seen.add(flow.ref); return flow; }
    let ref = `${flow.ref}#${index + 1}`;
    while (used.has(ref)) ref += '#';
    used.add(ref);
    return { ...flow, ref };
  });
  const check = (ref: unknown, owner: string) => {
    if (typeof ref !== 'string' || !known.has(ref)) throw new EnvelopeError(NO_EXPORT.unknown(owner, ref));
  };
  for (const relation of relations) { check(relation.source, relation.ref); check(relation.target, relation.ref); }
  for (const item of memberships) {
    if (item.view !== 'logical' && item.view !== 'physical') throw new EnvelopeError(NO_EXPORT.view(item.view));
    check(item.member, NO_EXPORT.membership); check(item.group, NO_EXPORT.membership);
  }
  for (const flow of flows) {
    for (const node of list(flow.nodes, `${flow.ref} nodes`)) check(node, flow.ref);
    for (const step of list(flow.steps, `${flow.ref} steps`) as FlowStep[]) { check(step.source, flow.ref); check(step.target, flow.ref); }
  }
  return {
    schema: SCHEMA, meta: isObject(json.meta) ? json.meta : {}, entities, relations, memberships,
    gaps: list(json.gaps ?? [], 'gaps') as Gap[], flows,
    technologies: list(json.technologies ?? [], 'technologies') as Technology[],
  };
}

// The envelope a file holds.
export function readEnvelope(text: string): Envelope {
  let json: unknown;
  try { json = JSON.parse(text); } catch (error) { throw new EnvelopeError(NO_EXPORT.json, { cause: error }); }
  return parseEnvelope(json);
}
