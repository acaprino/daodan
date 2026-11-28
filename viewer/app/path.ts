// The path of the analysis: «Repository», the choice of the context, which is no step of the pipeline, and then the steps of the plan
// in its order; and the foot of the step on the screen: the way back, and the one action that goes on. No list of steps is the app's.
import { accessible, isPreparing, sameChoice } from './repository.ts';
import { planOf, planSteps } from './plan.ts';
import type { PathStatus } from './plan.ts';
import { ctx, slug } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';

export const REPOSITORY = 'repository';
// The steps that show what `/api/app/premap` holds, read when one is on the screen.
export const SHOWS_PREMAP: readonly string[] = ['find_modules', 'assemble_graph'];

// `detail`: what the step found or how it is; `meta`: how long it took.
export type PathRow = { id: string; label: string; detail: string; state: PathStatus; meta: string };

// The plan is of a context: without one the path is «Repository» alone.
export function pathRows(s: Pick<Snapshot, 'server'>): PathRow[] {
  const c = ctx(s);
  return [
    { id: REPOSITORY, label: 'Repository', detail: c ? `${slug(c)} · ${c.branch}` : 'GitHub e branch', meta: '',
      state: isPreparing(s) ? 'running' : s.server?.job?.state === 'failed' ? 'error' : c ? 'done' : 'todo' },
    ...(c ? planSteps(s) : []).map(row => ({ id: row.id, label: row.label, detail: row.note, state: row.status, meta: row.time })),
  ];
}

// The first step of the plan, where the analysis goes once the context is chosen; none while the state has no plan.
export const firstStep = (s: Pick<Snapshot, 'server'>): string | null => planOf(s)?.steps[0]?.id ?? null;
// Whether the step is on the path: «Repository», or a step of the plan.
export const onPath = (s: Pick<Snapshot, 'server'>, id: string) => id === REPOSITORY || (planOf(s)?.steps ?? []).some(step => step.id === id);

// What the solid button does: the check of the address, the branch chosen, the graph, or the step it goes to.
export type Act = 'verify' | 'select' | 'graph' | string;
// `busy`: its word while what it asked for is under way, empty otherwise; `note`, beside it: why it waits, or what comes after it.
export type Foot = { back: string | null; label: string; act: Act; off: boolean; busy: string; note: string };

export function footOf(s: Pick<Snapshot, 'kept' | 'server' | 'checked' | 'branch' | 'checking' | 'selecting'>): Foot {
  const rows = pathRows(s), at = rows.findIndex(row => row.id === s.kept.analysisStage);
  const back = at > 0 ? rows[at - 1].id : null, next = at >= 0 ? rows[at + 1] : undefined;
  const foot = (act: Act, label: string, note: string, wait = ''): Foot =>
    ({ back, label, act, off: wait === 'off', busy: wait === 'off' ? '' : wait, note });
  const then = next ? `Poi: ${next.label}` : 'Poi: i passi dell’analisi';
  if (at > 0) return next ? foot(next.id, 'Continua', then) : foot('graph', 'Apri il grafo', 'Ultimo passo');
  // The server starts the analysis as it prepares the branch: the button that asks for it says so.
  if (isPreparing(s) || s.selecting) return foot('select', 'Avvia l’analisi', 'Preparazione in corso.', 'Preparazione…');
  if (s.checking) return foot('verify', 'Verifica accesso', 'Verifica in corso.', 'Verifica…');
  if (sameChoice(s)) return next ? foot(next.id, 'Continua', then) : foot(REPOSITORY, 'Continua', 'In attesa del piano dell’analisi.', 'off');
  if (accessible(s)) return foot('select', 'Avvia l’analisi', then);
  if (!s.kept.repositoryUrl.trim()) return foot('verify', 'Verifica accesso', 'Scrivi l’URL della repository.', 'off');
  return foot('verify', 'Verifica accesso', 'Poi: il branch');
}
