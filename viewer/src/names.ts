// How the interface names a node, an entity and a flow: pure, so the sidebar, the details and the canvas say the same.
import type { Envelope, Flow } from './envelope.ts';
import { indexOf } from './projection.ts';
import type { ProjectedNode } from './projection.ts';
import { STATUS_LABEL, TYPE_LABEL } from './icons.ts';

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

// The folder of the project the export is of.
export function projectName(envelope: Envelope): string {
  return String(envelope.meta.project_root ?? '').split(/[\\/]/).filter(Boolean).pop() ?? '';
}
