import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inSight } from '../src/sight.ts';

// A canvas 100 wide and tall, and what is drawn of it: the id of each thing and where its left side is.
const draw = (...things: [string, number][]) => {
  const box = (left: number, size: number) => ({ left, right: left + size, top: 0, bottom: size });
  const canvas = {
    getBoundingClientRect: () => box(0, 100),
    querySelectorAll: () => things.map(([nodeId, left]) => ({ dataset: { nodeId }, getBoundingClientRect: () => box(left, 20) })),
  };
  Object.assign(globalThis, { document: { querySelector: (name: string) => (name.includes('Mappa') ? canvas : null) } });
};

test('a thing is in sight by its own id, whatever else has its name, and whole', () => {
  draw(['file:a/index.ts@a', 0], ['file:b/index.ts@b', 90]);
  assert.equal(inSight('Mappa', ['file:a/index.ts@a']), true);
  assert.equal(inSight('Mappa', ['file:b/index.ts@b']), false);  // cut by the edge of the canvas
  assert.equal(inSight('Mappa', ['file:a/index.ts@a', 'file:b/index.ts@b']), false);
  assert.equal(inSight('Mappa', ['file:c/index.ts@c']), false);  // out of the view it is not drawn
  assert.equal(inSight('Altro', ['file:a/index.ts@a']), false);
});
