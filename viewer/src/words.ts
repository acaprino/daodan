// The Italian of the words Sigrid's components say by themselves, for every component the pages use.
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
