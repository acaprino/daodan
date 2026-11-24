import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import type { Envelope, Flow } from '../src/envelope.ts';
import type { Layout } from '../src/layoutClient.ts';
import { dataLinks, flowFocus, project } from '../src/projection.ts';
import type { Filters } from '../src/projection.ts';
import { chosenIn, graphOf, layoutKeyOf, sceneOf } from '../src/scene.ts';
import type { Drawing, Scene } from '../src/scene.ts';

const env = parseEnvelope(JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8')));
const [PAY, NIGHTLY] = env.flows;
const WEB = 'component:web@root', SERVER = 'component:server@root', PROVIDER = 'external:card payment provider@root';
const CHECKOUT = `file:web/checkout.tsx@${WEB}`;
const MONEY = 'imports:file:web/checkout.tsx->file:shared/money.ts';  // the relation from web to server

// What the page draws: at rest the relations and the data links, with a flow the relations and the flow's lines.
function drawing(envelope: Envelope = env, flow?: Flow, scope: string | null = null, open: string[] = [], filters: Filters = {}): Drawing {
  const projection = project(envelope, 'logical', scope, filters, open);
  const lines = flow ? flowFocus(envelope, flow.ref, projection).edges : dataLinks(envelope, projection);
  return { projection, edges: [...projection.edges, ...lines], direction: 'right', flow };
}
// What ELK answers: a box and a route of its own for each.
const layoutFor = (of: Drawing): Layout => ({
  nodes: Object.fromEntries(of.projection.nodes.map((node, n) => [node.id, { x: 10 * n, y: 100 * n, width: node.open ? 600 : 256, height: node.open ? 300 : 64 }])),
  edges: Object.fromEntries(of.edges.map((edge, n) => [edge.id, [{ x: n, y: 1 }, { x: n, y: 2 }]])),
});
const scene = (of: Drawing, token?: string) => sceneOf(of, layoutFor(of), token);
const node = (from: Scene, id: string) => from.nodes.find(item => item.id === id);
const line = (from: Scene, id: string) => from.edges.find(item => item.id === id);
const numbers = (of: Flow, scope: string | null = null, open: string[] = []) =>
  Object.fromEntries(scene(drawing({ ...env, flows: [of] }, of, scope, open)).steps!);

test('nodes and lines are where ELK put them: a size for all, a route each, and the facing sides for a line with none', () => {
  const at = drawing(), layout = layoutFor(at);
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

test('a node has its name, what it is and its icon; only a group opens in place, is entered and says how many it contains', () => {
  const drawn = scene(drawing());
  const said = (id: string) => {
    const { label, detail, icon, external, open, openLabel, hiddenCount } = node(drawn, id)!;
    return [label, detail, icon, external, open, openLabel, hiddenCount];
  };
  assert.deepEqual(said(WEB), ['web', 'componente', 'structure', false, false, 'Entra in web', 3]);
  assert.deepEqual(said('store:db/orders@root'), ['db/orders', 'database', 'data', false, undefined, undefined, undefined]);
  // «esterno» is the canvas's own word for `external`: the second line does not say it again.
  assert.deepEqual(said(PROVIDER), ['card payment provider', 'servizio o API', 'service', true, undefined, undefined, undefined]);
  assert.deepEqual(said('external:api gateway@root'), ['API gateway', 'gateway · incompleto', 'gateway', true, undefined, undefined, undefined]);
  assert.equal(drawn.refs.get(WEB), 'component:web');
});

test('a group opened in place is a frame as large as ELK made it, what it holds is in it, and the rest is in none', () => {
  const drawn = scene(drawing(env, undefined, null, ['component:web', 'file:web/checkout.tsx']));
  const { open, group, openLabel, hiddenCount, width, height } = node(drawn, WEB)!;
  assert.deepEqual([open, group, openLabel, hiddenCount, width, height], [true, undefined, undefined, undefined, 600, 300]);
  assert.deepEqual([node(drawn, CHECKOUT)?.open, node(drawn, CHECKOUT)?.group], [true, WEB]);
  assert.equal(node(drawn, `symbol:web/checkout.tsx::pay@${CHECKOUT}`)?.group, CHECKOUT);
  assert.deepEqual([node(drawn, SERVER)?.open, node(drawn, SERVER)?.group], [false, undefined]);
  for (const item of drawn.nodes) if (item.group) assert.ok(node(drawn, item.group)?.open, item.id);
});

test('a service with a logo has its address, with the token of the page, and keeps its icon under it', () => {
  const marked = { ...env, entities: env.entities.map(entity => (entity.ref === 'external:card payment provider' ? { ...entity, mark: 'stripe' } : entity)) };
  const provider = node(scene(drawing(marked)), PROVIDER);
  assert.deepEqual([provider?.image, provider?.icon], ['./api/mark?id=stripe', 'service']);
  assert.equal(node(scene(drawing(marked), 't'), PROVIDER)?.image, './api/mark?id=stripe&token=t');
  assert.equal(node(scene(drawing(marked)), WEB)?.image, undefined);
});

test('a kind with no icon has none, and no other thing\'s', () => {
  const at = drawing();
  at.projection.nodes[0] = { ...at.projection.nodes[0], nodeType: 'funzionalità' };
  assert.equal(scene(at).nodes[0].icon, undefined);
});

test('an entity that several nodes stand for is chosen in each of them', () => {
  const chosen = (ref: string | null, open: string[] = []) => chosenIn(drawing(env, undefined, null, open).projection, ref);
  assert.deepEqual([...chosen('file:shared/money.ts')].sort(), [SERVER, WEB]);
  assert.deepEqual([...chosen('file:shared/money.ts', ['component:web'])].sort(), [SERVER, `file:shared/money.ts@${WEB}`]);
  assert.deepEqual(chosen('component:web'), [WEB]);
  assert.deepEqual(chosen('component:web', ['component:web']), [WEB]);
  assert.deepEqual(chosen('feature:payment'), []);  // known, and not in this view
  assert.deepEqual(chosen(null), []);
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
  const drawn = scene(drawing(unsure, PAY));
  // Three lines between the same two nodes: proved, insufficiently proved, and the flow's.
  assert.equal(drawn.edges.filter(item => item.from === WEB && item.to === SERVER).length, 3);
  assert.equal(new Set(drawn.edges.map(item => item.id)).size, drawn.edges.length);
  for (const item of drawn.edges) assert.deepEqual([item.directed, item.kind], [true, undefined]);
});

test('a flow\'s lines, and no other, are its path: first, in the accent and with their words; one insufficiently proved keeps its warning', () => {
  const drawn = scene(drawing(env, PAY));
  assert.deepEqual(drawn.edges.slice(0, 5).map(item => item.id!.startsWith('flow:')), [true, true, true, true, false]);
  for (const item of drawn.edges) assert.equal(item.path, item.id!.startsWith('flow:'), item.id);
  assert.ok(scene(drawing()).edges.every(item => item.path === false));
  const { tone, style, label, labelShown } = line(drawn, `flow:${WEB}->${SERVER}`)!;
  assert.deepEqual([tone, style, label, labelShown], ['accent', 'solid', 'chiama', 'always']);
  const sampled: Flow = { ...PAY, steps: PAY.steps.map(step => ({ ...step, confidence: 'sampled' })) };
  const unsure = line(scene(drawing({ ...env, flows: [sampled] }, sampled)), `flow:${WEB}->${SERVER} uncertain`)!;
  assert.deepEqual([unsure.tone, unsure.style, unsure.label, unsure.labelShown, unsure.path], ['warning', 'dashed', 'chiama · prova insufficiente', 'always', true]);
});

test('a flow numbers its nodes as the details number its steps: every step a node has a part in', () => {
  assert.equal(scene(drawing()).steps, undefined);
  assert.deepEqual(numbers(PAY), { [WEB]: [1, 2], [SERVER]: [2, 3, 4, 5, 6, 7, 8], [PROVIDER]: [5], 'store:db/orders@root': [6], 'store:queue/receipts@root': [8] });
  // Inside a group only what is in view is numbered, and what reaches it from outside keeps its number.
  assert.deepEqual(numbers(PAY, 'component:server'), {
    'file:server/routes.ts@component:server': [2, 3, 4], 'file:server/auth.ts@component:server': [3], 'file:server/payments.ts@component:server': [4, 5, 6, 7, 8] });
  // With the group open in place the numbers are on what it holds, not on its frame.
  const open = numbers(PAY, null, ['component:server']);
  assert.deepEqual([open[SERVER], open[`file:server/auth.ts@${SERVER}`], open[WEB]], [undefined, [3], [1, 2]]);
});

test('a node that many steps reach has all their numbers, and a flow with no step numbers where it starts', () => {
  const jobs = 'file:server/jobs.ts@component:server', payments = 'file:server/payments.ts@component:server';
  const all = Array.from({ length: 43 }, (_, n) => n + 1);
  assert.deepEqual(numbers({ ...NIGHTLY, steps: Array(43).fill(NIGHTLY.steps[0]) }, 'component:server'), { [jobs]: all, [payments]: all });
  assert.deepEqual(numbers({ ...NIGHTLY, nodes: [NIGHTLY.entry], steps: [] }), { [SERVER]: [1] });
  assert.deepEqual(numbers({ ...NIGHTLY, nodes: [...NIGHTLY.nodes, PAY.steps[0].target], steps: [NIGHTLY.steps[0], PAY.steps[0]] }),
    { [SERVER]: [1], [WEB]: [2] });
});

test('the key has the kinds of line that are drawn, with their count and their look', () => {
  assert.deepEqual(scene(drawing()).legend, [
    { label: 'Relazioni', style: 'solid', tone: 'default', count: 6 }, { label: 'Collegamenti di dati', style: 'dashed', tone: 'default', count: 3 }]);
  const drawn = scene(drawing(env, PAY));
  assert.deepEqual(drawn.legend.map(entry => [entry.label, entry.count]), [['Relazioni', 6], ['Linee del flusso', 4]]);
  for (const entry of drawn.legend) assert.ok(drawn.edges.some(item => item.style === entry.style && item.tone === entry.tone), entry.label);
});

test('a layout is named by what it lays out, what is open in it and which way, and not by the choice', () => {
  const at = drawing(), chosen = { ...at, projection: project(env, 'logical', null, {}, [], 'component:web') };
  assert.equal(layoutKeyOf(chosen), layoutKeyOf(at));
  assert.equal(scene(at).layoutKey, layoutKeyOf(at));
  const components: Filters = { types: ['component'] };
  const others = [{ ...at, direction: 'down' as const }, drawing(env, PAY), drawing(env, undefined, 'component:web'), drawing(env, undefined, null, ['component:web']),
    drawing(env, undefined, null, [], components), drawing(env, undefined, null, ['component:web'], components)];
  assert.equal(new Set([at, ...others].map(layoutKeyOf)).size, 7);
});

test('a drawing keeps the flow it was made for', () => {
  const at = drawing(env, PAY), layout = layoutFor(at);
  assert.ok(sceneOf(at, layout).steps);
  assert.equal(sceneOf({ ...at, flow: undefined }, layout).steps, undefined);
});

test('ELK is asked for every node, at one size and in its group, and every line by its name', () => {
  const at = drawing(), asked = graphOf(at);
  assert.deepEqual(asked.nodes.map(item => item.id), at.projection.nodes.map(item => item.id));
  for (const item of asked.nodes) assert.deepEqual([item.width, item.height, item.parent], [256, 64, undefined]);
  assert.deepEqual(asked.edges.map(item => item.id), at.edges.map(item => item.id));
  assert.equal(asked.edges.length, 9);
  const inside = graphOf(drawing(env, undefined, null, ['component:web'])).nodes.filter(item => item.parent !== undefined);
  assert.deepEqual(inside.map(item => item.parent), [WEB, WEB, WEB]);
});
