// The plan of the run, in words: its steps for the path, the actions of each, the one under way, what is missing and the status row.
// All of it is read from the server's state (`run.plan`, the one `codebase_map_status` gives): the order and the presence of the
// steps are the plan's, their words are those of the page of the pipeline (`STEPS`, by `id`), and nothing is counted from the events.
import type { BadgeTone } from '@acaprino/sigrid/primitives';
import { STEPS } from '../pipeline/data.ts';
import { number, plural } from '../src/words.ts';
import { isPreparing, preparation } from './repository.ts';
import { passAlert, passWord } from './run.ts';
import type { Plan, PlanAction, PlanStep, Policy } from './server.ts';
import { complete, ctx, pass } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';

type Run = Pick<Snapshot, 'server'>;
const WORDS = new Map(STEPS.plan.flatMap(step => (step.id ? [[step.id, step] as const] : [])));

export const planOf = (s: Run): Plan | null => s.server?.run?.plan ?? null;
// The title of a step and what it does; a step the page of the pipeline has no words for is named by its id.
export const wordsOf = (id: string) => ({ title: WORDS.get(id)?.title ?? id, what: WORDS.get(id)?.what ?? '' });

// How `Steps` draws a step: it has no `pending` and no `failed`.
export type PathStatus = 'done' | 'running' | 'todo' | 'skipped' | 'error';
const STATUS: Record<PlanStep['state'], PathStatus> = { pending: 'todo', running: 'running', done: 'done', failed: 'error', skipped: 'skipped' };
export const UP_TO_DATE = 'Già aggiornata';
const SAID: Record<PlanStep['state'], string> = { pending: 'In attesa', running: 'In corso', done: 'Completata', failed: 'Non riuscita', skipped: UP_TO_DATE };

// How long from one time of the plan to another, or to `now` where it has no end; empty where there is no start.
export function duration(from: string | undefined, to: string | undefined, now: number): string {
  const seconds = Math.round(((to ? Date.parse(to) : now) - (from ? Date.parse(from) : NaN)) / 1000);
  return !(seconds >= 0) ? '' : seconds < 60 ? `${seconds} s` : `${Math.floor(seconds / 60)} min ${seconds % 60} s`;
}

const cause = (entry: Pick<PlanStep, 'cause' | 'remedy'>) => [entry.cause, entry.remedy && `Rimedio: ${entry.remedy}`].filter(Boolean).join(' · ');

export type StepRow = { id: string; label: string; what: string; status: PathStatus; note: string; time: string };
// The steps of the plan, in its order: the state for `Steps`, a note (why one failed, that one is up to date, how far the one under
// way is) and its time.
export function planSteps(s: Run, now = Date.now()): StepRow[] {
  const progress = s.server?.run?.progress;
  return (planOf(s)?.steps ?? []).map((step): StepRow => {
    const { title, what } = wordsOf(step.id);
    const far = step.state === 'running' && progress?.step === step.id && progress.total ? ` · ${progress.done}/${progress.total}` : '';
    const why = step.state === 'failed' ? cause(step) : '';
    return { id: step.id, label: title, what, status: STATUS[step.state] ?? 'todo', note: [SAID[step.state] + far, why].filter(Boolean).join(' · '),
      time: step.started_at ? duration(step.started_at, step.ended_at, now) : '' };
  });
}

// What an action does, by its kind (the closed list `plan.ACTIONS`), with what it is on.
const languages = (action: PlanAction) => action.target.languages?.join(', ') || 'file senza linguaggio';
const KIND: Record<PlanAction['kind'], (action: PlanAction) => string> = {
  read: action => `Lettura del codice: ${languages(action)}`,
  recognize: () => 'Riconoscimento delle tecnologie',
  model: action => `Modello di build: ${action.target.source ?? ''}`,
  entries: action => `Punti di ingresso: ${action.target.source ?? ''}`,
  resolve: action => `Chiamate: ${languages(action)}`,
  observe: action => `Esecuzione dei test: ${languages(action)}`,
  explore: action => `Esplorazione dell’app in ${action.target.root ?? ''}`,
  assemble: () => 'Unione dei grafi',
};
const ACTION_STATE: Record<PlanAction['state'], [string, BadgeTone | undefined]> = {
  pending: ['In attesa', undefined], running: ['In corso', 'info'], done: ['Fatta', 'success'], failed: ['Non riuscita', 'danger'],
  skipped: [UP_TO_DATE, 'success'], not_possible: ['Non possibile', 'warning'], awaiting_approval: ['Attende la tua risposta', 'warning'],
};
const NETWORK: Record<string, string> = { registries: 'registri dei pacchetti' };

export type ActionRow = {
  id: string; step: string; title: string; detail: string; state: string; tone?: BadgeTone; facts: string[]; note: string; hosts: string[];
  waiting: boolean;  // it waits for the person's answer on its hosts, in the window of the hosts
};
// An action in words: what it does, the tool or the adapter, its state, the three facts of where it runs, and why it cannot.
export function actionRow(action: PlanAction): ActionRow {
  const adapter = action.id.startsWith(action.step + ':') ? action.id.slice(action.step.length + 1) : '';
  const tools = action.tools?.length ? action.tools.join(', ') : adapter;
  const [state, tone] = ACTION_STATE[action.state] ?? [action.state, undefined];
  const files = action.target.files !== undefined ? plural(action.target.files, 'file', 'file')
    : action.target.technologies !== undefined ? plural(action.target.technologies, 'tecnologia', 'tecnologie') : '';
  const waiting = action.state === 'awaiting_approval';
  return {
    id: action.id, step: action.step, title: KIND[action.kind]?.(action) ?? action.id, detail: [tools && `Strumento: ${tools}`, files].filter(Boolean).join(' · '),
    state, tone, waiting, hosts: action.hosts ?? [],
    facts: [
      action.project_code ? 'Esegue il codice del progetto' : 'Non esegue il codice del progetto',
      action.container ? 'Nel container' : 'Sull’host, senza eseguire nulla',
      action.network?.length ? `Rete: ${action.network.map(name => NETWORK[name] ?? name).join(', ')}` : 'Nessuna rete dichiarata',
    ],
    note: waiting ? `Host da approvare: ${(action.hosts ?? []).join(', ')}` : action.state === 'failed' || action.state === 'not_possible' ? cause(action) : '',
  };
}
export const actionsOf = (s: Run, step: string): ActionRow[] => (planOf(s)?.actions ?? []).filter(action => action.step === step).map(actionRow);

