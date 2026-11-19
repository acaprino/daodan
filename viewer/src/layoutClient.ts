// Layout requests to a worker: only the latest answer counts, and a worker that overruns its time is ended.

export type LayoutGraph = { nodes: { id: string; width: number; height: number }[]; edges: { id: string; source: string; target: string }[] };
export type Point = { x: number; y: number };
export type Layout = { nodes: Record<string, { x: number; y: number; width: number; height: number }>; edges: Record<string, Point[] | null> };
export type WorkerLike = {
  postMessage(message: unknown): void;
  terminate(): void;
  onmessage: ((event: { data: unknown }) => void) | null;
};

export class LayoutError extends Error {
  reason: 'superseded' | 'timeout' | 'failed';
  constructor(reason: 'superseded' | 'timeout' | 'failed', message = reason) {
    super(message);
    this.reason = reason;
  }
}

type Pending = { id: number; resolve: (layout: Layout) => void; reject: (error: LayoutError) => void; timer: ReturnType<typeof setTimeout> };

// `make` builds a worker: a new one replaces the worker ended by a timeout.
export function createLayoutClient(make: () => WorkerLike, timeoutMs = 5000) {
  let worker: WorkerLike | null = null;
  let pending: Pending | null = null;
  let sequence = 0;

  const ensure = (): WorkerLike => {
    if (worker) return worker;
    const created = make();
    created.onmessage = event => {
      const data = (event.data ?? {}) as { id?: number; layout?: Layout; error?: string };
      if (!pending || data.id !== pending.id) return;  // the answer of a superseded request
      const { resolve, reject, timer } = pending;
      pending = null;
      clearTimeout(timer);
      if (data.error !== undefined || !data.layout) reject(new LayoutError('failed', data.error ?? 'empty layout'));
      else resolve(data.layout);
    };
    worker = created;
    return created;
  };

  const supersede = () => {
    if (!pending) return;
    clearTimeout(pending.timer);
    pending.reject(new LayoutError('superseded'));
    pending = null;
  };

  return {
    request(graph: LayoutGraph, direction: 'RIGHT' | 'DOWN'): Promise<Layout> {
      supersede();
      const id = ++sequence;
      return new Promise<Layout>((resolve, reject) => {
        const timer = setTimeout(() => {
          if (pending?.id !== id) return;
          pending = null;
          worker?.terminate();
          worker = null;
          reject(new LayoutError('timeout', `layout took more than ${timeoutMs} ms`));
        }, timeoutMs);
        pending = { id, resolve, reject, timer };
        ensure().postMessage({ id, graph, direction });
      });
    },
    dispose(): void {
      supersede();
      worker?.terminate();
      worker = null;
    },
  };
}
