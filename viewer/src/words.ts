// The Italian of the two pages: the words Sigrid's components and Imago's shell say by themselves, for all the pages use; the words of the
// model's closed lists, where the server has its own names; how things are counted; and what is said of what failed.
import type { ShellWords } from '@acaprino/imago';
import type { WordsOverride } from '@acaprino/sigrid';

export const WORDS: WordsOverride = {
  common: {
    close: 'Chiudi', undo: 'Annulla', notices: 'Avvisi', closeNotice: text => `Chiudi l'avviso: ${text}`, error: 'Errore',
    keysTogether: keys => keys.join(' + '), keysInSequence: keys => keys.join(' poi '),
  },
  sidebar: {
    collapse: 'Riduci la barra laterale', expand: 'Espandi la barra laterale', search: 'Cerca nel menu', empty: 'Nessun risultato',
    open: 'Apri il menu',
  },
  search: { clear: 'Svuota la ricerca' },
  list: { unread: 'Non letto', more: count => (count === 1 ? 'un altro' : `altri ${count}`) },
  palette: { placeholder: 'Cerca un comando', empty: 'Nessun comando', command: 'Comandi', keys: 'Tasti' },
  scheme: {
    group: 'Aspetto', light: 'Tema chiaro', dark: 'Tema scuro', system: 'Tema come il sistema', keywords: 'aspetto schema modalità',
  },
  keys: { ctrl: 'Ctrl', cmd: 'Cmd', alt: 'Alt', option: 'Opzione', shift: 'Maiusc' },
  progress: {
    value: (value, max) => `${Math.round((value / max) * 100)}%`, indeterminate: 'In corso', complete: 'Completato', error: 'Non riuscito',
  },
  note: { info: 'Informazione', success: 'Riuscito', warning: 'Attenzione' },
  shell: { skip: 'Vai al contenuto' },
  window: { minimize: 'Riduci a icona', maximize: 'Ingrandisci', restore: 'Ripristina', close: 'Chiudi' },
  graph: {
    view: 'Vista', zoomIn: 'Ingrandisci', zoomOut: 'Riduci', fit: 'Inquadra tutto', roleDescription: 'grafo', external: 'esterno',
    hides: (item, count) => `${item}, contiene ${count === 1 ? 'un elemento' : `${count} elementi`}`,
    chosenToo: item => `scelto con ${item}`,
    leadsTo: items => `porta a ${items.join(', ')}`, comesFrom: items => `arriva da ${items.join(', ')}`,
    open: item => `Apri ${item}`, close: item => `Chiudi ${item}`,
    holds: (item, count) => `${item}, aperto, contiene ${count === 1 ? 'un elemento' : `${count} elementi`}`, inGroup: group => `in ${group}`,
    resetLayout: 'Riordina', moveKeys: 'Alt e una freccia lo spostano', moved: (item, x, y) => `${item} spostato a ${x}, ${y}`,
    moreSteps: count => `+${count}`,
    onPath: (item, steps) => `${item}, ${steps.length === 1 ? `passo ${steps[0]}` : `passi ${steps.slice(0, -1).join(', ')} e ${steps[steps.length - 1]}`}`,
    line: (item, way, label) => `${label ? `${label}, ` : ''}${way === 'to' ? 'verso' : way === 'from' ? 'da' : 'con'} ${item}`,
  },
};

// What the person asked the window for.
const ASKED: Record<string, string> = { minimize: 'riduci a icona', toggleMaximize: 'ingrandisci', close: 'chiudi', setZoom: 'zoom' };
export const SHELL_WORDS: ShellWords = {
  views: 'Viste', search: 'Cerca in questa vista', noSearch: 'Questa vista non ha una ricerca.', nextRegion: 'Area successiva',
  screenFailed: 'Questa schermata non si può mostrare', retry: 'Riprova',
  windowFailed: (call, cause) => `La finestra non ha risposto (${ASKED[call] ?? call}): ${cause}`,
};

// -- counting ----------------------------------------------------------------------------------------------------------

export const number = (n: number | null | undefined) => Number(n || 0).toLocaleString('it-IT');
// «1 passo», «8 passi».
export const plural = (n: number, one: string, many: string) => `${number(n)} ${Number(n) === 1 ? one : many}`;

// The row that opens the rest of a long list: «1 altro passo», «Altri 3 passi».
const rest = (n: number, one: string, many: string, other: 'altro' | 'altra' = 'altro') =>
  (n === 1 ? `1 ${other} ${one}` : `${other === 'altra' ? 'Altre' : 'Altri'} ${number(n)} ${many}`);
export const MORE = {
  steps: (n: number) => rest(n, 'passo', 'passi'),
  links: (n: number) => rest(n, 'collegamento', 'collegamenti'),
  evidence: (n: number) => rest(n, 'evidenza', 'evidenze', 'altra'),
  files: (n: number) => rest(n, 'file', 'file'),
  symbols: (n: number) => rest(n, 'simbolo', 'simboli'),
  calls: (n: number) => rest(n, 'chiamata', 'chiamate', 'altra'),
  relations: (n: number) => rest(n, 'relazione', 'relazioni', 'altra'),
  events: (n: number) => rest(n, 'evento', 'eventi'),
  gaps: (n: number) => rest(n, 'lacuna', 'lacune', 'altra'),
};

