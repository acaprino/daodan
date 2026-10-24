# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## scope-and-fallback

Required offline entry is /app/order. Worker /assets/sw.js defaults to /assets/ scope; the server provides no Service-Worker-Allowed override.

```js
navigator.serviceWorker.register("/app/sw.js",{scope:"/app/"});
```
Manifest start_url is /app/order; that worker precaches /app/order and a local error view; denied push is optional.

## queued-write-resume

Offline edits must survive process termination and be replayed after reconnect; rejected writes restore the last accepted UI. Storage may be evicted and that state must be reported.

```js
export async function edit(store,value){await store.append(value);show(value);}
export async function reconnect(store,send){for(const item of await store.read()){const result=await send(item);if(result.accepted)await store.ack(item);else {show(result.lastAccepted);await store.reject(item);}}}
```
The supplied store reports eviction/read failure as an explicit recovery state and enforces the declared queue limit.
