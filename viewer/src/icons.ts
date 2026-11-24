// The icon of each kind of node, by Sigrid's names.
import type { IconName } from '@acaprino/sigrid/primitives';

// The empty slot (R6): a kind Sigrid has no name for takes no other thing's icon.
export const NO_ICON = '';
export type NodeIcon = IconName | typeof NO_ICON;

export const FLOW_ICON: IconName = 'branch';

// The icon of a generic node type (the closed list of the flow model; `altro` says nothing), else of the entity type.
const BY_NODE_TYPE: Record<string, NodeIcon> = {
  attore: 'account', schermata: 'layout', 'funzionalità': NO_ICON, 'servizio o API': 'service', gateway: 'gateway',
  database: 'data', coda: 'listOrdered', autenticazione: 'key', dispositivo: 'device',
};
const BY_TYPE: Record<string, NodeIcon> = {
  component: 'structure', feature: NO_ICON, external: 'globe', build: 'package', directory: 'folder', file: 'file',
  symbol: 'code', store: 'data', group: 'folder',
};

export function iconFor(node: { nodeType?: string; type: string }): NodeIcon {
  return BY_NODE_TYPE[node.nodeType ?? ''] ?? BY_TYPE[node.type] ?? NO_ICON;
}
