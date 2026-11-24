import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { NODE_TYPES, parseEnvelope } from '../src/envelope.ts';
import { iconFor, TYPE_LABEL } from '../src/icons.ts';

const env = parseEnvelope(JSON.parse(readFileSync(new URL('./fixture.json', import.meta.url), 'utf8')));
const UNKNOWN = iconFor({ type: 'nothing the model names' });

test('every generic node type has an icon, and only the one that says nothing has the icon of the unknown', () => {
  for (const nodeType of NODE_TYPES) assert.equal(iconFor({ nodeType, type: 'nothing the model names' }) === UNKNOWN, nodeType === 'altro', nodeType);
});

test('every entity type the interface has a word for has an icon, and so has every entity of the fixture', () => {
  for (const type of Object.keys(TYPE_LABEL)) assert.notEqual(iconFor({ type }), UNKNOWN, type);
  for (const entity of env.entities) assert.notEqual(iconFor({ type: entity.type }), UNKNOWN, entity.ref);
});

test('the node type of the flow model comes before the entity type, and one the list does not hold leaves the entity type', () => {
  assert.equal(iconFor({ nodeType: 'database', type: 'external' }), iconFor({ nodeType: 'database', type: 'file' }));
  assert.notEqual(iconFor({ nodeType: 'database', type: 'external' }), iconFor({ type: 'external' }));
  assert.equal(iconFor({ nodeType: 'not in the list', type: 'file' }), iconFor({ type: 'file' }));
});
