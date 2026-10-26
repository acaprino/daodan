<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# High-Frequency UI Rendering in Tauri

This reference covers frontend rendering strategies for high-update-rate UIs (trading dashboards, orderbooks, heatmaps, real-time charts). Extracted from the `tauri-desktop` agent to keep the agent body focused.

## State management for trading workloads

### Zustand with atomic selectors

```typescript
// BAD: Destructuring entire store causes re-renders on ANY change
const { price, volume, trades } = useStore();

// GOOD: Atomic selectors -- component re-renders only when its value changes
const price = useStore((state) => state.price);
const volume = useStore((state) => state.volume);
```

### Jotai for granular data (orderbook, price levels)

```typescript
// Each price level is its own atom -- surgical updates
const priceLevelAtom = atomFamily((price: number) =>
  atom({ price, quantity: 0, orders: 0 })
);

// Only components watching a specific price level re-render
const PriceLevel = ({ price }: { price: number }) => {
  const [level] = useAtom(priceLevelAtom(price));
  return <Row data={level} />;
};
```

### Computed values with createSelector

```typescript
import { createSelector } from 'reselect';

const selectSpread = createSelector(
  [(state) => state.bestBid, (state) => state.bestAsk],
  (bid, ask) => ask - bid // Recalculates only when inputs change
);
```

### Critical vs deferrable updates

```typescript
// Critical: price must be immediate
const price = useStore((s) => s.price);

// Deferrable: chart can lag during heavy updates
const chartData = useDeferredValue(useStore((s) => s.chartData));
```

### React Compiler considerations

- The Compiler handles ~30-40% of memoization automatically.
- Manual optimization still needed for:
  - External library callbacks (WebSocket, IndexedDB)
  - Complex derived state
  - High-frequency update handlers
  - WebSocket message processors

## Virtualization for large datasets

TanStack Virtual can handle 1M+ rows with careful key selection.

```typescript
const virtualizer = useVirtualizer({
  count: orderbook.length, // Can handle 1M+ items
  getScrollElement: () => parentRef.current,
  estimateSize: () => 24,  // Row height in pixels
  overscan: 10,            // Extra rows for smooth scrolling
  getItemKey: (index) => orderbook[index].price, // Stable keys, NOT index
});

return (
  <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
    <div style={{ height: virtualizer.getTotalSize() }}>
      {virtualizer.getVirtualItems().map((row) => (
        <OrderBookRow key={row.key} index={row.index} />
      ))}
    </div>
  </div>
);
```

### Key strategy

```typescript
// BAD: Index as key -- causes re-renders when data shifts
getItemKey: (index) => index

// GOOD: Stable identifier -- maintains component identity
getItemKey: (index) => items[index].id
getItemKey: (index) => items[index].price  // For orderbook
```

## Extreme high-frequency rendering (> 60 FPS)

Virtual DOM diffing cannot sustain sub-16ms ticks for thousands of rows. Delegate data-dense rendering to Canvas driven from a Web Worker.

**React shell + OffscreenCanvas in Worker:**
```typescript
const canvasRef = useRef<HTMLCanvasElement>(null);

useEffect(() => {
  const canvas = canvasRef.current!;
  const offscreen = canvas.transferControlToOffscreen();
  const worker = new Worker(new URL('./renderWorker.ts', import.meta.url));

  // Transfer canvas ownership to worker -- React no longer touches these pixels
  worker.postMessage({ type: 'init', canvas: offscreen }, [offscreen]);

  // Connect Tauri IPC binary channel directly to worker
  const channel = new Channel<ArrayBuffer>();
  channel.onmessage = (data) => {
    worker.postMessage({ type: 'data', buffer: data }, [data]);
  };
  invoke('subscribe_orderbook_binary', { channel });

  return () => worker.terminate();
}, []);
```

**renderWorker.ts (off main thread):**
```typescript
let ctx: OffscreenCanvasRenderingContext2D;

self.onmessage = (e) => {
  if (e.data.type === 'init') {
    ctx = e.data.canvas.getContext('2d')!;
  } else if (e.data.type === 'data') {
    const view = new Float64Array(e.data.buffer);
    renderOrderbook(ctx, view); // Pure canvas drawing, no DOM
  }
};
```

### When to use Canvas vs DOM

| Scenario | Approach |
|----------|----------|
| < 100 rows, < 10 updates/sec | React + virtualization |
| 100-1000 rows, 10-60 updates/sec | React + Jotai atomic + virtualization |
| > 1000 rows or > 60 updates/sec | Canvas + Web Worker |
| Charts with streaming data | Canvas (lightweight-charts or custom) |

## Build optimization for trading apps

### Cargo.toml release profile

```toml
[profile.release]
codegen-units = 1      # Better optimization, slower compile
lto = true             # Link-time optimization
opt-level = 3          # Maximum optimization
strip = true           # Remove symbols
panic = "abort"        # Smaller binary

[profile.release.package."*"]
opt-level = 3
```

### Windows linker (rust-lld)

Problem: MSVC default linker (`link.exe`) stalls 30-60s on final link. Rust's bundled LLD is 3-12x faster.

```bash
rustup component add llvm-tools
```

`.cargo/config.toml`:
```toml
[target.x86_64-pc-windows-msvc]
linker = "rust-lld.exe"
```

Caveats: large projects may hit the COFF 65k symbol limit; avoid combining with `-Ctarget-cpu=native`.

### Vite chunk splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    target: 'esnext',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react':  ['react', 'react-dom'],
          'vendor-charts': ['lightweight-charts'],
          'vendor-state':  ['zustand', 'jotai'],
        },
      },
    },
  },
});
```

### Lazy-load non-critical routes

```typescript
const Settings = lazy(() => import('./pages/Settings'));
const History  = lazy(() => import('./pages/History'));
// Trading dashboard loads immediately, others on demand
```

## Performance targets (trading UI)

| Metric | Target | Critical threshold |
|--------|--------|--------------------|
| Startup time | < 1s | < 2s |
| Memory baseline | < 100MB | < 150MB |
| Memory growth | < 5MB/hour | < 10MB/hour |
| Frontend bundle | < 3MB | < 5MB |
| Frame rate | 60 FPS stable | > 30 FPS minimum |
| IPC latency | < 0.5ms | < 1ms |
| Price update -> render | < 5ms | < 16ms |
