---
name: async-python-patterns
description: >
  Structure asyncio code: task management, cancellation, rate limiting, blocking calls kept off the event loop.
  TRIGGER WHEN: building async APIs, concurrent or I/O-bound systems needing non-blocking operations, or choosing between asyncio, threading and multiprocessing.
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

Implement asynchronous Python applications using asyncio, concurrent programming patterns, and async/await for building high-performance, non-blocking systems.

## When to Invoke

- Building async web APIs (FastAPI, aiohttp, Sanic)
- Implementing concurrent I/O operations (database, file, network)
- Creating web scrapers with concurrent requests
- Developing real-time applications (WebSocket servers, chat systems)
- Processing multiple independent tasks simultaneously
- Building microservices with async communication
- Optimizing I/O-bound workloads
- Implementing async background tasks and queues
- Deciding between threading, multiprocessing, and asyncio

## Core Concepts

### Event Loop
- Single-threaded cooperative multitasking
- Schedules coroutines for execution
- Handles I/O operations without blocking
- Manages callbacks and futures

### Coroutines
Functions defined with `async def` that can be paused and resumed.

```python
async def my_coroutine():
    result = await some_async_operation()
    return result
```

### Tasks
Scheduled coroutines that run concurrently on the event loop.

### Futures
Low-level objects representing eventual results of async operations.

### Async Context Managers
Resources that support `async with` for proper cleanup.

### Async Iterators
Objects that support `async for` for iterating over async data sources.

## Quick Start

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

asyncio.run(main())
```

## Fundamental Patterns

### Basic Async/Await

```python
import asyncio

async def fetch_data(url: str) -> dict:
    await asyncio.sleep(1)  # Simulate I/O
    return {"url": url, "data": "result"}

async def main():
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

### Concurrent Execution with gather()

```python
import asyncio
from typing import List

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.5)
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_all_users(user_ids: List[int]) -> List[dict]:
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)

asyncio.run(fetch_all_users([1, 2, 3, 4, 5]))
```

### Task Creation and Management

```python
import asyncio

async def background_task(name: str, delay: int):
    await asyncio.sleep(delay)
    return f"Result from {name}"

async def main():
    task1 = asyncio.create_task(background_task("Task 1", 2))
    task2 = asyncio.create_task(background_task("Task 2", 1))

    # Do other work while tasks run
    await asyncio.sleep(0.5)

    result1 = await task1
    result2 = await task2
    print(f"Results: {result1}, {result2}")

asyncio.run(main())
```

### Error Handling

```python
import asyncio
from typing import Optional

async def safe_operation(item_id: int) -> Optional[dict]:
    try:
        return await risky_operation(item_id)
    except ValueError as e:
        print(f"Error: {e}")
        return None

async def process_items(item_ids):
    tasks = [safe_operation(iid) for iid in item_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = [r for r in results if r is not None and not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    return successful
```

### Timeout Handling

```python
import asyncio

async def with_timeout():
    try:
        result = await asyncio.wait_for(slow_operation(5), timeout=2.0)
    except asyncio.TimeoutError:
        print("Operation timed out")
```

### Semaphore for Rate Limiting

```python
import asyncio
from typing import List

async def api_call(url: str, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        await asyncio.sleep(0.5)  # Simulate API call
        return {"url": url, "status": 200}

async def rate_limited_requests(urls: List[str], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [api_call(url, semaphore) for url in urls]
    return await asyncio.gather(*tasks)
```

## Decision Framework

### When to Use asyncio
- I/O-bound tasks (network, database, file)
- Many concurrent connections
- Web servers and API clients
- WebSocket applications

### When to Use threading
- I/O-bound tasks with existing sync libraries
- Simple parallelism needs
- Interfacing with C extensions that release GIL

### When to Use multiprocessing
- CPU-bound tasks (computation, data processing)
- Need true parallelism (bypasses GIL)
- Tasks that don't need shared memory

## Common Pitfalls

### Forgetting await
```python
# Wrong - returns coroutine object
result = async_function()

# Correct
result = await async_function()
```

### Blocking the Event Loop
```python
# Wrong - blocks event loop
import time
async def bad():
    time.sleep(1)  # Blocks!

# Correct
async def good():
    await asyncio.sleep(1)  # Non-blocking
```

### Not Handling Cancellation
```python
async def cancelable_task():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Perform cleanup
        raise  # Re-raise to propagate
```

### Mixing Sync and Async Code
```python
# Wrong
def sync_function():
    result = await async_function()  # SyntaxError!

# Correct
def sync_function():
    result = asyncio.run(async_function())
```

## Testing Async Code

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data("https://api.example.com")
    assert result is not None

@pytest.mark.asyncio
async def test_with_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(5), timeout=1.0)
```

## Best Practices

1. **Use asyncio.run()** for entry point (Python 3.7+)
2. **Always await coroutines** to execute them
3. **Use gather() for concurrent execution** of multiple tasks
4. **Implement proper error handling** with try/except
5. **Use timeouts** to prevent hanging operations
6. **Pool connections** for better performance
7. **Avoid blocking operations** in async code - use run_in_executor
8. **Use semaphores** for rate limiting
9. **Handle task cancellation** properly
10. **Test async code** with pytest-asyncio

## References

- `references/async-patterns.md` - async context managers, async iterators/generators, producer-consumer pattern, async locks and synchronization, web scraping with aiohttp, async database operations, WebSocket server implementation, connection pools, batch operations, running blocking operations in executors

## Resources

- **Python asyncio documentation**: https://docs.python.org/3/library/asyncio.html
- **aiohttp**: Async HTTP client/server
- **FastAPI**: Modern async web framework
- **asyncpg**: Async PostgreSQL driver
- **motor**: Async MongoDB driver
