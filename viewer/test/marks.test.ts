import { test } from 'node:test';
import assert from 'node:assert/strict';
import { frameworkMark, markAddress } from '../src/marks.ts';

test('a logo is asked of the server by the id of its entry, with the token of the page where there is one', () => {
  assert.equal(markAddress('./api/mark', 'stripe', ''), './api/mark?id=stripe');
  assert.equal(markAddress('/api/app/mark', 'stripe', 'a b&c'), '/api/app/mark?id=stripe&token=a+b%26c');
  assert.equal(markAddress('./api/mark', 'gcp/cloud run&x', ''), './api/mark?id=gcp%2Fcloud+run%26x');
});

test('a thing with no logo asks for none', () => {
  assert.deepEqual([undefined, null, ''].map(mark => markAddress('./api/mark', mark, 't')), [undefined, undefined, undefined]);
});

test('a group has the logo of the one framework it declares, and none of several', () => {
  const react = { category: 'framework', mark: 'react' }, next = { category: 'framework', mark: 'nextjs' }, zod = { category: 'library', mark: 'zod' };
  assert.deepEqual([[react], [zod, react], [react, next], [zod], [], [{ category: 'framework' }], [{ mark: 'react' }]].map(frameworkMark),
    ['react', 'react', undefined, undefined, undefined, undefined, undefined]);
});
