# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## keyboard-and-origin

Supported embedded host has origin http://intranet and no secure-context clipboard API. A 300px virtual keyboard shrinks visualViewport; Confirm must remain visible.

```js
export function confirmStyle(host){return {position:"fixed",top:(host.visualViewport.height-40)+"px"};}
export function copy(host,text){return host.navigator.clipboard?.writeText ? host.navigator.clipboard.writeText(text) : host.nativeCopy(text);}
```
Host registers nativeCopy and updates style on visualViewport resize.

## resume-and-webview-callback

Background timers are suspended. Expiry must reflect wall time after resume; the host calls only registered onResume.

```js
export function session(host){const deadline=host.now()+60000;return {isValid:()=>host.now()<deadline};}
```
