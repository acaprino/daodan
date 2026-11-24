import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import type { Envelope, Flow } from '../src/envelope.ts';
import type { Layout } from '../src/layoutClient.ts';
import { dataLinks, flowFocus, project } from '../src/projection.ts';
import { graphOf, layoutKeyOf, sceneOf } from '../src/scene.ts';
import type { Drawing, Scene } from '../src/scene.ts';

const env = parseEnvelope(JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8')));
const [PAY, NIGHTLY] = env.flows;
const WEB = 'component:web@root', SERVER = 'component:server@root', PROVIDER = 'external:card payment provider@root';
const MONEY = 'imports:file:web/checkout.tsx->file:shared/money.ts';  // the relation from web to server

// What the page draws: at rest the relations and the data links, with a flow the relations and the flow's lines.
function drawing(envelope: Envelope = env, flow?: Flow, scope: string | null = null): Drawing {
  const projection = project(envelope, 'logical', scope);
  return { projection, edges: [...projection.edges, ...(flow ? flowFocus(envelope, flow.ref, projection).edges : dataLinks(envelope, projection))], direction: 'right' };
}
// What ELK answers: a box and a route of its own for each.
const layoutOf = (of: Drawing): Layout => ({
  nodes: Object.fromEntries(of.projection.nodes.map((node, n) => [node.id, { x: 10 * n, y: 100 * n, width: 224, height: 64 }])),
  edges: Object.fromEntries(of.edges.map((edge, n) => [edge.id, [{ x: n, y: 1 }, { x: n, y: 2 }]])),
});
const scene = (of: Drawing, selected: string | null = null, flow?: Flow) => sceneOf(of, layoutOf(of), selected, flow);
const node = (from: Scene, id: string) => from.nodes.find(item => item.id === id);
const line = (from: Scene, id: string) => from.edges.find(item => item.id === id);
const numbers = (of: Flow, scope: string | null = null, envelope: Envelope = { ...env, flows: [of] }) =>
  Object.fromEntries(scene(drawing(envelope, of, scope), null, of).steps!);

test('nodes and lines are where ELK put them: a size for all, a route each, and the facing sides for a line with none', () => {
  const at = drawing(), layout = layoutOf(at);
  layout.edges[`${WEB}->${SERVER}`] = null;
  const drawn = sceneOf(at, layout);
  assert.equal(drawn.nodes.length, 8);
  for (const item of drawn.nodes) {
    const { x, y, width, height } = item;
    assert.deepEqual({ x, y, width, height }, layout.nodes[item.id]);
  }
  for (const item of drawn.edges) assert.deepEqual(item.points, layout.edges[item.id!]);
  assert.equal(line(drawn, `${WEB}->${SERVER}`)?.points, null);
});

test('a node has its name, what it is, its icon, and only a group is entered and says how many it contains', () => {
  const drawn = scene(drawing());
  const said = (id: string) => { const { label, detail, icon, external, openLabel, hiddenCount } = node(drawn, id)!; return [label, detail, icon, external, openLabel, hiddenCount]; };
  assert.deepEqual(said(WEB), ['web', 'componente', 'structure', false, 'Apri web', 3]);
  assert.deepEqual(said('store:db/orders@root'), ['db/orders', 'database', 'data', false, undefined, undefined]);
  // «esterno» is the canvas's own word for `external`: the second line does not say it again.
  assert.deepEqual(said(PROVIDER), ['card payment provider', 'servizio o API', 'service', true, undefined, undefined]);
  assert.deepEqual(said('external:api gateway@root'), ['API gateway', 'gateway · incompleto', 'gateway', true, undefined, undefined]);
  assert.equal(drawn.refs.get(WEB), 'component:web');
});

test('a kind with no icon has none, and no other thing\'s', () => {
  const at = drawing();
  at.projection.nodes[0] = { ...at.projection.nodes[0], nodeType: 'funzionalità' };
  assert.equal(scene(at).nodes[0].icon, undefined);
});

test('an entity that several nodes stand for is chosen in each of them', () => {
  assert.deepEqual(scene(drawing(), 'file:shared/money.ts').selected.sort(), [SERVER, WEB]);
  assert.deepEqual(scene(drawing(), 'component:web').selected, [WEB]);
  assert.deepEqual(scene(drawing(), 'feature:payment').selected, []);  // known, and not in this view
  assert.deepEqual(scene(drawing()).selected, []);
});

test('a line says its kind in words, a data link and an insufficient proof with their dash, the proof with its tone too', () => {
  const look = (from: Scene, id: string) => { const { style, tone, label, labelShown } = line(from, id)!; return [style, tone, label, labelShown]; };
  const drawn = scene(drawing());
  assert.deepEqual(look(drawn, `${WEB}->${SERVER}`), ['solid', 'default', 'importa', 'chosen']);
  assert.deepEqual(look(drawn, `data:${SERVER}->store:db/orders@root`), ['dashed', 'default', 'scrive', 'chosen']);
  const unsure = { ...env, relations: env.relations.map(relation => (relation.ref === MONEY ? { ...relation, conflict: true } : relation)) };
  assert.deepEqual(look(scene(drawing(unsure)), `${WEB}->${SERVER} uncertain`), ['dashed', 'warning', 'importa · prova insufficiente', 'chosen']);
});

test('every line has a name of its own, an arrowhead, and is of the kind the arrows follow', () => {
  const unsure = { ...env, relations: [...env.relations, { ...env.relations.find(relation => relation.ref === MONEY)!, ref: 'sampled', status: 'sampled' }] };
  const drawn = scene(drawing(unsure, PAY), null, PAY);
  // Three lines between the same two nodes: proved, insufficiently proved, and the flow's.
  assert.equal(drawn.edges.filter(item => item.from === WEB && item.to === SERVER).length, 3);
  assert.equal(new Set(drawn.edges.map(item => item.id)).size, drawn.edges.length);
  for (const item of drawn.edges) assert.deepEqual([item.directed, item.kind], [true, undefined]);
});

test('a flow\'s lines come first, in the accent and with their words; one insufficiently proved keeps its warning', () => {
  const drawn = scene(drawing(env, PAY), null, PAY);
  assert.deepEqual(drawn.edges.slice(0, 5).map(item => item.id!.startsWith('flow:')), [true, true, true, true, false]);
  const { tone, style, label, labelShown } = line(drawn, `flow:${WEB}->${SERVER}`)!;
  assert.deepEqual([tone, style, label, labelShown], ['accent', 'solid', 'chiama', 'always']);
  const sampled: Flow = { ...PAY, steps: PAY.steps.map(step => ({ ...step, confidence: 'sampled' })) };
  const unsure = line(scene(drawing({ ...env, flows: [sampled] }, sampled), null, sampled), `flow:${WEB}->${SERVER} uncertain`)!;
  assert.deepEqual([unsure.tone, unsure.style, unsure.label, unsure.labelShown], ['warning', 'dashed', 'chiama · prova insufficiente', 'always']);
});

test('a flow numbers its nodes as the details number its steps: where it starts, then the step that first reaches each', () => {
  assert.equal(scene(drawing()).steps, undefined);
  assert.deepEqual(numbers(PAY), { [WEB]: [1], [SERVER]: [2], [PROVIDER]: [5], 'store:db/orders@root': [6], 'store:queue/receipts@root': [8] });
  // Inside a group only what is in view is numbered, and what reaches it from outside keeps its number.
  assert.deepEqual(numbers(PAY, 'component:server'), {
    'file:server/routes.ts@component:server': [2], 'file:server/auth.ts@component:server': [3], 'file:server/payments.ts@component:server': [4] });
});

test('a node has one number however many steps reach it, and a flow with no step numbers where it starts', () => {
  const jobs = 'file:server/jobs.ts@component:server', payments = 'file:server/payments.ts@component:server';
  assert.deepEqual(numbers({ ...NIGHTLY, steps: Array(43).fill(NIGHTLY.steps[0]) }, 'component:server'), { [jobs]: [1], [payments]: [1] });
  assert.deepEqual(numbers({ ...NIGHTLY, nodes: [NIGHTLY.entry], steps: [] }), { [SERVER]: [1] });
  // Reached from nothing else in view: the first step it has a part in.
  assert.deepEqual(numbers({ ...NIGHTLY, nodes: [...NIGHTLY.nodes, PAY.steps[0].target], steps: [NIGHTLY.steps[0], PAY.steps[0]] }),
    { [SERVER]: [1], [WEB]: [2] });
});

test('the key has the kinds of line that are drawn, with their count and their look', () => {
  assert.deepEqual(scene(drawing()).legend, [
    { label: 'Relazioni', style: 'solid', tone: 'default', count: 6 }, { label: 'Collegamenti di dati', style: 'dashed', tone: 'default', count: 3 }]);
  const drawn = scene(drawing(env, PAY), null, PAY);
  assert.deepEqual(drawn.legend.map(entry => [entry.label, entry.count]), [['Relazioni', 6], ['Linee del flusso', 4]]);
  for (const entry of drawn.legend) assert.ok(drawn.edges.some(item => item.style === entry.style && item.tone === entry.tone), entry.label);
});

test('a layout is named by what it lays out and which way, and not by the choice', () => {
  const at = drawing(), chosen = { ...at, projection: project(env, 'logical', null, {}, [], 'component:web') };
  assert.equal(layoutKeyOf(chosen), layoutKeyOf(at));
  assert.equal(scene(at, 'component:web').layoutKey, scene(at).layoutKey);
  const others = [{ ...at, direction: 'down' as const }, drawing(env, PAY), drawing(env, undefined, 'component:web')].map(layoutKeyOf);
  assert.equal(new Set([layoutKeyOf(at), ...others]).size, 4);
});

test('ELK is asked for every node, at one size, and every line by its name', () => {
  const at = drawing(), asked = graphOf(at);
  assert.deepEqual(asked.nodes.map(item => item.id), at.projection.nodes.map(item => item.id));
  for (const item of asked.nodes) assert.deepEqual([item.width, item.height], [224, 64]);
  assert.deepEqual(asked.edges.map(item => item.id), at.edges.map(item => item.id));
  assert.equal(asked.edges.length, 9);
});
