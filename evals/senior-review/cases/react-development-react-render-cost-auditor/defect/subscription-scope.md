# Event-only report identity

Requirement: clicking Export opens the then-current report ID. No report identity is displayed in this component. Repeated rendering attributable to background clock updates must cost at most 100ms per second. Initial render is outside that repeated-work budget.

Supported React/store contract: store.useSnapshot() subscribes this component to the entire root snapshot; the immutable root is replaced 40 times per second for clock-only updates and uses reference equality. store.getState() is a synchronous current snapshot read without subscription. Parent props are stable and the parent does not rerender on these ticks. React Compiler is disabled; no build optimizer removes this call. Clicks occur after pending snapshot commits.

```jsx
function ExportButton({store, open}) {
  const report = store.useSnapshot();
  const chrome = expensiveChrome();
  return <button onClick={() => open(report.reportId)}>{chrome}</button>;
}
```

Supplied candidate-bound synthetic profile: expensiveChrome is pure, returns the same label and costs 40ms per invocation. The independent clock does not affect the label or selected report. Clock updates are the only ongoing source of rendering; the view is mounted for the supplied one-second interval. This is input evidence, not measured runtime by the reviewer.
