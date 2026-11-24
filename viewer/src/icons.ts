// The words of the model's closed lists, and the icon of each kind of node, by Sigrid's names.
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

export const TYPE_LABEL: Record<string, string> = {
  component: 'componente', feature: 'funzionalità', external: 'esterno', build: 'unità di build', directory: 'cartella',
  file: 'file', symbol: 'simbolo', store: 'dato', group: 'gruppo',
};
export const STATUS_LABEL: Record<string, string> = { confirmed: 'confermato', inferred: 'inferito', incomplete: 'incompleto' };
export const FRESHNESS_LABEL: Record<string, string> = {
  fresh: 'scheda aggiornata', stale_body: 'scheda da rileggere: corpo cambiato', stale_interface: 'scheda da rileggere: interfaccia cambiata',
  stale_callee: 'scheda da rileggere: chiamati cambiati', orphan: 'scheda orfana', uncovered: 'senza scheda',
};
export const LINK_LABEL: Record<string, string> = {
  chiama: 'chiama', scrive: 'scrive', legge: 'legge', attiva: 'attiva', usa: 'usa',
  imports: 'importa', calls: 'chiama', uses: 'usa', declares: 'dichiara',
};
export const ENTRY_LABEL: Record<string, string> = { azione: 'azione dell\'utente', rotta: 'rotta', 'lavoro pianificato': 'lavoro pianificato' };

export function iconFor(node: { nodeType?: string; type: string }): NodeIcon {
  return BY_NODE_TYPE[node.nodeType ?? ''] ?? BY_TYPE[node.type] ?? NO_ICON;
}
