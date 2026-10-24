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
  const resultQuery = text;
  return <><input value={text} onChange={e => setText(e.target.value)}/><Results items={items} query={resultQuery}/></>;
}
```

Initial committed query is empty; the event types 'a'. There is no other priority boundary or compiler transform. The urgent root commits only after every changed urgent child has rendered.

## Pending indication through actual transition commit

Requirement: selecting a new filter must show Updating after the event until the selected grid commits. The old grid may remain meanwhile. A scheduled update is not completion. FilterGrid is a memoized component; changed filter rendering costs 60ms, unchanged filter bails out. Event state updates are batched. The selected value is 'active', different from initial 'all'.

```jsx
function Filters() {
  const [filter, setFilter] = React.useState('all');
  const [loading, setLoading] = React.useState(false);
  function apply(next) {
    setLoading(true);
    React.startTransition(() => setFilter(next));
    setLoading(false);
  }
  return <><button onClick={() => apply('active')}>Active</button><span role="status">{loading ? 'Updating' : 'Ready'}</span><FilterGrid filter={filter}/></>;
}
```

The supported transition contract marks a scheduled changed filter pending until its commit. The manual loading state above has no external writer or reconciliation hook. No asynchronous network call is involved.

## Canvas-only pointer coordinates

Requirement: latest pointer coordinates must be available to the next host frame. They do not affect any React markup/state outcome and must not cause React renders. Only the frame callback draws coordinates. host.frames(fn) subscribes a frame callback, invokes it after completed event/commit work, and returns teardown. draw and host identities are stable; the parent never rerenders for pointer events.

```jsx
function Canvas({host, draw}) {
  const [point, setPoint] = React.useState({x: 0, y: 0});
  const latest = React.useRef(point);
  React.useLayoutEffect(() => { latest.current = point; }, [point]);
  React.useEffect(() => host.frames(() => draw(latest.current)), [host, draw]);
  const label = expensiveFrameChrome();
  return <canvas aria-label={label} onPointerMove={e => setPoint({x: e.clientX, y: e.clientY})}/>;
}
```

The supplied workload has 60 pointer events per second. expensiveFrameChrome is pure and costs 40ms per invocation, returning the same accessible label. Repeated React work has a 100ms-per-second budget; initial render is excluded. Browser drawing is separate and within its budget. These are supplied workload facts, not measured frames here.
