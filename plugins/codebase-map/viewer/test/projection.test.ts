import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import { flowFocus, flowsThrough, project } from '../src/projection.ts';

const env = parseEnvelope(JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8')));
const SHARED = 'file:shared/money.ts';
const FILES_OF_COMPONENTS = 7;  // web: 3, server: 5, shared/money.ts in both

test('shared file yields two occurrences and one unique count', () => {
  const projection = project(env, 'logical', null, {}, ['component:web', 'component:server']);
  const shared = projection.nodes.filter(node => node.ref === SHARED);
  assert.deepEqual(shared.map(node => node.parent).sort(), ['component:server@root', 'component:web@root']);
  assert.equal(projection.nodes.filter(node => node.type === 'file').length, FILES_OF_COMPONENTS + 1);
  assert.equal(projection.counts.files, FILES_OF_COMPONENTS);
});

test('collapsed group keeps the underlying relation refs', () => {
  const projection = project(env, 'logical', null);
  const edge = projection.edges.find(item => item.source === 'component:web@root' && item.target === 'component:server@root');
  assert.ok(edge, 'web depends on server through the shared file');
  assert.ok(edge.relations.includes('imports:file:web/checkout.tsx->file:shared/money.ts'));
});

test('edges inside a collapsed group become a count, not external edges', () => {
  const projection = project(env, 'logical', null);
  assert.ok(projection.edges.every(edge => edge.source !== edge.target));
  assert.ok(projection.counts.aggregated > 0);
  const internal = 'imports:file:server/routes.ts->file:server/payments.ts';
  assert.ok(projection.edges.every(edge => !edge.relations.includes(internal)));
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

test('node types and location reach the projected node', () => {
  const projection = project(env, 'logical', null);
  const provider = projection.nodes.find(node => node.ref === 'external:card payment provider');
  assert.deepEqual([provider?.nodeType, provider?.location], ['servizio o API', 'external']);
  assert.equal(projection.nodes.find(node => node.ref === 'store:db/orders')?.nodeType, 'database');
});
