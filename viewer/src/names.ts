// How the interface names a node, an entity and a flow, and how it counts: pure, so the sidebar, the details and the canvas
// say the same.
import type { Entity, Envelope, Flow, FlowStep } from './envelope.ts';
import { indexOf } from './projection.ts';
import type { ProjectedNode } from './projection.ts';
import { ENTRY_LABEL, FLOW_ICON, iconFor, STATUS_LABEL, TYPE_LABEL } from './icons.ts';
import type { NodeIcon } from './icons.ts';

export function nodeMeta(node: ProjectedNode): string {
  return [
    node.nodeType ?? TYPE_LABEL[node.type] ?? node.type,
    node.location === 'external' ? 'esterno' : null,
    node.status && node.status !== 'confirmed' ? STATUS_LABEL[node.status] ?? node.status : null,
    node.freshness && !['fresh', 'uncovered'].includes(node.freshness) ? 'scheda da rileggere' : null,
  ].filter(Boolean).join(' · ');
}

export function entityName(envelope: Envelope, ref: string): string {
  return indexOf(envelope).byRef.get(ref)?.name ?? ref;
}

export function bindingSite(flow: Flow): string | undefined {
  return flow.site && flow.column != null ? `${flow.site}:${flow.column}` : flow.site;
}

export function flowTitle(envelope: Envelope, flow: Flow): string {
  return flow.label || [flow.event || flow.shape || entityName(envelope, flow.entry), bindingSite(flow)].filter(Boolean).join(' · ');
}

export const entryName = (flow: Flow): string => ENTRY_LABEL[flow.entry_kind] ?? flow.entry_kind;
export const kindOf = (entity: Entity): string => entity.node_type ?? TYPE_LABEL[entity.type] ?? entity.type;

export function stepMeta(step: FlowStep): string {
  return [step.route?.slice(1).join(' '), step.site, step.origin,
    step.confidence === 'sampled' ? 'campionata dal profiler' : step.confidence === 'observed' ? 'osservata in esecuzione' : null,
    step.conflict ? 'destinazioni in conflitto' : null].filter(Boolean).join(' · ');
}

// The folder of the project the export is of.
export function projectName(envelope: Envelope): string {
  return String(envelope.meta.project_root ?? '').split(/[\\/]/).filter(Boolean).pop() ?? '';
}

// What the inspector is about: its title, and the name it shows with its icon. With no element and no flow it is the project.
export function headOf(envelope: Envelope, entity?: Entity, flow?: Flow): { title: string; name: string; icon: NodeIcon } {
  if (entity) return { title: 'Dettaglio', name: entity.name, icon: iconFor({ nodeType: entity.node_type, type: entity.type }) };
  if (flow) return { title: 'Flusso', name: flowTitle(envelope, flow), icon: FLOW_ICON };
  return { title: 'Informazioni sul progetto', name: projectName(envelope) || 'Progetto', icon: 'info' };
}

// «1 passo», «8 passi».
export const counted = (count: number, one: string, many: string): string => `${count} ${count === 1 ? one : many}`;

// The row that opens the rest of a long list, by what the list holds.
export const MORE = {
  steps: (count: number) => (count === 1 ? '1 altro passo' : `Altri ${count} passi`),
  links: (count: number) => (count === 1 ? '1 altro collegamento' : `Altri ${count} collegamenti`),
  evidence: (count: number) => (count === 1 ? '1 altra evidenza' : `Altre ${count} evidenze`),
  files: (count: number) => (count === 1 ? '1 altro file' : `Altri ${count} file`),
};
