# Independent render-work scenes

React Compiler is disabled. React memo shallowly compares props by identity. Source and synthetic profiles below are complete for these two independent components; no other updates or optimizer apply.

## Default property identity

Requirement: changing a parent tick with no options supplied must preserve the equivalent chart without repeating its 40ms rendering. Per-tick permitted work is 5ms. Options are immutable and default to empty; the chart does not mutate them. ticks change at the parent, but are not passed to Chart.

```jsx
const Chart = React.memo(function Chart({options}) { return renderChart(options); });
function Panel({tick, options = []}) {
  return <Chart options={options}/>;
}
```

Supplied profile: renderChart(empty) costs 40ms and produces the same output for every empty array. No other Chart props exist; React memo uses the options reference, not array contents. Panel's own work is below 1ms.

## Unused loading-branch work

Requirement: while loading=true, show the Loading label using at most 5ms computation. Full user input is valid, but avatar output is not used until loading=false. renderAvatar is pure and costs 50ms on the supplied workload; rendering the loading label costs below 1ms.

```jsx
function Profile({loading, user}) {
  const avatar = renderAvatar(user);
  if (loading) return <span>Loading</span>;
  return avatar;
}
```

The supplied profile attributes the 50ms to renderAvatar, not a network request or device latency. No loading-state side effect requires it to run.
