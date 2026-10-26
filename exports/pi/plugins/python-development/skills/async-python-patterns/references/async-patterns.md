<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Async Python Patterns

Reference for the asyncio patterns you actually use in production: context managers, generators, queues, gather/TaskGroup, cancellation, semaphores, locks, timeouts. Most surface lives in docs.python.org; this file is the gotchas + the decision points.

## When to use

Designing or auditing async Python code. For the architectural opinions (when to use gather vs TaskGroup, when threading wins over asyncio, structured concurrency philosophy), see the SKILL.md.

## Patterns at a glance

| Pattern | Use case | Key construct |
|---------|----------|---------------|
| Async context manager | Resource lifecycle (connection, transaction) | `__aenter__` / `__aexit__` + `async with` |
| Async generator / iterator | Streaming results, paginated APIs | `async def` + `yield` + `async for` |
| Producer-consumer | Decouple ingress from processing | `asyncio.Queue` |
| Fan-out / parallel | N independent tasks, all results | `asyncio.gather` (or TaskGroup, Py 3.11+) |
| Concurrency limit | Throttle parallel work | `asyncio.Semaphore` |
| Race / first-completed | First-to-finish wins | `asyncio.wait(..., return_when=FIRST_COMPLETED)` |
| Timeout | Bound a call's wall time | `async with asyncio.timeout(s)` (Py 3.11+) |
| Backpressure | Producer slows when consumer falls behind | `Queue(maxsize=N)` |

## Gotchas

- **`asyncio.gather` swallows exceptions if `return_exceptions=True`** -- they become elements of the result list. Without that flag, the first exception cancels siblings and re-raises. Pick consciously; the wrong choice means errors disappear into a list.
- **`asyncio.TaskGroup` (Python 3.11+) is the modern replacement for gather** for structured concurrency. It guarantees all spawned tasks finish before exiting the `async with` block, propagates the first exception, and cancels siblings cleanly. Prefer TaskGroup over gather for new code.
- **Don't `asyncio.run()` inside an already-running loop.** That's a `RuntimeError`. From a Jupyter cell or a sync framework with its own loop, use `asyncio.get_event_loop().run_until_complete(...)` or restructure to `await` directly.
- **`asyncio.create_task` returns a Task you must hold a reference to.** The runtime keeps only weak refs -- if you don't store the Task, it can be garbage-collected mid-flight. The fix is `task = asyncio.create_task(...)` (assign).
- **Cancellation propagates through `await` points, not over CPU work.** A coroutine doing pure CPU work for 10 seconds cannot be cancelled until it next awaits. Move CPU work to `loop.run_in_executor()` or yield with `asyncio.sleep(0)`.
- **`asyncio.Queue` is NOT thread-safe.** Use `queue.Queue` (sync) or `janus.Queue` (sync↔async bridge) when crossing thread boundaries.
- **Async generators must be closed explicitly** (`await gen.aclose()`) if you stop iterating early -- otherwise the cleanup `finally` blocks may not run.
- **`asyncio.sleep(0)` yields control without sleeping** -- useful for cooperative scheduling inside CPU-bound loops.
- **`Semaphore` and `Lock` count differently**: `Semaphore(N)` allows N concurrent holders; `Lock` is `Semaphore(1)`. For "at most N parallel HTTP requests", use Semaphore.

## Async context manager (the canonical shape)

```python
class AsyncDatabaseConnection:
    def __init__(self, dsn: str): self.dsn = dsn; self.conn = None
    async def __aenter__(self):
        self.conn = await connect(self.dsn)
        return self.conn
    async def __aexit__(self, *exc):
        await self.conn.close()

async with AsyncDatabaseConnection(dsn) as conn: ...
```

For one-shot wrappers, `contextlib.asynccontextmanager` is shorter:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def db_connection(dsn):
    conn = await connect(dsn)
    try: yield conn
    finally: await conn.close()
```

## Producer-consumer with backpressure

```python
import asyncio

async def producer(q, n):
    for i in range(n):
        await q.put(f"item-{i}")        # blocks if maxsize reached -> backpressure
    await q.put(None)                    # sentinel for shutdown

async def consumer(q):
    while True:
        item = await q.get()
        if item is None:
            q.task_done()
            break
        await process(item)
        q.task_done()

async def main():
    q = asyncio.Queue(maxsize=10)        # bounded -> producer blocks under pressure
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q, 100))
        for _ in range(3):
            tg.create_task(consumer(q))
    await q.join()
```

## Concurrency limit (Semaphore)

```python
sem = asyncio.Semaphore(10)              # at most 10 concurrent

async def fetch(url):
    async with sem:
        return await http.get(url)

results = await asyncio.gather(*[fetch(u) for u in urls])
```

## Timeout (Python 3.11+)

```python
async with asyncio.timeout(5):           # raises TimeoutError after 5s
    result = await slow_api()

# Per-task: asyncio.wait_for(coro, timeout=5)
```

## Cancellation hygiene

```python
task = asyncio.create_task(work())
try:
    result = await asyncio.wait_for(task, timeout=2)
except asyncio.TimeoutError:
    task.cancel()
    try: await task
    except asyncio.CancelledError: pass   # absorb
```

`asyncio.CancelledError` derives from `BaseException` (NOT `Exception`) -- a bare `except Exception` will NOT catch it. This is intentional.

## CPU-bound work (don't block the loop)

```python
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(None, cpu_intensive_function, arg)
```

For `to_thread` (Python 3.9+, simpler):
```python
result = await asyncio.to_thread(cpu_intensive_function, arg)
```

`asyncio.to_thread` runs in the default ThreadPoolExecutor -- fine for I/O-blocking calls (legacy sync libraries) and small CPU work. For true CPU-bound, use `ProcessPoolExecutor`.

## Async iteration

```python
async def async_range(start, end, delay=0.1):
    for i in range(start, end):
        await asyncio.sleep(delay)
        yield i

async for n in async_range(1, 5): ...
```

## Race / first-completed

```python
done, pending = await asyncio.wait(
    [asyncio.create_task(slow_a()), asyncio.create_task(slow_b())],
    return_when=asyncio.FIRST_COMPLETED,
)
for t in pending: t.cancel()             # cancel losers
result = next(iter(done)).result()
```

## Official docs

- asyncio module: https://docs.python.org/3/library/asyncio.html
- `asyncio.TaskGroup` (Py 3.11+): https://docs.python.org/3/library/asyncio-task.html#task-groups
- `asyncio.timeout` (Py 3.11+): https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout
- `asyncio.to_thread`: https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
- Cancellation semantics: https://docs.python.org/3/library/asyncio-task.html#task-cancellation
- Async iterators / generators (PEP 525): https://peps.python.org/pep-0525/
- `contextlib.asynccontextmanager`: https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager
- Structured concurrency in Python (Trio's influence): https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/

## Related

- `async-python-patterns/SKILL.md` -- the architectural opinions (TaskGroup over gather, when threading wins, structured concurrency)
- `pytest-patterns/references/framework-config.md` -- pytest-asyncio configuration
- `python-performance-optimization` skill -- profiling async code
