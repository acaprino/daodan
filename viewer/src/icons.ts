// The words of the model's closed lists, and the icon of each kind of node, by Sigrid's names.
import type { IconName } from '@acaprino/sigrid';

// shortcut: Sigrid 5.0.0 has no branch, code, external, package, key, device or gateway: the closest name it has stands in, until the release of Sigrid that has them
const BRANCH: IconName = 'moveRight', CODE: IconName = 'tag', EXTERNAL: IconName = 'link', PACKAGE: IconName = 'archive',
  KEY: IconName = 'profile', DEVICE: IconName = 'settings', GATEWAY: IconName = 'importExport';

// The icon of a generic node type (the closed list of the flow model), else of the entity type.
const BY_NODE_TYPE: Record<string, IconName> = {
  attore: 'account', schermata: 'layout', 'funzionalità': 'now', 'servizio o API': 'service', gateway: GATEWAY,
  database: 'data', coda: 'listOrdered', autenticazione: KEY, dispositivo: DEVICE, altro: 'more',
};
const BY_TYPE: Record<string, IconName> = {
  component: 'structure', feature: 'now', external: EXTERNAL, build: PACKAGE, directory: 'folder', file: 'file',
  symbol: CODE, store: 'data', group: 'folder',
};
export const FLOW_ICON = BRANCH;

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

export function iconFor(node: { nodeType?: string; type: string }): IconName {
  return (node.nodeType && BY_NODE_TYPE[node.nodeType]) || BY_TYPE[node.type] || 'more';
}
