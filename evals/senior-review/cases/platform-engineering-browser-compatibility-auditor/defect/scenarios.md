# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## keyboard-and-origin

Supported embedded host has origin http://intranet and no secure-context clipboard API. A 300px virtual keyboard shrinks visualViewport; Confirm must remain visible.

```js
export const confirmStyle={position:"fixed",top:"calc(100vh - 40px)"};
export function copy(host,text){return host.navigator.clipboard.writeText(text);}
```
Supplied host layout: 100vh remains 800px, visual viewport becomes 500px; clipboard is undefined.

## resume-and-webview-callback

Background timers are suspended. Expiry must reflect wall time after resume; the host calls only registered onResume.

```js
export function session(host){let seconds=60;host.setInterval(()=>seconds--,1000);return {isValid:()=>seconds>0};}
```
