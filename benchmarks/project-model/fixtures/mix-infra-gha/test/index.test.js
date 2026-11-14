import test from 'node:test';
import assert from 'node:assert/strict';
import { slug } from '../src/index.js';

test('slug', () => {
  assert.equal(slug(' Hello World '), 'hello-world');
});
