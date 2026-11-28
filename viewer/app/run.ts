// The run, read from its state and its events: its steps, percent, notices, log and gaps, in words.
import type { BadgeTone } from '@acaprino/sigrid/primitives';
import { EVENT_LABEL, number, plural } from '../src/words.ts';
import { isPreparing, preparation } from './repository.ts';
import { complete, ctx, pass } from './snapshot.ts';
import type { Links, Mapped } from './server.ts';
import type { Snapshot } from './snapshot.ts';

type Run = Pick<Snapshot, 'server' | 'events'>;
export type Message = { tone: 'info' | 'warning' | 'error'; title: string; message: string };

// The steps the pipeline runs, by their ids (`pipeline.STEPS`); a journal of old names reaches here with the ids. A bridge until
// the view of the eight steps reads the plan from the server.
const STEPS: [string, string][] = [['recognize_stack', 'Tecnologie · stack e librerie'], ['find_modules', 'Moduli · struttura del progetto'],
  ['find_entry_points', 'Ingressi · rotte e pagine'], ['link_calls', 'Chiamate · analizzatore per linguaggio'],
  ['run_and_observe', 'Esecuzione · osservazione dei test'], ['assemble_graph', 'Grafo · collegamento dei grafi']];
const STEP: Record<string, string> = Object.fromEntries(STEPS.map(([id, label]) => [id, label.split(' · ')[0]]));

export const pipelineEvents = (s: Pick<Snapshot, 'events'>) => s.events.filter(e => !e.run);

export type StepStatus = 'running' | 'done' | 'failed' | 'pending' | 'skipped';
export type RunStep = { id: string; label: string; status: StepStatus; note: string };

// A step the pipeline did not run because its records are fresh (`step.skipped`): it counts as done.
const UP_TO_DATE = 'Già aggiornata';

// The run's steps follow their own events: the pass's state is the engine's, whose end does not end the steps after it. The
// note comes from the run: the progress, the cause of a step that failed or of an analyzer that could not run, and the pass's
// cause for a step the run will not reach.
export function steps(s: Run): RunStep[] {
  const status: Record<string, StepStatus> = {}, causes: Record<string, string[]> = {}, failed: Record<string, string> = {};
  for (const e of pipelineEvents(s)) {
    const step = e.step ?? '';
    if (e.kind === 'step.started') { status[step] = 'running'; causes[step] = []; delete failed[step]; }
    if (e.kind === 'step.finished') status[step] = 'done';
    if (e.kind === 'step.skipped') { status[step] = 'skipped'; causes[step] = []; delete failed[step]; }
    if (e.kind === 'step.failed' || (e.kind === 'log' && e.level === 'error' && e.data?.cause)) failed[step] = e.data?.cause || e.message;
    if (e.kind === 'analyzer.unavailable') (causes[step] ||= []).push(`${e.analyzer || 'analyzer'}: ${e.data?.cause || e.message}`);
  }
  const progress = s.server?.run?.progress, p = pass(s);
  const of = (id: string): StepStatus => (failed[id] ? 'failed' : status[id] || 'pending');
  const reached = !complete(s) || STEPS.some(([id]) => of(id) === 'running');  // a step still runs: the next may start
  return STEPS.map(([id, label]): RunStep => {
    const now = of(id), cause = causes[id]?.join(' · ');
    const note = now === 'done' ? (cause ? 'Completata con lacune · ' + cause : 'Completata')
      : now === 'running' ? 'In corso' + (progress?.step === id && progress.total ? ` · ${progress.done}/${progress.total}` : '')
        : now === 'failed' ? 'Non riuscita · ' + failed[id] : now === 'skipped' ? UP_TO_DATE
          : reached ? 'In attesa' : 'Non eseguita' + (p.reason ? ' · ' + p.reason : '');
    return { id, label, status: now === 'pending' && !reached ? 'skipped' : now, note };
  });
}

