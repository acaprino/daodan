import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inSight, onceDrawn } from '../src/sight.ts';

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

test('what waits for the drawing runs once the canvas has kept its width, and not while something slides beside it', () => {
  const widths = [100, 100, 90, 80, 80, 80];
  let frames = 0, ran = 0, next: (() => void) | null = null;
  Object.assign(globalThis, {
    document: { querySelector: () => ({ getBoundingClientRect: () => ({ width: widths[Math.min(frames, widths.length - 1)] }) }) },
    requestAnimationFrame: (run: () => void) => { next = run; return 1; }, cancelAnimationFrame: () => { next = null; },
  });
  const step = () => { const run = next; next = null; frames += 1; run?.(); };
  onceDrawn('Mappa', () => { ran = frames; });
  for (let n = 0; n < 12; n += 1) step();
  assert.equal(ran, 6);  // 80 three times after the frame it came in
  const stop = onceDrawn('Mappa', () => { ran = -1; });
  stop();
  step();
  assert.equal(ran, 6);
});
