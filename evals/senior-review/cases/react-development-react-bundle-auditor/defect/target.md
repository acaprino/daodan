# Product/build packet

Requirement: home initial JavaScript at most 100KB; Export is used only after a click. Build evidence is supplied for exactly this source; do not claim to have built it.

## app.js
```js
import { exportReport } from "optional-export";
export const onExport = () => exportReport();
```

## Supplied bundler output
- home.js: 830KB, including optional-export: 800KB; loaded on home entry.
- optional-export exports this supported public API; its initialization has side effects so it is retained.
