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

# IPC Streaming and High-Frequency Data

This reference covers Tauri v2 IPC patterns optimized for high-frequency/streaming data (trading, real-time dashboards, telemetry). Extracted from the `tauri-desktop` agent to keep the agent body focused; use these patterns when sustained throughput above ~100 msg/sec is required.

## Channel API vs emit/listen

The `emit`/`listen` pair has per-event overhead (~0.5-2ms). For high-frequency updates, use `Channel` -- a typed, one-shot pipe that bypasses the event bus.

**Anti-pattern (events for streaming):**
```rust
// BAD: emit/listen has overhead for high-frequency updates
app.emit("price-update", &price)?;
```

**Correct (Channel API):**
```rust
use tauri::ipc::Channel;

#[tauri::command]
async fn subscribe_prices(channel: Channel<PriceUpdate>) -> Result<(), String> {
    let mut rx = PRICE_STREAM.subscribe();
    tokio::spawn(async move {
        while let Ok(price) = rx.recv().await {
            if channel.send(price).is_err() {
                break; // Frontend disconnected
            }
        }
    });
    Ok(())
}
```

**Frontend consumption:**
```typescript
import { Channel } from '@tauri-apps/api/core';

const channel = new Channel<PriceUpdate>();
channel.onmessage = (price) => {
  updatePriceAtom(price); // Target: < 1ms handling time
};
await invoke('subscribe_prices', { channel });
```

## Batching to reduce IPC count

Instead of N round-trips for N items, issue one command returning the batch:

```rust
#[tauri::command]
async fn get_orderbook_batch(symbols: Vec<String>) -> Result<Vec<OrderBook>, Error> {
    let books = fetch_all_orderbooks(&symbols).await?;
    Ok(books)
}
```

## Binary payloads (bypass JSON)

Use `tauri::ipc::Response::new(bytes)` to return raw `ArrayBuffer` to the frontend. Eliminates the JSON serialize/parse round-trip.

```rust
use tauri::ipc::Response;

#[tauri::command]
fn get_chart_data() -> Response {
    let data: Vec<u8> = generate_binary_chart_data();
    Response::new(data)
}
```

## Zero-copy serialization with rkyv

For complex structured payloads, rkyv lets the frontend read the archive in-place without parsing.

```rust
use rkyv::{Archive, Deserialize, Serialize};
use tauri::ipc::Response;

#[derive(Archive, Deserialize, Serialize)]
struct OrderBookSnapshot {
    bids: Vec<(f64, f64)>,
    asks: Vec<(f64, f64)>,
    timestamp: u64,
}

#[tauri::command]
async fn get_orderbook_binary() -> Response {
    let snapshot = generate_orderbook_snapshot();
    let bytes = rkyv::to_bytes::<_, 4096>(&snapshot)
        .expect("serialization failed");
    Response::new(bytes.to_vec())
}
```

**Frontend TypedArray consumption:**
```typescript
const buffer = await invoke<ArrayBuffer>('get_orderbook_binary');
const view = new Float64Array(buffer);
// Direct memory access -- zero parsing overhead
// Layout: [bid_price, bid_qty, ..., ask_price, ask_qty, ..., timestamp]
```

## Backpressure and memory protection

If the Rust backend produces data faster than the frontend consumes, the queue grows unbounded and causes OOM.

**Rust-side throttling (preferred -- drop stale data):**
```rust
use tokio::time::{interval, Duration};

async fn throttled_stream(channel: Channel<Vec<u8>>) {
    let mut tick = interval(Duration::from_millis(16)); // ~60 FPS cap
    let mut latest: Option<Vec<u8>> = None;

    loop {
        tokio::select! {
            data = data_rx.recv() => {
                latest = Some(data?); // Always keep only the latest frame
            }
            _ = tick.tick() => {
                if let Some(frame) = latest.take() {
                    let _ = channel.send(frame);
                }
            }
        }
    }
}
```

**Frontend worker queue limit:**
```typescript
let pendingFrames = 0;
const MAX_PENDING = 3;

channel.onmessage = (data) => {
  if (pendingFrames < MAX_PENDING) {
    pendingFrames++;
    worker.postMessage({ type: 'data', buffer: data }, [data]);
  }
  // else: drop frame silently
};

worker.onmessage = () => { pendingFrames--; };
```

**Memory monitoring (dev-only):**
```typescript
if (import.meta.env.DEV) {
  setInterval(() => {
    const mem = (performance as any).memory;
    if (mem && mem.usedJSHeapSize > 500 * 1024 * 1024) {
      console.warn('Heap exceeding 500MB -- check for leaks');
    }
  }, 5000);
}
```

## Rust concurrency patterns

### Tokio channel selection

| Channel | Use case | Example |
|---------|----------|---------|
| `mpsc` | Many producers, single consumer | Order submissions |
| `broadcast` | One producer, many consumers | Price distribution |
| `watch` | Single latest value | Connection status |
| `oneshot` | Single response | Request/response |

### Broadcast for price distribution

```rust
use tokio::sync::broadcast;

lazy_static! {
    static ref PRICE_TX: broadcast::Sender<PriceUpdate> = {
        let (tx, _) = broadcast::channel(1024);
        tx
    };
}

// Publisher (single source)
PRICE_TX.send(price_update)?;

// Subscribers (multiple consumers)
let mut rx = PRICE_TX.subscribe();
while let Ok(update) = rx.recv().await {
    process_price(update);
}
```

### I/O-bound vs CPU-bound separation

```rust
// I/O-bound: use tokio (async runtime)
async fn fetch_market_data() -> Result<Data> {
    let response = reqwest::get(url).await?;
    Ok(response.json().await?)
}

// CPU-bound: use rayon (thread pool)
fn calculate_indicators(data: &[Candle]) -> Vec<Indicator> {
    use rayon::prelude::*;
    data.par_iter()
        .map(|candle| compute_indicator(candle))
        .collect()
}

// CRITICAL RULE: Async code must not block > 10-100us without .await.
// Use spawn_blocking for CPU work in async context:
let result = tokio::task::spawn_blocking(|| {
    calculate_heavy_indicators(&data)
}).await?;
```

## Memory management

### React cleanup patterns

```typescript
useEffect(() => {
  const controller = new AbortController();
  const channel = new Channel<PriceUpdate>();

  channel.onmessage = (price) => updatePrice(price);
  invoke('subscribe_prices', { channel });

  return () => {
    controller.abort();
    channel.onmessage = null; // Clear reference
    invoke('unsubscribe_prices'); // Notify Rust to cleanup
  };
}, []);
```

### Rust Drop + Weak refs

```rust
impl Drop for PriceSubscriber {
    fn drop(&mut self) {
        self.channels.clear();
        self.buffer.shrink_to_fit();
    }
}

// Weak references for long-lived subscribers
use std::sync::Weak;

struct SubscriptionManager {
    subscribers: Vec<Weak<Subscriber>>,
}

impl SubscriptionManager {
    fn cleanup_dead(&mut self) {
        self.subscribers.retain(|s| s.strong_count() > 0);
    }
}
```
