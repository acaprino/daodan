import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { actionsOf, currentAction, duration, planCount, planGaps, planPercent, planSteps, policyFacts, statusOf, wordsOf } from '../app/plan.ts';
import type { Plan } from '../app/server.ts';
import type { Snapshot } from '../app/snapshot.ts';

// The plan as the server gives it (`tests/test_codebase_map_plan.py` checks it against the server's closed lists).
const PLAN: Plan = JSON.parse(readFileSync(new URL('./plan.json', import.meta.url), 'utf8'));
const context = { repository: { owner: 'demo', name: 'shop' }, branch: 'main', commit: '1'.repeat(40), run_id: 'r1' };
const of = (plan: Plan | null, more: object = {}, server: object = {}) => ({
  server: { context, job: { state: 'ready' }, run: { pass: { state: 'running', reason: null }, progress: null, plan, ...more }, ...server },
  serverError: '', events: [], graph: null,
}) as unknown as Snapshot;

test('the steps are those of the plan, in its order, with the words of the page of the pipeline', () => {
  const rows = planSteps(of(PLAN), Date.parse('2026-11-28T10:02:10Z'));
  assert.deepEqual(rows.map(row => row.id), PLAN.steps.map(step => step.id));
  assert.deepEqual(rows.map(row => row.label), ['Elenco dei file', 'Lettura del codice', 'Tecnologie', 'Moduli', 'Punti di ingresso', 'Chiamate',
    'Esecuzione', 'Grafo finale']);
  assert.deepEqual(rows.map(row => row.status), ['done', 'done', 'done', 'done', 'skipped', 'running', 'todo', 'todo']);
  assert.deepEqual(rows.map(row => row.time), ['', '', '4 s', '1 min 6 s', '0 s', '1 min 0 s', '', '']);
  assert.equal(rows[4].note, 'Già aggiornata');
  // A plan of seven has seven steps: the app keeps no list of its own.
  const seven = { ...PLAN, steps: PLAN.steps.filter(step => step.id !== 'run_and_observe') };
  assert.deepEqual(planSteps(of(seven)).map(row => row.id), seven.steps.map(step => step.id));
  assert.equal(planCount(of(seven)), '5 di 7 passi completati');
  // A step the page has no words for is named by its id; no plan, no steps.
  assert.deepEqual(wordsOf('publish'), { title: 'publish', what: '' });
  assert.deepEqual(planSteps(of(null)), []);
});

test('a step under way says how far it is, and one that failed says why and what to do', () => {
  const failed = { ...PLAN, steps: PLAN.steps.map(step => (step.id === 'find_modules' ? { ...step, state: 'failed' as const, cause: 'disco pieno', remedy: 'libera spazio' } : step)) };
  const rows = planSteps(of(failed, { progress: { step: 'link_calls', done: 2, total: 4 } }));
  assert.equal(rows[3].note, 'Non riuscita · disco pieno · Rimedio: libera spazio');
  assert.equal(rows[5].note, 'In corso · 2/4');
  assert.equal(planPercent(of(PLAN, { progress: { step: 'link_calls', done: 2, total: 4 } })), Math.round(100 * 5.5 / 8));
  assert.equal(duration('2026-11-28T10:00:00Z', undefined, Date.parse('2026-11-28T10:00:09Z')), '9 s');
  assert.equal(duration(undefined, undefined, 0), '');
});

