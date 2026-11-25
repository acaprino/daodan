import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseEnvelope, readEnvelope, SCHEMA } from '../src/envelope.ts';

test('an entity and a technology keep the mark of their registry entry, and neither needs one', () => {
  const env = parseEnvelope({
    schema: SCHEMA, relations: [], memberships: [],
    entities: [{ ref: 'external:stripe', type: 'external', mark: 'stripe' }, { ref: 'external:own', type: 'external' }],
    technologies: [{ id: 'express', name: 'Express', type: 'altro', paths: [], mark: 'express' }, { id: 'requests', name: 'Requests', type: 'altro', paths: [] }],
  });
  assert.deepEqual(env.entities.map(item => item.mark), ['stripe', undefined]);
  assert.deepEqual(env.technologies.map(item => item.mark), ['express', undefined]);
});

test('what holds no export says why, in Italian', () => {
  const bare = { schema: SCHEMA, entities: [], relations: [], memberships: [] };
  const wrong: [unknown, string][] = [
    [[], 'non è un oggetto JSON'], [{}, 'non dice il suo schema'], [{ schema: 'altro' }, 'schema sconosciuto: altro'],
    [{ ...bare, entities: 1 }, '«entities» non è un elenco'], [{ ...bare, entities: [{}] }, "un'entità non ha ref o type"],
    [{ ...bare, relations: [{ ref: 'r', source: 'a', target: 'b' }] }, "r nomina un'entità sconosciuta: a"],
    [{ ...bare, memberships: [{ member: 'a', group: 'b', view: 'altra' }] }, 'vista sconosciuta: altra'],
    [{ ...bare, memberships: [{ member: 'a', group: 'b', view: 'logical' }] }, "un'appartenenza nomina un'entità sconosciuta: a"],
  ];
  for (const [json, why] of wrong) assert.throws(() => parseEnvelope(json), { message: why });
  assert.throws(() => readEnvelope('not json'), { message: 'non è JSON' });
  assert.deepEqual(readEnvelope(JSON.stringify(bare)).entities, []);
});
