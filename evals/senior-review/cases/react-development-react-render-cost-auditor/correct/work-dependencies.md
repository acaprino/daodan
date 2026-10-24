# Independent derivation dependencies

Requirement: sortOrder can change without items or query changing. A sort-only event must leave the already-computed filter result current and consume at most 5ms computation. filterRows is pure and depends only on items/query; sortRows is pure and depends only on items/sortOrder. Both outputs are displayed separately. Items identity is stable until contents change. Supported React useMemo caches while dependencies are Object.is-equal; Compiler is disabled, no remount/replay occurs in this bounded event.

```jsx
function Summary({items, query, sortOrder}) {
  const filtered = React.useMemo(() => filterRows(items, query), [items, query]);
  const sorted = React.useMemo(() => sortRows(items, sortOrder), [items, sortOrder]);
  return <Output filtered={filtered} sorted={sorted}/>;
}
```

Supplied synthetic profile: filterRows costs 60ms; sortRows plus Output/render overhead costs 2ms. The filter has no required side effect on sort changes. This packet does not assert timing of any real device.

## Bounded primitive expression

The same project also contains this independent component. Effective profile attributes below 0.01ms per render to this memo and all its bookkeeping. Its workload is at most one render per second and its accepted CPU budget is 1ms per second. The following source and supported React dependency equality meet the functional result requirement for every boolean enabled. No style rule prohibits memo here.

```jsx
function Counter({enabled}) {
  const count = React.useMemo(() => enabled ? 1 : 0, [enabled]);
  return <span>{count}</span>;
}
```
