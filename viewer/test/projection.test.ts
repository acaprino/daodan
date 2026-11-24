import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import { dataLinks, flowFocus, flowsThrough, keptBy, project, typesIn, UNASSIGNED } from '../src/projection.ts';

const env = parseEnvelope(JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8')));
const SHARED = 'file:shared/money.ts';
const FILES_OF_COMPONENTS = 7;  // web: 3, server: 5, shared/money.ts in both

test('shared file yields two occurrences', () => {
  const projection = project(env, 'logical', null, {}, ['component:web', 'component:server']);
  const shared = projection.nodes.filter(node => node.ref === SHARED);
  assert.deepEqual(shared.map(node => node.parent).sort(), ['component:server@root', 'component:web@root']);
  assert.equal(projection.nodes.filter(node => node.type === 'file').length, FILES_OF_COMPONENTS + 1);
});

test('a relation between things of two closed groups is a line between the groups', () => {
  const projection = project(env, 'logical', null);
  const edge = projection.edges.find(item => item.source === 'component:web@root' && item.target === 'component:server@root');
  assert.deepEqual(edge?.kinds, ['imports']);  // web depends on server through the shared file
});

test('edges inside a collapsed group become a count, not external edges', () => {
  const projection = project(env, 'logical', null);
  assert.ok(projection.edges.every(edge => edge.source !== edge.target));
  assert.ok(projection.counts.aggregated > 0);
});

test('a group opened in place has what it holds in it, and the rest is as it was', () => {
  const closed = project(env, 'logical', null), open = project(env, 'logical', null, {}, ['component:web']);
  const at = (from: typeof open, id: string) => from.nodes.find(node => node.id === id);
  assert.deepEqual([at(closed, 'component:web@root')?.open, at(open, 'component:web@root')?.open, at(open, 'component:server@root')?.open], [false, true, false]);
  assert.equal(at(open, 'store:db/orders@root')?.open, undefined);  // it holds nothing: no group
  const inside = open.nodes.filter(node => node.parent === 'component:web@root');
  assert.deepEqual(inside.map(node => node.label).sort(), ['api.ts', 'checkout.tsx', 'money.ts']);
  assert.deepEqual(open.nodes.filter(node => node.parent === null).map(node => node.id), closed.nodes.map(node => node.id));
  // A line reaches the thing in the group, and what stands for a file is its own node alone.
  assert.ok(open.edges.some(edge => edge.source === 'file:web/checkout.tsx@component:web@root' && edge.target === 'file:web/api.ts@component:web@root'));
  assert.deepEqual(open.owners['file:web/api.ts'], ['file:web/api.ts@component:web@root']);
  assert.deepEqual(open.owners['component:web'], ['component:web@root']);
  // A group in a group.
  const deep = project(env, 'logical', null, {}, ['component:web', 'file:web/checkout.tsx']);
  assert.ok(deep.nodes.some(node => node.label === 'pay' && node.parent === 'file:web/checkout.tsx@component:web@root'));
  // A group in itself is opened once.
  const ring = parseEnvelope({ ...env, memberships: [...env.memberships, { member: 'component:web', group: 'component:web', view: 'logical' }] });
  assert.equal(project(ring, 'logical', null, {}, ['component:web']).nodes.filter(node => node.ref === 'component:web').length, 2);
  assert.ok(typesIn(ring, 'logical', null, ['component:web']).includes('file'));
});

test('an open group stays, as the frame of what the filters leave in it, and goes when they leave nothing', () => {
  const left = (text: string) => project(env, 'logical', null, { text }, ['component:web', 'component:server']);
  assert.deepEqual(left('checkout').nodes.map(node => [node.label, node.open]), [['web', true], ['checkout.tsx', false]]);
  assert.deepEqual([left('zzzz').nodes.length, left('zzzz').counts.filtered], [0, 8 + FILES_OF_COMPONENTS + 1]);
  // What is itself what is looked for stays, open on nothing.
  const only = project(env, 'logical', null, { types: ['component'] }, ['component:web']);
  assert.deepEqual(only.nodes.map(node => [node.label, node.open]), [['web', true], ['server', false]]);
});

test('a choice changes the projection only where the filters would hide it', () => {
  assert.equal(keptBy(env, {}, 'component:web'), null);
  assert.equal(keptBy(env, { types: ['component'] }, 'component:web'), null);
  assert.equal(keptBy(env, { types: ['external'] }, 'component:web'), 'component:web');
  assert.deepEqual([keptBy(env, { types: ['external'] }, null), keptBy(env, { types: ['external'] }, 'file:nowhere')], [null, null]);
});

test('filters hide but never delete the selection', () => {
  const projection = project(env, 'logical', null, { types: ['external'] }, [], 'component:web');
  assert.ok(projection.nodes.some(node => node.ref === 'component:web'));
  assert.ok(projection.nodes.filter(node => node.ref !== 'component:web').every(node => node.type === 'external'));
  assert.ok(projection.counts.filtered > 0);
});

test('empty projection exposes resetFilters', () => {
  const projection = project(env, 'logical', null, { text: 'nothing-matches-this' });
  assert.equal(projection.nodes.length, 0);
  assert.ok(projection.counts.filtered > 0);
});

test('inferred and stale_body stay distinct', () => {
  const projection = project(env, 'physical', null, {}, ['build:package.json', 'directory:server', 'file:server/payments.ts']);
  const charge = projection.nodes.find(node => node.ref === 'symbol:server/payments.ts::chargeOrder');
  assert.equal(charge?.freshness, 'stale_body');
  assert.notEqual(charge?.status, 'stale_body');
  const states = new Set(['confirmed', 'inferred', 'incomplete', undefined]);
  for (const node of projection.nodes) assert.ok(states.has(node.status), `${node.ref} status ${node.status}`);
  assert.equal(env.entities.find(entity => entity.ref === 'feature:payment')?.status, 'inferred');
});

test('a flow highlights its nodes at the view level', () => {
  const projection = project(env, 'logical', null);
  const focus = flowFocus(env, 'flow:symbol:web/checkout.tsx::pay', projection);
  for (const id of ['component:web@root', 'component:server@root', 'external:card payment provider@root'])
    assert.ok(focus.nodes.includes(id), id);
  assert.ok(focus.edges.some(edge => edge.source === 'component:web@root' && edge.target === 'component:server@root' && edge.flow));
  const inside = project(env, 'logical', 'component:server');
  const deeper = flowFocus(env, 'flow:symbol:web/checkout.tsx::pay', inside);
  assert.ok(deeper.nodes.includes('file:server/payments.ts@component:server'));
});

test('a node lists the flows through it', () => {
  const server = flowsThrough(env, 'component:server', 'logical').map(flow => flow.ref).sort();
  assert.deepEqual(server, ['flow:symbol:server/jobs.ts::nightlyReconcile', 'flow:symbol:web/checkout.tsx::pay']);
  assert.deepEqual(flowsThrough(env, 'component:web', 'logical').map(flow => flow.ref), ['flow:symbol:web/checkout.tsx::pay']);
});

test('files no component holds sit in one group of the logical view, and data links come from the flows', () => {
  const raw = JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8'));
  const bare = parseEnvelope({ ...raw, memberships: raw.memberships.filter((item: { group: string }) => item.group !== 'component:web') });
  const root = project(bare, 'logical', null);
  const loose = root.nodes.find(node => node.ref === UNASSIGNED);
  assert.equal(loose?.count, 2);  // checkout.tsx and api.ts; money.ts stays in server
  assert.ok(!root.nodes.some(node => node.ref === 'component:web' && node.count > 0));
  const data = dataLinks(env, project(env, 'logical', null));
  assert.ok(data.some(edge => edge.source === 'component:server@root' && edge.target === 'store:db/orders@root' && edge.kinds.includes('scrive')));
  assert.ok(data.some(edge => edge.target === 'external:card payment provider@root' && edge.kinds.includes('usa')));
  assert.equal(project(env, 'logical', null).nodes.some(node => node.ref === UNASSIGNED), false);
});

test('node types and location reach the projected node', () => {
  const projection = project(env, 'logical', null);
  const provider = projection.nodes.find(node => node.ref === 'external:card payment provider');
  assert.deepEqual([provider?.nodeType, provider?.location], ['servizio o API', 'external']);
  assert.equal(projection.nodes.find(node => node.ref === 'store:db/orders')?.nodeType, 'database');
});

test('the logo of a service reaches its node', () => {
  const marked = parseEnvelope({ ...env, entities: env.entities.map(entity => (entity.ref === 'external:card payment provider' ? { ...entity, mark: 'stripe' } : entity)) });
  const projection = project(marked, 'logical', null);
  assert.deepEqual(projection.nodes.filter(node => node.mark).map(node => [node.label, node.mark]), [['card payment provider', 'stripe']]);
});

test('old exports with a shared handler still allow selecting either event', () => {
  const first = env.flows[0];
  const repeated = parseEnvelope({ ...env, flows: [first, { ...first, steps: [], complete: false }] });
  assert.notEqual(repeated.flows[0].ref, repeated.flows[1].ref);
  assert.equal(repeated.flows.find(f => f.ref === repeated.flows[1].ref)?.complete, false);
});

test('uncertain and proved steps between the same groups stay distinguishable on export', () => {
  const first = env.flows[0];
  const base = { source: 'component:web', target: 'component:server', type: 'scrive', origin: 'dedotto', site: 'a:1' };
  const envelope = { ...env, flows: [{ ...first, steps: [base, { ...base, confidence: 'sampled', site: 'a:2' }] }] };
  const projection = project(envelope, 'logical', null);
  for (const edges of [flowFocus(envelope, first.ref, projection).edges, dataLinks(envelope, projection)]) {
    assert.equal(edges.length, 2);
    assert.equal(edges.filter(edge => edge.uncertain).length, 1);
  }
});

test('the types to choose from are those of the scope, whatever the filters hide, with the chosen one', () => {
  assert.deepEqual(typesIn(env, 'logical', null), ['component', 'external', 'store']);
  assert.deepEqual(typesIn(env, 'logical', null, ['component:web']), ['component', 'external', 'file', 'store']);
  assert.deepEqual(typesIn(env, 'logical', 'component:server'), ['file']);
  assert.deepEqual(typesIn(env, 'logical', 'component:server', [], 'component'), ['component', 'file']);
});
