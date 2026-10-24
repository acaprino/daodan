# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## scope-and-fallback

Required offline entry is /app/order. Worker /assets/sw.js defaults to /assets/ scope; the server provides no Service-Worker-Allowed override.

```js
navigator.serviceWorker.register("/assets/sw.js");
```
Manifest start_url is /app/order; no other worker or offline fallback exists.

## queued-write-resume

Offline edits must survive process termination and be replayed after reconnect; rejected writes restore the last accepted UI. Storage may be evicted and that state must be reported.

```js
const queue=[];
export function edit(value){queue.push(value);show(value);}
export async function reconnect(send){for(const item of queue) await send(item);queue.length=0;}
```
