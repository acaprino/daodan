import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import { counted, entryName, headOf, MORE, stepMeta } from '../src/names.ts';

const env = parseEnvelope(JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8')));
const entity = (ref: string) => env.entities.find(item => item.ref === ref);

test('one thing is counted in the singular, none and many in the plural', () => {
  assert.deepEqual([0, 1, 8].map(count => counted(count, 'passo', 'passi')), ['0 passi', '1 passo', '8 passi']);
});

test('the row that opens the rest of a list says how many, in the gender and number of what it holds', () => {
  assert.deepEqual([MORE.steps(1), MORE.steps(3)], ['1 altro passo', 'Altri 3 passi']);
  assert.deepEqual([MORE.links(1), MORE.links(2)], ['1 altro collegamento', 'Altri 2 collegamenti']);
  assert.deepEqual([MORE.evidence(1), MORE.evidence(2)], ['1 altra evidenza', 'Altre 2 evidenze']);
  assert.deepEqual([MORE.files(1), MORE.files(2)], ['1 altro file', 'Altri 2 file']);
});

test('the inspector is named by the element, else by the flow, else by the project', () => {
  const web = entity('component:web'), flow = env.flows[0];
  assert.deepEqual(headOf(env, web, flow), { title: 'Dettaglio', name: 'web', icon: 'structure' });
  assert.deepEqual(headOf(env, undefined, flow), { title: 'Flusso', name: 'pay', icon: 'branch' });
  assert.deepEqual(headOf(env), { title: 'Informazioni sul progetto', name: 'shop', icon: 'info' });
  assert.equal(headOf({ ...env, meta: {} }).name, 'Progetto');
});

test('a step says its route, its site, where its proof comes from and what weakens it', () => {
  const step = { source: 'a', target: 'b', type: 'chiama', origin: 'dedotto', site: 'web/api.ts:4' };
  assert.equal(stepMeta(step), 'web/api.ts:4 · dedotto');
  assert.equal(stepMeta({ ...step, route: ['http', 'POST', '/payments'], confidence: 'sampled', conflict: true }),
    'POST /payments · web/api.ts:4 · dedotto · campionata dal profiler · destinazioni in conflitto');
});

test('an entry the interface has no word for keeps its own', () => {
  assert.equal(entryName(env.flows[0]), "azione dell'utente");
  assert.equal(entryName({ ...env.flows[0], entry_kind: 'altro ingresso' }), 'altro ingresso');
});
