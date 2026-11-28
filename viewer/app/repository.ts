// The repository, in words: its address, what the check found, how its preparation goes, and the facts of the run in view.
import { ctx, slug } from './snapshot.ts';
import type { Snapshot } from './snapshot.ts';
import type { Checked, Context, Job } from './server.ts';

export function preferredBranch(branches: { name: string }[], fallback: string) {
  const names = branches.map(b => b.name);
  return names.includes('main') ? 'main' : names.includes('master') ? 'master' : fallback;
}

// The owner and the name of a GitHub address, or null when it is not one.
export function repositorySlug(url: string): string | null {
  const value = url.trim();
  const normalized = value.startsWith('github.com/') ? 'https://' + value : value;
  const match = /^https:\/\/github\.com\/([A-Za-z0-9-]+)\/([A-Za-z0-9._-]+)\/?$/i.exec(normalized);
  const name = match?.[2].replace(/\.git$/, '');
  return match && name && !['.', '..'].includes(name) ? match[1] + '/' + name : null;
}
export const urlError = (url: string) => (url.trim()
  ? 'Usa un URL https://github.com/proprietario/repository, senza percorsi aggiuntivi.' : 'Inserisci l’URL GitHub della repository.');

export const isPreparing = (s: Pick<Snapshot, 'server'>) => s.server?.job?.state === 'preparing';
export const accessible = (s: Pick<Snapshot, 'checked'>) => (s.checked?.state === 'accessible' ? s.checked : null);

// Whether what is written and chosen is the run in view, or nothing is: the path goes on with that run. A branch that has moved since is
// another one.
export function sameChoice(s: Pick<Snapshot, 'server' | 'kept' | 'checked' | 'branch'>): boolean {
  const c = ctx(s), url = s.kept.repositoryUrl, repo = accessible(s);
  if (!c || (url.trim() && repositorySlug(url)?.toLowerCase() !== slug(c).toLowerCase())) return false;
  return !repo || (s.branch === c.branch && repo.branches.some(b => b.name === c.branch && b.commit === c.commit));
}
// What starts again when another repository or branch is chosen.
export const RESTART = 'I passi dell’analisi ripartono dal branch scelto; lo stesso commit riusa l’analisi già fatta.';

type Feedback = { tone: 'error' | 'warning'; title: string; message: string };
const FEEDBACK: Record<string, Feedback> = {
  not_accessible: { tone: 'error', title: 'Repository non accessibile senza login.',
    message: 'Potrebbe non esistere o richiedere permessi. Il login GitHub non è disponibile in questa versione.' },
  network: { tone: 'error', title: 'Errore di rete.', message: 'Riprova la verifica. Il login non risolve un errore di connessione.' },
  empty: { tone: 'warning', title: 'La repository non ha branch.', message: 'Non c’è nulla da analizzare.' },
};
// What the check said of a repository that cannot be read.
export function accessFeedback(checked: Checked | null): Feedback | null {
  if (!checked || checked.state === 'accessible') return null;
  const found = FEEDBACK[checked.state] ?? FEEDBACK.not_accessible;
  return { ...found, message: found.message + (checked.detail ? ` (${checked.detail})` : '') };
}

const JOB_STEP: Record<string, string> = { checkout: 'Checkout del branch', snapshot: 'Snapshot del codice e modello di build' };
export type Preparation = { state: 'preparing' | 'failed'; step: string; detail: string };
// How the preparation of the branch goes: while it goes, and when it failed.
export function preparation(job: Job | undefined): Preparation | null {
  const state = job?.state === 'preparing' ? 'preparing' : job?.state === 'failed' ? 'failed' : null;
  if (!job || !state) return null;
  return { state, step: JOB_STEP[job.step ?? ''] ?? job.step ?? '', detail: job.detail ?? '' };
}

// A commit as it is read: its first twelve signs.
export const short = (commit: string) => commit.slice(0, 12);
// The facts of the run in view, to read and copy.
export function repositoryContext(s: Pick<Snapshot, 'server'>): { name: string; value: string }[] {
  const c: Context | null = ctx(s);
  return c ? [
    { name: 'Repository', value: slug(c) },
    { name: 'Branch', value: c.branch },
    { name: 'Commit', value: short(c.commit) },
    { name: 'Run', value: c.run_id },
  ] : [];
}
