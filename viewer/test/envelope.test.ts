import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseEnvelope, SCHEMA } from '../src/envelope.ts';

test('an entity and a technology keep the mark of their registry entry, and neither needs one', () => {
  const env = parseEnvelope({
    schema: SCHEMA, relations: [], memberships: [],
    entities: [{ ref: 'external:stripe', type: 'external', mark: 'stripe' }, { ref: 'external:own', type: 'external' }],
    technologies: [{ id: 'express', name: 'Express', type: 'altro', paths: [], mark: 'express' }, { id: 'requests', name: 'Requests', type: 'altro', paths: [] }],
  });
  assert.deepEqual(env.entities.map(item => item.mark), ['stripe', undefined]);
  assert.deepEqual(env.technologies.map(item => item.mark), ['express', undefined]);
});
