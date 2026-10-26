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
