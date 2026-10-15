<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# React 19 Compiler, External Store Selectors, Effects, and Bundle Optimization

On-demand reference for `react-development:react-performance-optimizer` and `react-development:react-best-practices`.

## 1. React Compiler (`babel-plugin-react-compiler`)

```javascript
// vite.config.js
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: ['babel-plugin-react-compiler'],
      },
    }),
  ],
});
```

- Automatically handles `useMemo`, `useCallback`, and `React.memo` inside React's render cycle (capturing ~30-40% of optimization opportunities).
- **Cannot fix external store re-renders:** Zustand, Jotai, Redux, and `useSyncExternalStore` hooks evaluate `Object.is(oldSelector, newSelector)` *before* React Compiler runs. If a selector returns a new object or array reference, the store triggers a re-render regardless of React Compiler.

## 2. External Store Selector Fixes (Zustand / Redux / Jotai)

### Fix 1: Narrow Selectors (Select Primitives)

```javascript
const isOnline = useStore((state) => state.agents[agentId]?.isOnline);  // boolean
const agentName = useStore((state) => state.agents[agentId]?.name);      // string
const hasActiveAgents = useStore((state) =>
  Object.values(state.agents).some((a) => a.isOnline)
);
```

### Fix 2: `useShallow` (Shallow Compare Objects/Arrays)

```javascript
import { useShallow } from 'zustand/react/shallow';

const { bid, ask, spread } = useStore(
  useShallow((state) => ({
    bid: state.orderbook.bestBid,
    ask: state.orderbook.bestAsk,
    spread: state.orderbook.spread,
  }))
);

const agentIds = useStore(useShallow((state) => Object.keys(state.agents)));
```

### Fix 3: `createSelector` (Memoized Derived State)

```javascript
import { createSelector } from 'reselect';

const selectOnlineCount = createSelector(
  [(state) => state.agents],
  (agents) => Object.values(agents).filter((a) => a.isOnline).length
);
```

### Fix 4: `subscribeWithSelector` (Outside React Render Loop)

```javascript
import { subscribeWithSelector } from 'zustand/middleware';

const useStore = create(subscribeWithSelector((set) => ({ agents: {} })));

useStore.subscribe(
  (state) => state.agents[agentId]?.isOnline,
  (isOnline) => updateStatusIndicator(isOnline)
);
```

### Jotai `atomFamily` for High-Frequency Granular Data

```javascript
import { atom } from 'jotai';
import { atomFamily } from 'jotai/utils';

const priceLevelAtom = atomFamily((price: number) =>
  atom({ price, quantity: 0, orders: 0 })
);

const PriceLevel = ({ price }: { price: number }) => {
  const [level] = useAtom(priceLevelAtom(price));
  return <Row data={level} />;
};
```

*(Note: Recoil was archived in Jan 2025; use Zustand for global state and Jotai for granular atom state.)*

## 3. React 19 Concurrency and Resource APIs

- **`use(promiseOrContext)`**: Reads Promises (with Suspense) or Context conditionally inside render.
- **`useOptimistic(state)`**: Immediate UI feedback while an async action is in flight.
- **`useDeferredValue(value)`**: Keep urgent updates (e.g. live price) immediate while deferring heavy renders (charts, filtered lists).

## 4. `useEffect` / `useCallback` Infinite Loop Fixes

```javascript
// BAD: fetchData updates usageStatus -> new callback ref -> effect re-fires infinitely
const fetchData = useCallback(async () => {
  await refreshUsage(); // mutates usageStatus
}, [usageStatus]);
useEffect(() => { fetchData(); }, [fetchData]);

// FIX 1: Read mutable state via ref to keep callback reference stable
const usageStatusRef = useRef(usageStatus);
usageStatusRef.current = usageStatus;
const fetchData = useCallback(async () => {
  const status = usageStatusRef.current;
  await refreshUsage();
}, []);

// FIX 2: Move user-triggered logic into the event handler instead of useEffect
```

## 5. Stale Closure Fixes (`useEffect` with `[]` Deps)

```javascript
// FIX 1: Ref indirection
const countRef = useRef(count);
countRef.current = count;

useEffect(() => {
  const handler = () => console.log(countRef.current);
  window.addEventListener('focus', handler);
  return () => window.removeEventListener('focus', handler);
}, []);

// FIX 2: experimental_useEffectEvent (React 19.x experimental)
import { experimental_useEffectEvent as useEffectEvent } from 'react';
const onFocus = useEffectEvent(() => console.log(count));
```

## 6. `useEffect` Cleanup Template

```javascript
useEffect(() => {
  const controller = new AbortController();
  const channel = new Channel<PriceUpdate>();
  channel.onmessage = (price) => updatePrice(price);
  invoke('subscribe_prices', { channel, signal: controller.signal });

  return () => {
    controller.abort();
    channel.onmessage = null;
    invoke('unsubscribe_prices');
  };
}, []);
```

## 7. Bundle Splitting, Virtualization, and TanStack Query

- **Route splitting + hover preload**: `const Settings = lazy(() => import('./pages/Settings'));` paired with `onMouseEnter={() => import('./pages/Settings')}`.
- **Tree shaking**: Import named icons (`import { Settings } from 'lucide-react'`) and `lodash-es` functions rather than barrel/namespace imports.
- **Vite manualChunks**: Split `vendor-react`, `vendor-charts`, and `vendor-state` in `build.rollupOptions.output.manualChunks`.
- **TanStack Virtual**: Always provide a stable `getItemKey: (index) => items[index].id` (never array index) with `overscan: 10`.
- **TanStack Query v5 (`gcTime` replaces `cacheTime`)**:
  - CRUD Web Apps: `staleTime: 5 * 60 * 1000`, `gcTime: 30 * 60 * 1000`, `refetchOnWindowFocus: true`.
  - Real-Time/Trading Apps: `staleTime: 0`, `gcTime: 5 * 60 * 1000`, `refetchOnWindowFocus: false`, `refetchOnReconnect: true`.
