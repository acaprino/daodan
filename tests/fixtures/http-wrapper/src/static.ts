// Calls of the client with no rule: the route is read where the table says (`tests/test_codebase_map_flows_http_static.py`).

declare function computedUrl(): string;

export async function createDirect() {
  await fetch('/api/orders', { method: 'POST' });
}

export async function computedDirect() {
  await fetch(computedUrl(), { method: 'POST' });
}

export async function twinDirect() {
  await fetch('/api/twin');
}