test('an action says what it does, where it runs, and an action waiting names its hosts', () => {
  const modelling = actionsOf(of(PLAN), 'find_modules');
  assert.deepEqual(modelling.map(row => row.id), ['find_modules:gradle', 'find_modules:go']);
  const [waiting] = modelling;
  assert.deepEqual([waiting.title, waiting.state, waiting.tone, waiting.waiting, waiting.hosts, waiting.note],
    ['Modello di build: gradle', 'Attende la tua risposta', 'warning', true, ['repo.example.com'], 'Host da approvare: repo.example.com']);
  assert.deepEqual(waiting.facts, ['Esegue il codice del progetto', 'Nel container', 'Rete: registri dei pacchetti']);
  const [go, python] = actionsOf(of(PLAN), 'link_calls');
  assert.deepEqual([go.title, go.detail, go.state], ['Chiamate: go', 'Strumento: scip-go · 3 file', 'In corso']);
  assert.deepEqual([python.state, python.note], ['Non possibile', 'no container engine answers · Rimedio: start Docker or Podman']);
  const [read] = actionsOf(of(PLAN), 'read_code');
  assert.deepEqual(read.facts, ['Non esegue il codice del progetto', 'Sull’host, senza eseguire nulla', 'Nessuna rete dichiarata']);
  assert.deepEqual(actionsOf(of(PLAN), 'recognize_stack').map(row => row.detail), ['Strumento: stack-analyser · 4 tecnologie']);
  assert.deepEqual(currentAction(of(PLAN, { progress: { step: 'link_calls', done: 1, total: 3 } }))?.action.id, 'link_calls:scip-go');
  assert.deepEqual(currentAction(of(PLAN, { progress: { step: 'find_modules', done: 1, total: 3 } }))?.total, 0);
});

test('an app\'s exploration and the tests open the window of their command; a stated one says who stated it', () => {
  const [tests, app] = actionsOf(of(PLAN), 'run_and_observe');
  assert.deepEqual([tests.commandAt, tests.command], [{ kind: 'tests', root: '.' }, '']);
  assert.deepEqual([app.title, app.commandAt, app.command], ['Esplorazione dell’app in web', { kind: 'starts', root: 'web' }, '']);
  assert.deepEqual(actionsOf(of(PLAN), 'link_calls').map(row => row.commandAt), [null, null]);
  const stated = (grade: 'confermato' | 'proposto') => ({ ...PLAN, actions: PLAN.actions.map(action =>
    (action.kind === 'explore' ? { ...action, by: grade === 'confermato' ? 'user' as const : 'assistant' as const, grade } : action)) });
  assert.equal(actionsOf(of(stated('proposto')), 'run_and_observe')[1].command, 'Comando proposto dall’assistente');
  assert.equal(actionsOf(of(stated('confermato')), 'run_and_observe')[1].command, 'Comando confermato da te');
});

test('the gaps are the plan\'s and the graph\'s, never the events\'', () => {
  const s = { ...of(PLAN), events: [{ kind: 'gap', message: 'dagli eventi', data: { gap: { detail: 'dagli eventi' } } }],
    graph: { unassigned: { count: 2 }, gaps: [{ reason: 'del grafo' }] } } as unknown as Snapshot;
  assert.deepEqual(planGaps(s), [
    'go: no observer runs its tests, so its graph holds no observed edge',
    'how much a run downloads is not known before it runs: no source gives its size',
    'Chiamate: python: no container engine answers · Rimedio: start Docker or Podman',
    '2 file non assegnati a un modulo.', 'del grafo']);
});

test('the status row follows the plan, and the policy is said before anything runs', () => {
  assert.deepEqual(statusOf(of(PLAN)), { state: 'Analisi in corso', tone: 'info', text: 'Chiamate', percent: Math.round(100 * 5 / 8) });
  const over = of({ ...PLAN, steps: PLAN.steps.map(step => ({ ...step, state: 'done' as const })) }, { pass: { state: 'fresh' } });
  assert.deepEqual(statusOf(over), { state: 'Contesto pronto', tone: 'success', text: 'Pipeline completata', percent: null });
  const facts = policyFacts(PLAN.policy);
  assert.deepEqual(facts.map(fact => fact.name), ['Registri aperti', 'Host approvati', 'Host bloccati', 'Ogni altro host', 'Container']);
  assert.equal(facts[1].value, 'git.example.com');
  const off = policyFacts({ ...PLAN.policy, container: { engine: 'off', cause: 'DAODAN_CONTAINER=off', remedy: 'unset it' } });
  assert.equal(off[4].value, 'Spento · DAODAN_CONTAINER=off · Rimedio: unset it');
});
