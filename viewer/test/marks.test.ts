import { test } from 'node:test';
import assert from 'node:assert/strict';
import { markAddress } from '../src/marks.ts';

test('a logo is asked of the server by the id of its entry, with the token of the page where there is one', () => {
  assert.equal(markAddress('stripe', ''), './api/mark?id=stripe');
  assert.equal(markAddress('stripe', 'a b&c'), './api/mark?id=stripe&token=a%20b%26c');
  assert.equal(markAddress('gcp/cloud run&x', ''), './api/mark?id=gcp%2Fcloud%20run%26x');
});

test('a thing with no logo asks for none', () => {
  assert.deepEqual([markAddress(undefined, 't'), markAddress('', 't')], [undefined, undefined]);
});
