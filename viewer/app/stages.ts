// The stages of the analysis, each with how it is in words and, when it cannot be opened, why.
import { isPreparing } from './repository.ts';
import { steps } from './run.ts';
import { complete, ctx, pass } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';
import type { Stage } from './storage.ts';

export type StageState = 'done' | 'now' | 'todo' | 'failed';
export const STAGE_WORD: Record<StageState, string> = { done: 'fatta', now: 'in corso', todo: 'da fare', failed: 'non riuscita' };
export const STAGE_LABEL: Record<Stage, string> = { repository: 'Repository', premap: 'Pre-mappa', analysis: 'Analisi', synthesis: 'Sintesi e grafo' };
const STAGE_DETAIL: Record<Stage, string> = {
  repository: 'GitHub e branch', premap: 'Inventario e tecnologie', analysis: 'Pipeline e costruzione', synthesis: 'Risultati e lacune',
};
export type StageRow = { id: Stage; label: string; detail: string; state: StageState; reason: string };

export function stages(s: Pick<Snapshot, 'server' | 'premapError' | 'events'>): StageRow[] {
  const chosen = ctx(s) !== null, list = steps(s);
  const noContext = chosen ? '' : 'Scegli prima una repository e un branch.';
  const running = !complete(s) || list.some(step => step.status === 'running');
  const failed = pass(s).state === 'failed' || list.some(step => step.status === 'failed');
  const row = (id: Stage, state: StageState, reason: string): StageRow => ({ id, label: STAGE_LABEL[id], detail: STAGE_DETAIL[id], state, reason });
  return [
    row('repository', isPreparing(s) ? 'now' : s.server?.job?.state === 'failed' ? 'failed' : chosen ? 'done' : 'todo', ''),
    row('premap', !chosen ? 'todo' : s.premapError ? 'failed' : 'done', noContext),
    row('analysis', !chosen ? 'todo' : running ? 'now' : failed ? 'failed' : 'done', noContext),
    row('synthesis', complete(s) ? 'done' : 'todo', noContext || (complete(s) ? '' : 'La sintesi è pronta quando la pipeline è conclusa.')),
  ];
}