// How long a step has taken, or took, as its events say; empty where they do not.
export function stepTime(s: Pick<Snapshot, 'events'>, { id, status }: Pick<RunStep, 'id' | 'status'>, now: number): string {
  const running = status === 'running';
  let from = NaN, to = running ? now : NaN;
  for (const e of pipelineEvents(s)) {
    if (e.step !== id || !e.at) continue;
    if (e.kind === 'step.started') from = Date.parse(e.at);
    else if (!running && (e.kind === 'step.finished' || e.kind === 'step.failed')) to = Date.parse(e.at);
  }
  const seconds = Math.round((to - from) / 1000);
  return !(seconds >= 0) ? '' : seconds < 60 ? `${seconds} s` : `${Math.floor(seconds / 60)} min ${seconds % 60} s`;
}

// The steps as the path draws them. What the dot says is not said again under the name.
const SAID: readonly string[] = ['Completata', 'In attesa'];
export function phaseItems(s: Run, now: number) {
  return steps(s).map(step => ({
    label: step.label, status: step.status === 'failed' ? 'error' as const : step.status === 'pending' ? 'todo' as const : step.status,
    description: SAID.includes(step.note) ? undefined : step.note, meta: stepTime(s, step, now) || undefined,
  }));
}

const completed = (list: readonly RunStep[]) => list.filter(t => t.status === 'done' || t.note === UP_TO_DATE).length;
// How many of its steps are done, beside the screen's title.
export function runCount(s: Run): string {
  const list = steps(s);
  return `${completed(list)} di ${list.length} passi completati`;
}
export function runPercent(s: Run): number {
  if (!ctx(s)) return 0;
  const list = steps(s), progress = s.server?.run?.progress;
  const running = list.find(t => t.status === 'running');
  const part = running && progress?.step === running.id && progress.total ? progress.done / progress.total : 0;
  return Math.round(100 * (completed(list) + part) / list.length);
}

// The bar of the steps: how far it is. It stopped when the run is over with a step that failed, and says it.
export function runBar(s: Run): { value: number; status?: 'error'; valueText?: string } {
  const list = steps(s), value = runPercent(s);
  const stopped = complete(s) && list.some(t => t.status === 'failed') && !list.some(t => t.status === 'running');
  return stopped ? { value, status: 'error', valueText: `Non riuscito · ${value}%` } : { value };
}

const PHASE: Record<string, string> = {
  fresh: 'Pipeline completata', unavailable: 'Pipeline completata con lacune',
  failed: 'Pipeline conclusa, grafo delle chiamate non rifinito', off: 'Passaggio del grafo spento',
};
export const runPhaseLabel = (s: Run) =>
  steps(s).find(t => t.status === 'running')?.label ?? PHASE[pass(s).state ?? ''] ?? 'In attesa del passaggio del grafo';

const PASS: Record<string, string> = { fresh: 'completato', unavailable: 'non disponibile', failed: 'non riuscito', off: 'spento' };
// The state of the pass that refines the graph of the calls; empty where the run says none.
export function passWord(s: Pick<Snapshot, 'server'>): string {
  const { state } = pass(s);
  return state ? PASS[state] ?? 'in corso' : '';
}

const STATUS: Record<string, string> = { fresh: 'Completata', unavailable: 'Completata con lacune', failed: 'Da riprovare', off: 'Spenta' };
export const statusLabel = (s: Pick<Snapshot, 'server'>) => STATUS[pass(s).state ?? ''] ?? 'In esecuzione';

