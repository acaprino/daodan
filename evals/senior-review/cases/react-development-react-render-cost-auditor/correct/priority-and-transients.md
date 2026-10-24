# Independent priority and transient-state scenes

Supported React 19.2 concurrent root; Compiler disabled. These independent modules do not remount during their scoped event. Supplied synthetic scheduling/profile facts are bound to these snippets; no actual React/browser trace was executed by the reviewer.

## Urgent input versus derived results

Requirement: typing one new character must commit the input's new text before starting the next expensive result render. Old results may remain until the derived update completes. items identity is stable. Results is memoized by items/query identity; rendering a new query costs 60ms. An unchanged query bails out below 1ms. The supported scheduler's deferred-value contract returns the previous committed value in an urgent render and schedules its update afterward; no suspense/failure interrupts this bounded scene.

```jsx
const Results = React.memo(function Results({items, query}) {
  return renderResults(items, query);
});
function Search({items}) {
  const [text, setText] = React.useState('');
  const resultQuery = React.useDeferredValue(text);
  return <><input value={text} onChange={e => setText(e.target.value)}/><Results items={items} query={resultQuery}/></>;
}
```

Initial committed query is empty; the event types 'a'. The unchanged memoized Results bails out during the urgent input render, which commits before the deferred query render. Equivalent scheduling that preserves this required ordering is also valid; there is no universal millisecond promise from a hook name.

## Pending indication through actual transition commit

Requirement: selecting a new filter must show Updating after the event until the selected grid commits. The old grid may remain meanwhile. A scheduled update is not completion. FilterGrid is a memoized component; changed filter rendering costs 60ms, unchanged filter bails out. Event state updates are batched. The selected value is 'active', different from initial 'all'.

```jsx
function Filters() {
  const [filter, setFilter] = React.useState('all');
  const [pending, startTransition] = React.useTransition();
  function apply(next) {
    startTransition(() => setFilter(next));
  }
  return <><button onClick={() => apply('active')}>Active</button><span role="status">{pending ? 'Updating' : 'Ready'}</span><FilterGrid filter={filter}/></>;
}
```

The supported transition contract commits pending=true in the urgent update and clears it with the changed filter's commit. No asynchronous network call is involved. A correctly bound equivalent pending owner could also satisfy this requirement.

## Canvas-only pointer coordinates

Requirement: latest pointer coordinates must be available to the next host frame. They do not affect any React markup/state outcome and must not cause React renders. Only the frame callback draws coordinates. host.frames(fn) subscribes a frame callback, invokes it after completed event/commit work, and returns teardown. draw and host identities are stable; the parent never rerenders for pointer events.

```jsx
function Canvas({host, draw}) {
  const latest = React.useRef({x: 0, y: 0});
  React.useEffect(() => host.frames(() => draw(latest.current)), [host, draw]);
  const label = expensiveFrameChrome();
  return <canvas aria-label={label} onPointerMove={e => { latest.current = {x: e.clientX, y: e.clientY}; }}/>;
}
```

The supplied workload has 60 pointer events per second. expensiveFrameChrome is pure and costs 40ms per invocation, returning the same accessible label. Repeated React work has a 100ms-per-second budget; initial render is excluded. Browser drawing is separate and within its budget. No displayed coordinate or reactive consumer was removed; using refs for a value that did affect markup would need a different contract.
