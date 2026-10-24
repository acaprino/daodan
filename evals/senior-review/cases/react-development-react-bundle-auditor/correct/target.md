# Product/build packet

Requirement: home initial JavaScript at most 100KB; Export is used only after a click. Build evidence is supplied for exactly this source; do not claim to have built it.

## app.js
```js
export const onExport = async () => {
  const { exportReport } = await import("optional-export");
  return exportReport();
};
```

## Supplied bundler output
- home.js: 30KB; loaded on home entry.
- exporter.js: 800KB; requested by onExport only.
- optional-export exports this supported public API.