// The action under way, and how far it is where the run's progress is of its step.
export function currentAction(s: Run): { action: ActionRow; done: number; total: number } | null {
  const running = planOf(s)?.actions.find(action => action.state === 'running');
  if (!running) return null;
  const progress = s.server?.run?.progress;
  if (!progress || progress.step !== running.step || !progress.total) return { action: actionRow(running), done: 0, total: 0 };
  return { action: actionRow(running), done: progress.done, total: progress.total };
}

// What the run says it does not know: the plan's gaps, why a step or an action failed or cannot be done, the pass of the graph of the
// calls, and the graph's own. None comes from the events.
export function planGaps(s: Run & Pick<Snapshot, 'graph'>): string[] {
  const plan = planOf(s), lines: string[] = [];
  for (const gap of plan?.gaps ?? []) lines.push(gap.detail);
  for (const step of plan?.steps ?? []) if (step.state === 'failed') lines.push(`${wordsOf(step.id).title}: ${cause(step) || 'non riuscita'}`);
  for (const action of plan?.actions ?? []) {
    if (action.state === 'failed' || action.state === 'not_possible') lines.push(`${actionRow(action).title}: ${cause(action) || actionRow(action).state}`);
  }
  if (passAlert(s)) lines.push('Grafo delle chiamate non rifinito: ' + (pass(s).reason || passWord(s)));
  if (s.graph?.unassigned.count) lines.push(`${number(s.graph.unassigned.count)} file non assegnati a un modulo.`);
  for (const gap of s.graph?.gaps ?? []) lines.push(gap.reason);
  return [...new Set(lines)];
}

const finished = (rows: readonly StepRow[]) => rows.filter(row => row.status === 'done' || row.status === 'skipped').length;
// How many of its steps are done, beside the title.
export function planCount(s: Run): string {
  const rows = planSteps(s);
  return `${finished(rows)} di ${rows.length} passi completati`;
}
// How far the plan is: its steps done, and the part of the one under way the progress says.
export function planPercent(s: Run): number {
  const rows = planSteps(s), progress = s.server?.run?.progress;
  if (!ctx(s) || !rows.length) return 0;
  const running = rows.find(row => row.status === 'running');
  const part = running && progress?.step === running.id && progress.total ? progress.done / progress.total : 0;
  return Math.round(100 * (finished(rows) + part) / rows.length);
}

const PHASE: Record<string, string> = {
  fresh: 'Pipeline completata', unavailable: 'Pipeline completata con lacune',
  failed: 'Pipeline conclusa, grafo delle chiamate non rifinito', off: 'Passaggio del grafo spento',
};
// The step under way by its title, else how the run ended.
export const planPhase = (s: Run) =>
  planSteps(s).find(row => row.status === 'running')?.label ?? PHASE[pass(s).state ?? ''] ?? 'In attesa del passaggio del grafo';

// The status row: the state, what is under way, and how far it is where that is known. A step under way is said by its title: the
// row stays one line at 620 px.
export function statusOf(s: Run & Pick<Snapshot, 'serverError'>): { state: string; tone?: BadgeTone; text: string; percent: number | null } {
  if (s.serverError) return { state: 'Errore', tone: 'danger', text: 'Server non raggiungibile', percent: null };
  if (!s.server) return { state: 'Lettura', tone: 'info', text: 'Lettura dello stato del server…', percent: null };
  const work = preparation(s.server.job);
  if (isPreparing(s)) return { state: 'Preparazione in corso', tone: 'info', text: work?.step ?? '', percent: null };
  if (!ctx(s)) return { state: 'Nessuna repository', text: work ? `Preparazione non riuscita (${work.step})` : '', percent: null };
  const running = !complete(s) || planSteps(s).some(row => row.status === 'running');
  return { state: running ? 'Analisi in corso' : 'Contesto pronto', tone: running ? 'info' : 'success', text: planPhase(s),
    percent: running ? planPercent(s) : null };
}

// What a run may reach and where it runs, before anything of the project is run: the registries, the hosts approved and blocked,
// that every other host asks in the app, and the container engine, or why there is none.
export function policyFacts(policy: Policy): { name: string; value: string; code?: boolean }[] {
  const { network, container } = policy;
  return [
    { name: 'Registri aperti', value: network.canonical.join(', ') || '—', code: true },
    { name: 'Host approvati', value: network.approved.join(', ') || 'Nessuno', code: network.approved.length > 0 },
    { name: 'Host bloccati', value: network.blocked.join(', ') || 'Nessuno', code: network.blocked.length > 0 },
    { name: 'Ogni altro host', value: 'Chiede la tua risposta in questa app' },
    { name: 'Container', value: container.engine === 'off' ? ['Spento', container.cause, container.remedy && `Rimedio: ${container.remedy}`].filter(Boolean).join(' · ')
      : container.engine === 'daodan' ? 'Il motore di Daodan' : 'Il motore di container dell’utente' },
  ];
}
