import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { firstStep, footOf, onPath, pathRows } from '../app/path.ts';
import { sameChoice } from '../app/repository.ts';
import type { Plan } from '../app/server.ts';
import type { Snapshot } from '../app/snapshot.ts';
import { DEFAULTS, readKept, STORAGE } from '../app/storage.ts';
import type { Kept } from '../app/storage.ts';

const PLAN: Plan = JSON.parse(readFileSync(new URL('./plan.json', import.meta.url), 'utf8'));
const DONE: Plan = { ...PLAN, steps: PLAN.steps.map(step => ({ ...step, state: 'done' as const })) };
const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
const of = (server: object | null, more: object = {}) => ({
  server, serverError: '', events: [], premapError: '', checked: null, checking: false, graph: null, graphLoading: false, ...more,
}) as unknown as Snapshot;
const ready = (plan: Plan | null = DONE, pass = 'fresh') => ({ context, job: { state: 'ready' }, run: { pass: { state: pass }, plan } });

test('the path is «Repository» and then the steps of the plan, in its order, and why a step cannot be opened', () => {
  const rows = pathRows(of(ready(PLAN, 'running')));
  assert.deepEqual(rows.map(row => row.id), ['repository', ...PLAN.steps.map(step => step.id)]);
  assert.deepEqual(rows.map(row => row.state), ['done', 'done', 'done', 'done', 'done', 'skipped', 'running', 'todo', 'todo']);
  assert.deepEqual([rows[0].label, rows[0].detail, rows[3].label, rows[3].meta], ['Repository', 'demo/shop · main', 'Tecnologie', '4 s']);
  // A plan of seven is a path of eight: the app keeps no list of its own.
  const seven = { ...PLAN, steps: PLAN.steps.filter(step => step.id !== 'run_and_observe') };
  assert.equal(pathRows(of(ready(seven))).length, 8);
  // Without a context, Repository alone; while it is prepared, it runs; when the preparation fails, it says so.
  assert.deepEqual(pathRows(of({ job: { state: 'idle' } })).map(row => [row.id, row.state]), [['repository', 'todo']]);
  assert.equal(pathRows(of({ job: { state: 'preparing' } }))[0].state, 'running');
  assert.equal(pathRows(of({ job: { state: 'failed' } }))[0].state, 'error');
  assert.deepEqual([firstStep(of(ready())), firstStep(of({ context, run: null }))], ['list_files', null]);
  assert.deepEqual([onPath(of(ready()), 'repository'), onPath(of(ready()), 'link_calls'), onPath(of(ready(seven)), 'run_and_observe')], [true, true, false]);
});

test('the foot has the way back, one action, and why it waits or what comes after it', () => {
  const at = (analysisStage: Kept['analysisStage'], server: object | null, more: object = {}, repositoryUrl = '') =>
    of(server, { kept: { ...DEFAULTS, analysisStage, repositoryUrl }, branch: '', ...more });
  const foot = (...given: Parameters<typeof at>) => {
    const { back, label, act, off, busy, note } = footOf(at(...given));
    return [back, label, act, off ? 'off' : busy, note];
  };
  const idle = { job: { state: 'idle' } }, done = ready();
  const url = 'https://github.com/demo/shop', commit = context.commit;
  const checked = { state: 'accessible', repository: context.repository, branches: [{ name: 'main', commit }, { name: 'dev', commit }] };
  assert.deepEqual(foot('repository', idle), [null, 'Verifica accesso', 'verify', 'off', 'Scrivi l’URL della repository.']);
  assert.deepEqual(foot('repository', idle, {}, url), [null, 'Verifica accesso', 'verify', '', 'Poi: il branch']);
  assert.deepEqual(foot('repository', idle, { checking: true }, url), [null, 'Verifica accesso', 'verify', 'Verifica…', 'Verifica in corso.']);
  assert.deepEqual(foot('repository', idle, { checked, branch: 'main' }, url), [null, 'Avvia l’analisi', 'select', '', 'Poi: i passi dell’analisi']);
  assert.deepEqual(foot('repository', { job: { state: 'preparing' } }, { checked }, url), [null, 'Avvia l’analisi', 'select', 'Preparazione…', 'Preparazione in corso.']);
  assert.deepEqual(foot('repository', done, { checked, branch: 'main', selecting: true }, url)[3], 'Preparazione…');
  // A step done is looked at, and goes on with its run; another branch, commit or address is another analysis.
  const more = [null, 'Continua', 'list_files', '', 'Poi: Elenco dei file'];
  assert.deepEqual([foot('repository', done), foot('repository', done, {}, url), foot('repository', done, { checked, branch: 'main' }, url)], [more, more, more]);
  assert.equal(foot('repository', done, { checked, branch: 'dev' }, url)[2], 'select');
  assert.equal(foot('repository', done, {}, 'https://github.com/demo/altro')[2], 'verify');
  assert.equal(sameChoice(at('repository', done, {}, 'https://github.com/Demo/Shop')), true);
  assert.deepEqual(foot('repository', { context, job: { state: 'ready' }, run: null }), [null, 'Continua', 'repository', 'off', 'In attesa del piano dell’analisi.']);
  // The steps go on in the plan's order, and the last opens the graph.
  assert.deepEqual(foot('list_files', done), ['repository', 'Continua', 'read_code', '', 'Poi: Lettura del codice']);
  assert.deepEqual(foot('link_calls', done), ['find_entry_points', 'Continua', 'run_and_observe', '', 'Poi: Esecuzione']);
  assert.deepEqual(foot('assemble_graph', done), ['run_and_observe', 'Apri il grafo', 'graph', '', 'Ultimo passo']);
});

test('the step kept is an id of the plan, and the stages of before are not read', () => {
  const storage = (kept: object) => () => ({ getItem: (key: string) => (key === STORAGE ? JSON.stringify(kept) : null), setItem: () => undefined });
  assert.equal(STORAGE, 'daodan-app-v3');
  assert.equal(readKept(storage({ analysisStage: 'link_calls' })).kept.analysisStage, 'link_calls');
  assert.equal(readKept(storage({ analysisStage: 3 })).kept.analysisStage, 'repository');
});
