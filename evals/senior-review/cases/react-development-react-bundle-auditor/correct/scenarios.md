# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## supported-exports

Package widget declares exports:{".":"./index.js"}; no subpath exports. The supplied build tree-shakes its public named import to 2KB.

```js
import {Button} from "widget";
export {Button};
```
The public import is supported and emits 2KB.

## preload-and-critical-work

Error reporting must initialize before the first checkout operation. The optional chart is not needed until requested. loadReporter and loadChart are supplied modules.

```js
export async function start(){const reporter=await import("./reporter.js");reporter.install();startCheckout();}
export function openChart(){return import("./large-chart.js");}
```
