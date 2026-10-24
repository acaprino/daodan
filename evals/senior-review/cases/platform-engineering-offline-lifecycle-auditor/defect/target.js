// Service-worker packet: v1 clients remain open after v2 activation and lazily request /v1/editor.js offline from cache v1. Requirement: open clients keep working.
export async function activate(caches, clients) {
  await caches.delete("v1");
  await clients.claim();
}
