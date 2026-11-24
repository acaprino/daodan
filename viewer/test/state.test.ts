import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseEnvelope } from '../src/envelope.ts';
import { canEnter, initialState, placeOf, reduce, shownDetails } from '../src/state.ts';
import type { Action } from '../src/state.ts';

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

test('an export of another schema is refused where it is read, before it reaches the state', () => {
  assert.throws(() => parseEnvelope({ ...raw, schema: 'something/else@9' }), /unknown schema: something\/else@9/);
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
  state = reduce(state, { type: 'replaceEnvelope', envelope: parseEnvelope(next) });
  assert.equal(state.selected, null);
  assert.match(state.warning ?? '', /pos terminal/);
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

test('a group opened in place changes where nothing is: the scope, the choice and the way up stay', () => {
  let state = reduce(reduce(initialState(env), { type: 'select', ref: 'component:web' }), { type: 'toggleGroup', ref: 'component:web' });
  state = reduce(state, { type: 'toggleGroup', ref: 'component:server' });
  assert.deepEqual([state.scope, state.selected, state.open, placeOf(state)], [null, 'component:web', ['component:web', 'component:server'], ['Sistema']]);
  assert.deepEqual(reduce(state, { type: 'up' }), state);
  const inside = reduce(state, { type: 'open', ref: 'component:web' });  // «Entra» still goes in
  assert.deepEqual([inside.scope, inside.open], ['component:web', []]);
  assert.deepEqual(reduce(state, { type: 'closeGroups' }).open, []);
});

test('what holds something in the view is gone into, and a feature is not', () => {
  const state = initialState(env);
  assert.deepEqual(['component:web', 'file:web/checkout.tsx', 'store:db/orders', 'feature:payment', 'file:nowhere', null].map(ref => canEnter(state, ref)),
    [true, true, false, false, false, false]);
});

test('load starts a run clean: nothing of the last one is kept', () => {
  const state = reduce(reduce(initialState(env), { type: 'select', ref: 'file:shared/money.ts' }), { type: 'view', view: 'physical' });
  const loaded = reduce(state, { type: 'load', envelope: env });
  assert.deepEqual(loaded, initialState(env));
});

const FLOW = 'flow:symbol:web/checkout.tsx::pay';
const after = (...actions: Action[]) => actions.reduce(reduce, initialState(env));

test('the inspector shows the element first, then the flow or the project, the one asked for last', () => {
  assert.equal(shownDetails(initialState(env)), null);
  assert.equal(shownDetails(after({ type: 'flow', ref: FLOW })), 'flow');
  assert.equal(shownDetails(after({ type: 'flow', ref: FLOW }, { type: 'select', ref: 'component:web' })), 'entity');
  assert.equal(shownDetails(after({ type: 'flow', ref: FLOW }, { type: 'info' })), 'project');
  assert.equal(shownDetails(after({ type: 'info' }, { type: 'flow', ref: FLOW })), 'flow');
  assert.equal(shownDetails(after({ type: 'select', ref: 'component:web' }, { type: 'info' })), 'project');
});

test('closing the inspector leaves the flow chosen; the whole map clears it and closes its steps', () => {
  const closed = after({ type: 'flow', ref: FLOW }, { type: 'select', ref: 'component:web' }, { type: 'close' });
  assert.deepEqual([shownDetails(closed), closed.flow, closed.selected], [null, FLOW, null]);
  assert.equal(shownDetails(reduce(closed, { type: 'flow', ref: FLOW })), 'flow');
  const whole = after({ type: 'flow', ref: FLOW }, { type: 'flow', ref: null });
  assert.deepEqual([shownDetails(whole), whole.flow], [null, null]);
  assert.equal(shownDetails(after({ type: 'flow', ref: FLOW }, { type: 'info' }, { type: 'flow', ref: null })), 'project');
});

test('the project does not come back when a chosen element is left, and a flow does', () => {
  assert.equal(shownDetails(after({ type: 'info' }, { type: 'select', ref: 'component:web' }, { type: 'open', ref: 'component:web' })), null);
  assert.equal(shownDetails(after({ type: 'open', ref: 'component:web' }, { type: 'info' }, { type: 'up' }, { type: 'select', ref: null })), null);
  assert.equal(shownDetails(after({ type: 'flow', ref: FLOW }, { type: 'select', ref: 'component:web' }, { type: 'open', ref: 'component:web' })), 'flow');
});

test('a flow that is not in the new export takes its steps away', () => {
  const state = reduce(after({ type: 'flow', ref: FLOW }), { type: 'replaceEnvelope', envelope: parseEnvelope({ ...raw, flows: [] }) });
  assert.deepEqual([shownDetails(state), state.flow], [null, null]);
});

test('the place is the way up from the scope, from the system down', () => {
  assert.deepEqual(placeOf(initialState(env)), ['Sistema']);
  assert.deepEqual(placeOf(after({ type: 'open', ref: 'component:web' }, { type: 'open', ref: 'file:web/checkout.tsx' })), ['Sistema', 'web', 'checkout.tsx']);
});
