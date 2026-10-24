# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## window-capability

Save is available only in the editor window. Native command save_document is registered, capability file grants it only to editor; preview intentionally lacks it.

```js
// editor preload
export const save=(invoke,text)=>invoke("save_document",{content:text});
```
The actual editor window label is "main"; no capability grants main this command.

## event-restart

The window must receive one completion event after each native restart; listener registration is process-scoped and lost on restart.

```js
export function attach(host,listener){host.onCompletion(listener);host.onRestart(()=>{});}
```
