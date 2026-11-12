import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import { initialState, reduce } from '../src/state.ts';

const raw = JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8'));
const env = parseEnvelope(raw);

test('switching view keeps the selection only when its ref resolves', () => {
  let state = reduce(initialState(env), { type: 'select', ref: 'file:shared/money.ts' });
  state = reduce(state, { type: 'view', view: 'physical' });
  assert.equal(state.selected, 'file:shared/money.ts');
  state = reduce(reduce(state, { type: 'view', view: 'logical' }), { type: 'select', ref: 'component:web' });
  state = reduce(state, { type: 'view', view: 'physical' });
  assert.equal(state.selected, null);
});

test('replaceEnvelope with an unknown schema leaves the previous envelope and reports the error', () => {
  const state = reduce(initialState(env), { type: 'replaceEnvelope', json: { ...raw, schema: 'something/else@9' } });
  assert.equal(state.envelope, env);
  assert.match(state.error ?? '', /unknown schema/);
});

test('replaceEnvelope drops vanished refs from the selection and returns a warning', () => {
  const gone = 'external:pos terminal';
  const next = {
    ...raw,
    entities: raw.entities.filter((entity: { ref: string }) => entity.ref !== gone),
    relations: raw.relations.filter((relation: { source: string; target: string }) => relation.source !== gone && relation.target !== gone),
    memberships: raw.memberships.filter((item: { member: string; group: string }) => item.member !== gone && item.group !== gone),
  };
  let state = reduce(initialState(env), { type: 'select', ref: gone });
  state = reduce(state, { type: 'replaceEnvelope', json: next });
  assert.equal(state.selected, null);
  assert.match(state.warning ?? '', /pos terminal/);
  assert.equal(state.error, null);
});

test('open enters a group, up returns with the group selected', () => {
  let state = reduce(initialState(env), { type: 'open', ref: 'component:server' });
  assert.equal(state.scope, 'component:server');
  state = reduce(state, { type: 'up' });
  assert.deepEqual([state.scope, state.selected], [null, 'component:server']);
  assert.equal(reduce(state, { type: 'open', ref: 'feature:payment' }).scope, null);
  const deep = reduce(reduce(initialState(env), { type: 'open', ref: 'component:server' }), { type: 'select', ref: 'file:server/auth.ts' });
  assert.deepEqual([reduce(deep, { type: 'root' }).scope, reduce(deep, { type: 'root' }).selected], [null, null]);
});

test('filters, groups and flows change only their own field', () => {
  let state = reduce(initialState(env), { type: 'filter', filters: { text: 'pay' } });
  state = reduce(state, { type: 'toggleGroup', ref: 'component:web' });
  state = reduce(state, { type: 'flow', ref: 'flow:symbol:web/checkout.tsx::pay' });
  assert.deepEqual([state.filters, state.open, state.flow], [{ text: 'pay' }, ['component:web'], 'flow:symbol:web/checkout.tsx::pay']);
  state = reduce(reduce(state, { type: 'resetFilters' }), { type: 'toggleGroup', ref: 'component:web' });
  assert.deepEqual([state.filters, state.open], [{}, []]);
  assert.equal(reduce(state, { type: 'flow', ref: 'flow:nowhere' }).flow, 'flow:symbol:web/checkout.tsx::pay');
});
