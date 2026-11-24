import { test } from 'node:test';
import assert from 'node:assert/strict';
import { NODE_TYPES } from '../src/envelope.ts';
import { FLOW_ICON, iconFor, NO_ICON, TYPE_LABEL } from '../src/icons.ts';

const UNKNOWN = { type: 'nothing the model names' };

test('what Sigrid has a name for has its icon', () => {
  const byNodeType = Object.fromEntries(NODE_TYPES.map(nodeType => [nodeType, iconFor({ ...UNKNOWN, nodeType })]));
  assert.deepEqual(byNodeType, {
    attore: 'account', schermata: 'layout', 'funzionalità': NO_ICON, 'servizio o API': 'service', gateway: 'gateway', database: 'data',
    coda: 'listOrdered', autenticazione: 'key', dispositivo: 'device', altro: NO_ICON,
  });
  assert.deepEqual([iconFor({ type: 'symbol' }), iconFor({ type: 'build' }), FLOW_ICON], ['code', 'package', 'branch']);
});

test('no kind borrows the icon of another thing: without a name of its own it has the empty slot', () => {
  const borrowed = ['settings', 'profile', 'moveRight', 'tag', 'link', 'archive', 'importExport', 'now', 'more'];
  const icons = [...NODE_TYPES.map(nodeType => iconFor({ ...UNKNOWN, nodeType })), ...Object.keys(TYPE_LABEL).map(type => iconFor({ type })), FLOW_ICON];
  for (const icon of icons) assert.ok(!borrowed.includes(icon), icon);
  assert.equal(iconFor(UNKNOWN), NO_ICON);
});

test('the node type of the flow model comes before the entity type, and one that says nothing leaves the entity type', () => {
  assert.equal(iconFor({ nodeType: 'database', type: 'external' }), iconFor({ nodeType: 'database', type: 'file' }));
  assert.notEqual(iconFor({ nodeType: 'database', type: 'external' }), iconFor({ type: 'external' }));
  assert.equal(iconFor({ nodeType: 'altro', type: 'file' }), iconFor({ type: 'file' }));
  assert.equal(iconFor({ nodeType: 'not in the list', type: 'file' }), iconFor({ type: 'file' }));
});
