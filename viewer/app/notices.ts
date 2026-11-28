// What the run says beside its plan, in words: the pass that refines the graph of the calls, the map of the system, the links between
// the modules, the graph as it is built, the foot of the window, and the events of the journal, which are its chronicle.
import { STEPS } from '../pipeline/data.ts';
import { EVENT_LABEL, plural } from '../src/words.ts';
import { complete, pass } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';
import type { Links, Mapped } from './server.ts';

export type Message = { tone: 'info' | 'warning' | 'error'; title: string; message: string };

const PASS: Record<string, string> = { fresh: 'completato', unavailable: 'non disponibile', failed: 'non riuscito', off: 'spento' };
// The state of the pass that refines the graph of the calls; empty where the run says none.
export function passWord(s: Pick<Snapshot, 'server'>): string {
  const { state } = pass(s);
  return state ? PASS[state] ?? 'in corso' : '';
}

// Why the pass that refines the graph of the calls did not; one that failed can be tried again.
export function passAlert(s: Pick<Snapshot, 'server'>): (Message & { retry: boolean }) | null {
  const p = pass(s), failed = p.state === 'failed';
  if (!failed && p.state !== 'unavailable' && p.state !== 'off') return null;
  return {
    tone: failed ? 'error' : 'warning', retry: failed, message: p.reason || 'Nessuna causa registrata.',
    title: failed ? 'Il passaggio che rifinisce il grafo delle chiamate non è riuscito.'
      : 'Lacuna: il passaggio che rifinisce il grafo delle chiamate non è disponibile.',
  };
}

// The words of an event, with the title of its step from the page of the pipeline (`STEPS`, by `id`).
// An event of no step is the pipeline's: the steps of the page without an id (what comes after, what all share) are none of them.
const titleOf = (id: string | undefined) => (id && STEPS.plan.find(step => step.id === id)?.title) || id || 'Pipeline';
const KIND: Record<string, string> = {
  'step.started': 'avviato', 'step.finished': 'completato', 'step.failed': 'non riuscito', 'step.skipped': 'saltato', 'analyzer.started': 'strumento avviato',
  'analyzer.unavailable': 'strumento non disponibile', 'analyzer.finished': 'strumento completato', gap: 'lacuna', 'graph.ready': 'grafo pronto', log: 'nota',
};
export type LogItem = { title: string; detail: string; type: 'error' | 'gap' | ''; at?: string };
// The events of the run, in words, without the progress and the debug: the journal is a chronicle, the plan says how the steps are.
export function logItems(s: Pick<Snapshot, 'events'>): LogItem[] {
  return s.events.filter(e => e.run || (e.kind !== 'progress' && e.level !== 'debug')).map((e): LogItem => {
    if (e.run) {
      const event = e.event ?? '';
      return { title: EVENT_LABEL[event] || event, detail: e.message, type: /failed/.test(event) ? 'error' : /unavailable/.test(event) ? 'gap' : '', at: e.timestamp };
    }
    const kind = e.kind ?? '', gap = e.data?.gap;
    return {
      title: `${titleOf(e.step)} · ${KIND[kind] || kind}${e.analyzer && kind !== 'gap' ? ' · ' + e.analyzer : ''}`,
      detail: kind === 'gap' ? (gap?.detail || e.message) + (gap?.remedy ? ' Rimedio: ' + gap.remedy : '')
        : kind === 'analyzer.unavailable' ? e.data?.cause || e.message
          : kind === 'step.finished' && e.data?.outputs ? 'Scritti: ' + e.data.outputs.join(', ')
            : kind === 'step.started' && e.data?.inputs ? 'Legge: ' + e.data.inputs.join(', ') : e.message,
      type: e.level === 'error' ? 'error' : kind === 'gap' || e.level === 'warning' ? 'gap' : '', at: e.at,
    };
  });
}

const MAPPED: Record<string, string> = {
  running: 'Mappatura del sistema in corso', failed: 'Mappatura del sistema interrotta',
  no_engine: 'Mappatura in attesa di un motore', done: 'Mappa del sistema registrata',
};
// The map of the system: what is said of it is the server's state, from the stream.
export function mapNotice(s: Pick<Snapshot, 'server'>): Message | null {
  const map = s.server?.mapped;
  if (!map) return null;
  const review: NonNullable<Mapped['needs_review']> = map.needs_review ?? {};
  const counts = [
    review.nodes?.count && plural(review.nodes.count, 'nodo', 'nodi'),
    review.flows?.count && plural(review.flows.count, 'flusso', 'flussi'),
    review.refused_proposals?.count && plural(review.refused_proposals.count, 'proposta rifiutata', 'proposte rifiutate'),
  ].filter(Boolean);
  const partial = counts.length > 0 || map.state === 'incomplete';
  const title = partial ? 'Mappa del sistema parziale' : MAPPED[map.state];
  if (!title) return null;
  const cause = map.cause === 'the recorded map still has stale or incomplete records'
    ? 'Alcune prove sono incomplete o si riferiscono a una revisione precedente.' : map.cause;
  return { tone: partial || map.state === 'no_engine' ? 'warning' : map.state === 'failed' ? 'error' : 'info', title,
    message: [counts.length > 0 && `Da verificare: ${counts.join(', ')}.`, cause].filter(Boolean).join(' ') };
}

const LINKS: Record<string, string> = {
  idle: 'Non ancora cercati: il motore scrive le regole del progetto, la macchina le applica e decide ogni legame.',
  running: 'In corso: il motore scrive le regole, la macchina le applica e gli rimanda quello che resta scollegato.',
  done: 'Trovati dalla macchina con le regole del progetto.', failed: 'Non trovati.', no_engine: 'Nessun motore scelto.',
};
// The links between modules: the engine writes the project's link rules, the machine applies them and decides every link.
// `reason` is why they cannot be looked for now, and it is in the message too.
export function linksNote(s: Pick<Snapshot, 'server'>): Message & { running: boolean; reason: string } {
  const l: Links = s.server?.links ?? { state: 'idle' };
  const reason = s.server?.engine?.engine ? '' : 'Scegli e salva prima un motore.';
  const counts = l.state === 'done' && l.routes
    ? [plural(l.routes.called, 'richiesta', 'richieste'), plural(l.routes.offered, 'rotta', 'rotte'), plural(l.routes.linked, 'legame', 'legami'),
      plural(l.gaps ?? 0, 'lacuna', 'lacune'), ...(l.stores ? [plural(l.stores, 'archivio', 'archivi')] : [])].join(', ') + '.'
    : '';
  return { tone: l.state === 'failed' ? 'error' : 'info', title: 'Legami tra i moduli', running: l.state === 'running', reason,
    message: [LINKS[l.state] ?? l.state, counts, l.state === 'failed' && l.cause, reason].filter(Boolean).join(' ') };
}

// How the graph is being built: read, written by the pipeline, or not yet.
export function buildStatus(s: Pick<Snapshot, 'server' | 'events' | 'graphLoading'>): string {
  if (s.graphLoading) return 'Lettura del grafo…';
  if (s.events.some(e => !e.run && e.kind === 'graph.ready')) return 'Grafo del codice scritto';
  return complete(s) ? 'Costruzione conclusa' : 'Costruzione in corso';
}

// The foot: where the service is, and the engine.
export function serviceLine(s: Pick<Snapshot, 'server' | 'serverError'>): string {
  const engine = s.server?.engine?.engine;
  return [s.serverError ? 'Server non raggiungibile' : s.server ? 'App locale: il codice resta sul tuo disco' : 'Lettura dello stato del server…',
    engine ? `Motore: ${engine}` : 'Motore non scelto'].join(' · ');
}
