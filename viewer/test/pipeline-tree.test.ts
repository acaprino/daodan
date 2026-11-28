import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DATA, STEPS } from '../pipeline/data.ts';
import { countOf, detailOf, groupsOf, itemsOf, lineOf, pathOf, rowId, stepId } from '../pipeline/tree.ts';
import type { Path } from '../pipeline/tree.ts';

const choice = (id: string) => DATA.choices.find(item => item.id === id)!;
const names = (path: Path) => new Set([...path.steps, ...path.beside].flatMap(step => step.rows.map(row => row.name)));
const stepOf = (path: Path, name: string) => path.steps.find(step => step.rows.some(row => row.name === name))!;

test('every thing a step uses is in a step of both orders, once, and the path is its numbered steps in their order', () => {
  for (const [mode, keys] of [['today', ['s1', 's2', 's3', 's4', 's5', 's6', 's7']], ['plan', ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8']]] as const) {
    const all = new Set(DATA.steps[mode].map(step => step.key));
    for (const row of DATA.rows) assert.ok(all.has(row[mode]), `${row.name}: ${row[mode]}`);
    const path = pathOf(DATA, mode, null);
    assert.deepEqual(path.steps.map(step => step.key), keys);
    assert.equal(path.steps.length + path.beside.length, DATA.steps[mode].length);
    assert.equal(path.shown, DATA.rows.length);
    assert.equal(names(path).size, DATA.rows.length);
    assert.equal(path.boxed, DATA.rows.filter(row => row.where === 'container').length);
    // Each step can be gone to, and says how much it uses.
    assert.deepEqual(itemsOf(path), path.steps.map(step => ({ label: step.title, meta: countOf(step.rows), status: 'todo' })));
  }
  assert.deepEqual(pathOf(DATA, 'today', null).beside.map(step => step.key), ['after', 'common']);
  assert.deepEqual([countOf([]), countOf(DATA.rows.slice(0, 1)), countOf(DATA.rows.slice(0, 2))], ['0 voci', '1 voce', '2 voci']);
});

test('a framework brings its languages and its build tools with it, and what is for every project', () => {
  const path = pathOf(DATA, 'today', choice('fw:next'));
  const shown = names(path);
  for (const name of ['next', 'noir', 'npm', 'scip-typescript', 'esplorazione', 'stack-analyser']) assert.ok(shown.has(name), name);
  for (const name of ['cargo', 'scip-rust', 'nuxt', 'lettore python']) assert.ok(!shown.has(name), name);
  assert.ok(path.shown < DATA.rows.length && path.boxed > 0 && path.boxed < path.shown);
  assert.equal(path.shown, shown.size);
  // A step with nothing for the choice stays in the path.
  assert.equal(path.steps.length, 7);
});

test('the framework tools are in the structure today, and in the entry points in the plan, where the stack says when', () => {
  const next = DATA.rows.find(row => row.name === 'next')!;
  assert.equal(stepOf(pathOf(DATA, 'today', choice('fw:next')), 'next').key, 's3');
  assert.deepEqual(lineOf(next, 'today'), {
    title: next.ver ? `next ${next.ver}` : 'next', tool: next.tool, contained: true,
    facts: [{ text: 'se un package.json dichiara next' }, { text: 'solo nel container' }],
  });
  assert.equal(stepOf(pathOf(DATA, 'plan', choice('fw:next')), 'next').key, 'p5');
  assert.equal(lineOf(next, 'plan').facts[0].text, 'se il passo 3 ha trovato Next.js');
  // What is still to settle is said on the line, after when and where.
  const open = DATA.rows.find(row => row.status && row.where === 'host')!;
  assert.deepEqual(lineOf(open, 'today').facts.slice(1), [{ text: "sull'host" }, { text: open.status, tone: 'strong' }]);
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

test('the numbered steps of the plan carry the ids of the pipeline, which the app reads from STEPS alone', () => {
  assert.equal(STEPS, DATA.steps);
  assert.deepEqual(pathOf(DATA, 'plan', null).steps.map(step => step.id), ['list_files', 'read_code', 'recognize_stack', 'find_modules',
    'find_entry_points', 'link_calls', 'run_and_observe', 'assemble_graph']);
  assert.ok(STEPS.today.every(step => step.id === undefined) && pathOf(DATA, 'plan', null).beside.every(step => step.id === undefined));
});