export function runHelp(s: Pick<Snapshot, 'server'>): string {
  const p = s.server?.run?.progress;
  if (complete(s)) {
    return pass(s).state === 'fresh' ? 'Pipeline conclusa: sintesi e grafo sono pronti da leggere.'
      : 'Pipeline conclusa: sintesi e grafo mostrano quello che c’è, con le sue lacune.';
  }
  return p ? `Ultimo avanzamento: ${STEP[p.step ?? ''] || p.step || 'pipeline'}${p.analyzer ? ' · ' + p.analyzer : ''} · ${p.message || p.done + '/' + p.total}`
    : 'In attesa del primo avanzamento del run.';
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

const KIND: Record<string, string> = {
  'step.started': 'avviato', 'step.finished': 'completato', 'step.failed': 'non riuscito', 'step.skipped': 'saltato', 'analyzer.started': 'analyzer avviato', 'analyzer.unavailable': 'analyzer non disponibile',
  'analyzer.finished': 'analyzer completato', gap: 'lacuna', 'graph.ready': 'grafo pronto', log: 'nota',
};
export type LogItem = { title: string; detail: string; type: 'error' | 'gap' | ''; at?: string };
export function logItems(s: Pick<Snapshot, 'events'>): LogItem[] {
  return s.events.filter(e => e.run || (e.kind !== 'progress' && e.level !== 'debug')).map((e): LogItem => {
    if (e.run) {
      const event = e.event ?? '';
      return { title: EVENT_LABEL[event] || event, detail: e.message, type: /failed/.test(event) ? 'error' : /unavailable/.test(event) ? 'gap' : '', at: e.timestamp };
    }
    const kind = e.kind ?? '', gap = e.data?.gap;
    return {
      title: `${STEP[e.step ?? ''] || e.step || 'Pipeline'} · ${KIND[kind] || kind}${e.analyzer && kind !== 'gap' ? ' · ' + e.analyzer : ''}`,
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

// What the run says it does not know.
export function gapLines(s: Pick<Snapshot, 'server' | 'events' | 'graph'>): string[] {
  const lines: string[] = [];
  if (passAlert(s)) lines.push('Grafo delle chiamate non rifinito: ' + (pass(s).reason || passWord(s)));
  if (s.graph?.unassigned.count) lines.push(`${number(s.graph.unassigned.count)} file non assegnati a un modulo.`);
  for (const e of pipelineEvents(s)) if (e.kind === 'gap') lines.push(e.data?.gap?.detail || e.message);
  for (const gap of s.graph?.gaps ?? []) lines.push(gap.reason);
  return [...new Set(lines)];
}

export function buildStatus(s: Run & Pick<Snapshot, 'graphLoading'>): string {
  if (s.graphLoading) return 'Lettura del grafo…';
  if (pipelineEvents(s).some(e => e.kind === 'graph.ready')) return 'Grafo del codice scritto';
  return complete(s) ? 'Costruzione conclusa' : 'Costruzione in corso';
}

// Why a question cannot be asked now; empty when it can.
export const askReason = (s: Pick<Snapshot, 'server'>) =>
  (!ctx(s) ? 'Seleziona prima una repository.' : s.server?.engine?.engine ? '' : 'Scegli e salva prima un motore.');
export const isAsking = (s: Pick<Snapshot, 'server' | 'asked'>) => s.asked?.state === 'running' || s.server?.asked?.state === 'running';

// The status row: the state, what is under way, and how far it is where that is known. A step under way is said by its short
// name: the row stays one line at 620 px, and the screen of the run says the rest.
export function statusOf(s: Run & Pick<Snapshot, 'serverError'>): { state: string; tone?: BadgeTone; text: string; percent: number | null } {
  if (s.serverError) return { state: 'Errore', tone: 'danger', text: 'Server non raggiungibile', percent: null };
  if (!s.server) return { state: 'Lettura', tone: 'info', text: 'Lettura dello stato del server…', percent: null };
  const work = preparation(s.server.job);
  if (isPreparing(s)) return { state: 'Preparazione in corso', tone: 'info', text: work?.step ?? '', percent: null };
  if (!ctx(s)) return { state: 'Nessuna repository', text: work ? `Preparazione non riuscita (${work.step})` : '', percent: null };
  const now = steps(s).find(step => step.status === 'running'), running = !complete(s) || Boolean(now);
  return { state: running ? 'Analisi in corso' : 'Contesto pronto', tone: running ? 'info' : 'success', text: now ? STEP[now.id] : runPhaseLabel(s),
    percent: running ? runPercent(s) : null };
}

// The foot: where the service is, and the engine.
export function serviceLine(s: Pick<Snapshot, 'server' | 'serverError'>): string {
  const engine = s.server?.engine?.engine;
  return [s.serverError ? 'Server non raggiungibile' : s.server ? 'App locale: il codice resta sul tuo disco' : 'Lettura dello stato del server…',
    engine ? `Motore: ${engine}` : 'Motore non scelto'].join(' · ');
}
