import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DATA } from '../pipeline/data.ts';
import { detailOf, groupsOf, legendOf, rowId, sceneOf, stepId } from '../pipeline/tree.ts';

const choice = (id: string) => DATA.choices.find(item => item.id === id)!;
const hangsFrom = (scene: ReturnType<typeof sceneOf>, name: string) => scene.edges.find(edge => edge.to === `row:${name}`);

test('every thing a step uses is in a step of both orders, and the steps of the path are numbered in their order', () => {
  for (const mode of ['today', 'plan'] as const) {
    const keys = new Set(DATA.steps[mode].map(step => step.key));
    for (const row of DATA.rows) assert.ok(keys.has(row[mode]), `${row.name}: ${row[mode]}`);
    const scene = sceneOf(DATA, mode, null);
    assert.deepEqual([...scene.steps.values()].flat(), [...scene.steps.keys()].map((_, index) => index + 1));
    assert.equal(scene.shown, DATA.rows.length);
    assert.equal(scene.nodes.length, DATA.rows.length + DATA.steps[mode].length);
    assert.equal(new Set(scene.nodes.map(node => node.id)).size, scene.nodes.length);
    const ids = new Set(scene.nodes.map(node => node.id));
    for (const edge of scene.edges) assert.ok(ids.has(edge.from) && ids.has(edge.to), edge.id);
  }
  assert.equal(sceneOf(DATA, 'today', null).steps.size, 7);
  assert.equal(sceneOf(DATA, 'plan', null).steps.size, 8);
});

test('a framework brings its languages and its build tools with it, and what is for every project', () => {
  const scene = sceneOf(DATA, 'today', choice('fw:next'));
  const ids = new Set(scene.nodes.map(node => node.id));
  for (const name of ['next', 'noir', 'npm', 'scip-typescript', 'esplorazione', 'stack-analyser']) assert.ok(ids.has(`row:${name}`), name);
  for (const name of ['cargo', 'scip-rust', 'nuxt', 'lettore python']) assert.ok(!ids.has(`row:${name}`), name);
  assert.ok(scene.shown < DATA.rows.length && scene.boxed > 0);
  assert.deepEqual(legendOf(scene).map(entry => entry.count), [scene.shown - scene.boxed, scene.boxed, undefined]);
});

test('the framework tools hang from the structure today, and from the entry points in the plan, where the stack says when', () => {
  const today = hangsFrom(sceneOf(DATA, 'today', choice('fw:next')), 'next')!;
  assert.deepEqual([today.from, today.label, today.style], [stepId('s3'), 'se un package.json dichiara next', 'dashed']);
  const plan = hangsFrom(sceneOf(DATA, 'plan', choice('fw:next')), 'next')!;
  assert.deepEqual([plan.from, plan.label], [stepId('p5'), 'se il passo 3 ha trovato Next.js']);
});

test('the details of a thing say when, with what, at which version and where; of a step what it does and writes', () => {
  const noir = DATA.rows.find(row => row.name === 'noir')!;
  const said = detailOf(DATA, 'today', rowId(noir))!;
  assert.equal(said.name, 'noir');
  assert.deepEqual(said.facts.find(fact => fact.name === 'Versione'), { name: 'Versione', value: noir.ver, code: true });
  assert.equal(said.facts.find(fact => fact.name === 'Dove gira')!.value, 'Solo nel container');
  const step = detailOf(DATA, 'plan', stepId('p3'))!;
  assert.deepEqual(step.facts.map(fact => fact.name), ['Che cosa fa', 'Scrive', 'Nome nel codice']);
  assert.equal(detailOf(DATA, 'today', stepId('p3')), null);
  assert.equal(detailOf(DATA, 'today', 'row:none'), null);
});

test('the choices are in their groups, in the order of the data', () => {
  const groups = groupsOf(DATA);
  assert.deepEqual(groups.map(group => group.label), ['Linguaggi', 'Strumenti di build', 'Framework']);
  assert.equal(groups.flatMap(group => group.options).length, DATA.choices.length);
});
