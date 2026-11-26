// ELK in a worker: positions and orthogonal routes for one projection, answered with the request id.
import ELK from 'elkjs/lib/elk.bundled.js';
import { elkGraphOf, layoutOf } from './elkGraph.ts';
import type { LayoutGraph } from './layoutClient.ts';

const elk = new ELK();

self.onmessage = async (event: MessageEvent<{ id: number; graph: LayoutGraph; direction: 'RIGHT' | 'DOWN' }>) => {
  const { id, graph, direction } = event.data;
  try {
    self.postMessage({ id, layout: layoutOf(await elk.layout(elkGraphOf(graph, direction))) });
  } catch (error) {
    self.postMessage({ id, error: String((error as Error)?.message ?? error) });
  }
};