// -- the model's closed lists ------------------------------------------------------------------------------------------
// A name that is not here is shown as the server wrote it.

export const TYPE_LABEL: Record<string, string> = {
  component: 'componente', feature: 'funzionalità', external: 'esterno', build: 'unità di build', directory: 'cartella',
  file: 'file', symbol: 'simbolo', store: 'dato', group: 'gruppo', virtual: 'fuori dalle unità di build',
};
export const STATUS_LABEL: Record<string, string> = { confirmed: 'confermato', inferred: 'inferito', incomplete: 'incompleto', proposed: 'proposto' };
export const FRESHNESS_LABEL: Record<string, string> = {
  fresh: 'scheda aggiornata', stale_body: 'scheda da rileggere: corpo cambiato', stale_interface: 'scheda da rileggere: interfaccia cambiata',
  stale_callee: 'scheda da rileggere: chiamati cambiati', orphan: 'scheda orfana', uncovered: 'senza scheda',
};
export const PROVENANCE_LABEL: Record<string, string> = {
  build: 'strumento di build', declared: 'dichiarato dal progetto', proposed: 'proposto dal modello', virtual: 'nessuno strumento di build lo nomina',
  registry: 'registro delle tecnologie',
};
export const ENTRY_LABEL: Record<string, string> = { azione: 'azione dell\'utente', rotta: 'rotta', 'lavoro pianificato': 'lavoro pianificato' };
// The categories of the technology registry.
export const CATEGORY_LABEL: Record<string, string> = { framework: 'framework', library: 'libreria', service: 'servizio', tool: 'strumento' };

// What a line does, from where it starts.
export const LINK_LABEL: Record<string, string> = {
  chiama: 'chiama', scrive: 'scrive', legge: 'legge', attiva: 'attiva', usa: 'usa',
  imports: 'importa', calls: 'chiama', uses: 'usa', declares: 'dichiara', reads: 'legge',
};
// How many of each kind a relation counts: «2 chiamate, 1 import».
const RELATIONS: Record<string, [string, string]> = {
  calls: ['chiamata', 'chiamate'], imports: ['import', 'import'], uses: ['utilizzo', 'utilizzi'], reads: ['lettura', 'letture'],
  declares: ['dichiarazione', 'dichiarazioni'],
};
export const relationCounts = (counts: Record<string, number>) => Object.entries(counts).map(([kind, count]) =>
  (RELATIONS[kind] ? plural(count, ...RELATIONS[kind]) : `${kind}: ${number(count)}`)).join(', ');

const PROOF: Record<string, string> = { observed: 'osservata in esecuzione', sampled: 'campionata dal profiler', uncertain: 'incerta' };
// What proves a relation or a step, where it is not the code alone.
export const proofLabel = (status: string | undefined, conflict = false) =>
  [PROOF[status ?? ''] ?? '', conflict && 'destinazioni in conflitto'].filter(Boolean).join(' · ');

// The events of a run's own journal.
export const EVENT_LABEL: Record<string, string> = {
  run_created: 'Run creato', run_resumed: 'Run ripreso', run_stopped: 'Run fermato', run_published: 'Run pubblicato',
  phase_started: 'Fase avviata', phase_completed: 'Fase completata', blocked: 'Run bloccato',
  engine_started: 'Passaggio del grafo avviato', engine_unavailable: 'Passaggio del grafo non disponibile',
  engine_failed: 'Passaggio del grafo interrotto', engine_stopped: 'Passaggio del grafo fermato',
  index_failed: 'Indice lessicale non costruito', index_refreshed: 'Indice lessicale aggiornato',
  modules_failed: 'Grafo dei moduli non costruito', modules_proposed: 'Moduli proposti', modules_refreshed: 'Grafo dei moduli aggiornato',
};

// -- what failed -------------------------------------------------------------------------------------------------------

export const FAILURE = {
  busy: 'Daodan è occupato', retried: 'Daodan è occupato, riprovo', unanswered: 'il server non risponde',
  refused: 'il server rifiuta la richiesta: riapri la pagina dall\'indirizzo che Daodan ti ha dato',
  status: (status: number) => `il server ha risposto ${status}`,
  layoutEmpty: 'la disposizione è vuota', layoutSlow: (ms: number) => `la disposizione ha richiesto più di ${ms} ms`,
};
// Why a file or an answer holds no export.
export const NO_EXPORT = {
  json: 'non è JSON', object: 'non è un oggetto JSON', entity: 'un\'entità non ha ref o type', membership: 'un\'appartenenza',
  schema: (schema: unknown) => (schema === undefined ? 'non dice il suo schema' : `schema sconosciuto: ${String(schema)}`),
  list: (field: string) => `«${field}» non è un elenco`,
  unknown: (owner: string, ref: unknown) => `${owner} nomina un'entità sconosciuta: ${String(ref)}`,
  view: (view: unknown) => `vista sconosciuta: ${String(view)}`,
};
