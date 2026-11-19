// A generic icon per node type (the closed list of the flow model), else per entity type.
import { Archive, Boxes, Braces, CircleDot, Cpu, Database, FileCode, Folder, Globe, KeyRound, ListOrdered, Monitor,
  Package, Router, Server, Sparkles, User } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const BY_NODE_TYPE: Record<string, LucideIcon> = {
  attore: User, schermata: Monitor, 'funzionalità': Sparkles, 'servizio o API': Server, gateway: Router,
  database: Database, coda: ListOrdered, autenticazione: KeyRound, dispositivo: Cpu, altro: CircleDot,
};
const BY_TYPE: Record<string, LucideIcon> = {
  component: Boxes, feature: Sparkles, external: Globe, build: Package, directory: Folder, file: FileCode,
  symbol: Braces, store: Archive, group: Folder,
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

export function iconFor(node: { nodeType?: string; type: string }): LucideIcon {
  return (node.nodeType && BY_NODE_TYPE[node.nodeType]) || BY_TYPE[node.type] || CircleDot;
}
