import { mock, test } from 'node:test';
import assert from 'node:assert/strict';
import { createLayoutClient, LayoutError } from '../src/layoutClient.ts';
import type { Layout, WorkerLike } from '../src/layoutClient.ts';

class FakeWorker implements WorkerLike {
  onmessage: ((event: { data: unknown }) => void) | null = null;
  posted: { id: number }[] = [];
  terminated = false;
  postMessage(message: unknown) { this.posted.push(message as { id: number }); }
  terminate() { this.terminated = true; }
  answer(id: number, layout: Layout) { this.onmessage?.({ data: { id, layout } }); }
}

const graph = { nodes: [{ id: 'a', width: 10, height: 10 }], edges: [] };
const layout = (x: number): Layout => ({ nodes: { a: { x, y: 0, width: 10, height: 10 } }, edges: {} });

test('a request answered after a newer one is rejected as superseded', async () => {
  const workers: FakeWorker[] = [];
  const client = createLayoutClient(() => { const worker = new FakeWorker(); workers.push(worker); return worker; });
  const first = client.request(graph, 'RIGHT');
  const second = client.request(graph, 'RIGHT');
  const [worker] = workers;
  worker.answer(worker.posted[1].id, layout(2));
  worker.answer(worker.posted[0].id, layout(1));  // late answer of the first request: dropped
  await assert.rejects(first, (error: unknown) => error instanceof LayoutError && error.reason === 'superseded');
  assert.equal((await second).nodes.a.x, 2);
  assert.equal(workers.length, 1);
});

test('a layout past its deadline ends the worker and the next request gets a new one', async () => {
  mock.timers.enable({ apis: ['setTimeout'] });
  try {
    const workers: FakeWorker[] = [];
    const client = createLayoutClient(() => { const worker = new FakeWorker(); workers.push(worker); return worker; }, 5000);
    const slow = client.request(graph, 'DOWN');
    mock.timers.tick(5000);
    await assert.rejects(slow, (error: unknown) => error instanceof LayoutError && error.reason === 'timeout');
    assert.equal(workers[0].terminated, true);
    const again = client.request(graph, 'DOWN');
    assert.equal(workers.length, 2);
    workers[1].answer(workers[1].posted[0].id, layout(3));
    assert.equal((await again).nodes.a.x, 3);
  } finally {
    mock.timers.reset();
  }
});
