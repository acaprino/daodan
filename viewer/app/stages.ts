// The path of the analysis: its steps in their order, each with how it is and, when it cannot be opened, why; and the foot of the
// step on the screen: the way back, and the one action that goes on.
import { plural } from '../src/words.ts';
import { accessible, isPreparing, sameChoice } from './repository.ts';
import { runCount, runPercent, steps } from './run.ts';
import { complete, ctx, pass, slug } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';
import { STAGES } from './storage.ts';
import type { Stage } from './storage.ts';

export type StageState = 'done' | 'running' | 'todo' | 'error';
export const STAGE_LABEL: Record<Stage, string> = { repository: 'Repository', premap: 'Pre-mappa', analysis: 'Analisi', synthesis: 'Sintesi e grafo' };
// `detail`: what the step found, or what it is for; `meta`: how far it is; `reason`: why it cannot be opened, empty when it can.
export type StageRow = { id: Stage; label: string; detail: string; state: StageState; meta: string; reason: string };

export function stages(s: Pick<Snapshot, 'server' | 'premap' | 'premapError' | 'events'>): StageRow[] {
  const c = ctx(s), list = steps(s), over = complete(s);
  const noContext = c ? '' : 'Scegli prima una repository e un branch.';
  const running = c !== null && (!over || list.some(step => step.status === 'running'));
  const failed = pass(s).state === 'failed' || list.some(step => step.status === 'failed');
  const row = (id: Stage, state: StageState, detail: string, reason: string, meta = ''): StageRow => ({ id, label: STAGE_LABEL[id], detail, state, meta, reason });
  return [
    row('repository', isPreparing(s) ? 'running' : s.server?.job?.state === 'failed' ? 'error' : c ? 'done' : 'todo',
      c ? `${slug(c)} · ${c.branch}` : 'GitHub e branch', ''),
    row('premap', !c ? 'todo' : s.premapError ? 'error' : 'done',
      c && s.premap ? `${plural(s.premap.files.length, 'file', 'file')} · ${plural(s.premap.units.length, 'unità tecnica', 'unità tecniche')}` : 'Inventario e tecnologie', noContext),
    row('analysis', !c ? 'todo' : running ? 'running' : failed ? 'error' : 'done', c ? runCount(s) : 'Pipeline e costruzione', noContext, running ? `${runPercent(s)}%` : ''),
    row('synthesis', over ? 'done' : 'todo', 'Risultati e lacune', noContext || (over ? '' : 'La sintesi è pronta quando la pipeline è conclusa.')),
  ];
}

// What the solid button does: the check of the address, the branch chosen, the step it goes to, or the graph.
export type Act = 'verify' | 'select' | 'graph' | Stage;
// `busy`: its word while what it asked for is under way, empty otherwise; `note`, beside it: why it waits, or what comes after it.
export type Foot = { back: Stage | null; label: string; act: Act; off: boolean; busy: string; note: string };

export function footOf(s: Pick<Snapshot, 'kept' | 'server' | 'checked' | 'branch' | 'checking' | 'selecting'>): Foot {
  const stage = s.kept.analysisStage, back = STAGES[STAGES.indexOf(stage) - 1] ?? null;
  const foot = (act: Act, label: string, note: string, wait = ''): Foot =>
    ({ back, label, act, off: wait === 'off', busy: wait === 'off' ? '' : wait, note });
  const then = (next: Stage) => `Poi: ${STAGE_LABEL[next]}`;
  if (stage === 'premap') return foot('analysis', 'Continua', then('analysis'));
  if (stage === 'analysis') return complete(s) ? foot('synthesis', 'Continua', then('synthesis')) : foot('synthesis', 'Continua', 'Attendi la fine della pipeline.', 'off');
  if (stage === 'synthesis') return foot('graph', 'Apri il grafo', 'Ultimo passo');
  // The server starts the analysis as it prepares the branch: the button that asks for it says so.
  if (isPreparing(s) || s.selecting) return foot('select', 'Avvia l’analisi', 'Preparazione in corso.', 'Preparazione…');
  if (s.checking) return foot('verify', 'Verifica accesso', 'Verifica in corso.', 'Verifica…');
  if (sameChoice(s)) return foot('premap', 'Continua', then('premap'));
  if (accessible(s)) return foot('select', 'Avvia l’analisi', then('premap'));
  if (!s.kept.repositoryUrl.trim()) return foot('verify', 'Verifica accesso', 'Scrivi l’URL della repository.', 'off');
  return foot('verify', 'Verifica accesso', 'Poi: il branch');
}
