import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  askedState, askedText, askedTitle, askedTone, findingPlace, findingSeverity, findingText, findingTone, gapText, questionProblem, runProblem,
} from '../src/requests.ts';

const asked = { id: 3, kind: 'review', scope: 'changeset', text: '', state: 'pending' };

test('a feature and a free prompt need their text, the other scopes do not', () => {
  const problem = (scope: string, text: string) => questionProblem({ kind: 'review', scope, text });
  assert.deepEqual(['global', 'changeset'].map(scope => problem(scope, '')), ['', '']);
  assert.equal(problem('feature', '  '), 'Scrivi il nome della funzionalità.');
  assert.equal(problem('prompt', ''), 'Scrivi le indicazioni per la sessione.');
  assert.deepEqual(['feature', 'prompt'].map(scope => problem(scope, 'Pagamenti')), ['', '']);
});

test("a run's name is the server's: lower case, digits and single hyphens", () => {
  assert.deepEqual(['run', 'run-2', '2026-11-24'].map(runProblem), ['', '', '']);
  assert.equal(runProblem(''), 'Scrivi il nome del run.');
  for (const name of ['Run', 'mio run', 'run--2', '-run', 'run-', 'run\n']) assert.match(runProblem(name), /^Solo minuscole/);
});

test('a request says what was asked, its state, and what the session said when it closed it', () => {
  assert.equal(askedTitle(asked), '#3 Review · Changeset');
  assert.equal(askedTitle({ ...asked, kind: 'map', scope: 'feature' }), '#3 Mappa · Funzionalità');
  assert.equal(askedTitle({ ...asked, kind: 'altro', scope: 'prompt' }), '#3 altro · Prompt libero');
  assert.equal(askedText(asked), '');
  assert.equal(askedText({ ...asked, text: 'Pagamenti', message: 'Due finding' }), 'Pagamenti\nDue finding');
  assert.deepEqual(['pending', 'taken', 'done', 'altro'].map(state => askedState({ ...asked, state })),
    ['in attesa della sessione', 'in corso', 'conclusa', 'altro']);
  assert.deepEqual(['pending', 'taken', 'done', 'altro'].map(state => askedTone({ ...asked, state })), [null, null, 'success', null]);
});

test('a finding says its place, its words and its severity, and what it does not say is said to be missing', () => {
  const finding = { file: 'web/checkout.tsx', line: 12, severity: 'High', title: 'Premessa', example: 'un esempio', request: 1 };
  assert.deepEqual([findingPlace(finding), findingText(finding), findingSeverity(finding)], ['web/checkout.tsx:12', 'Premessa · un esempio', 'gravità alta']);
  assert.equal(findingSeverity({ severity: 'altra', request: 1 }), 'gravità altra');
  assert.equal(findingText({ premise: 'Solo la premessa', request: 1 }), 'Solo la premessa');
  assert.equal(findingPlace({ file: 'web/api.ts', request: 1 }), 'web/api.ts:?');
  assert.deepEqual([findingPlace({ request: 1 }), findingText({ request: 1 }), findingSeverity({ request: 1 })],
    ['file non indicato', 'senza titolo', 'gravità non indicata']);
  assert.deepEqual(['Critical', 'High', 'Medium', 'Low', undefined].map(severity => findingTone({ severity, request: 1 })),
    ['danger', 'danger', 'warning', 'warning', 'warning']);
});

test('a gap is its words, or what it holds', () => {
  assert.equal(gapText('non letto'), 'non letto');
  assert.equal(gapText({ path: 'a.json' }), '{"path":"a.json"}');
});
