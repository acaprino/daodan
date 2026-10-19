---
name: python-performance-optimization
description: >
  Measure first with cProfile, line_profiler, memory_profiler or py-spy, then fix what the numbers show.
  TRIGGER WHEN: debugging slow Python code, optimizing bottlenecks, cutting memory usage, or improving application performance.
---

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
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Python Performance Optimization

Profile, analyze, and optimize Python code for better performance - CPU profiling, memory optimization, and implementation best practices.

## When to Invoke

- User reports slow Python code or asks to speed up execution
- Profiling or benchmarking Python applications
- Reducing CPU time, memory consumption, or I/O wait
- Optimizing database queries or data processing pipelines
- Debugging memory leaks or excessive memory usage
- Choosing between parallelization strategies (threading, multiprocessing, async)
- Evaluating algorithmic vs implementation-level improvements

## Core Concepts

### Profiling Types
- **CPU Profiling**: Identify time-consuming functions (cProfile, py-spy)
- **Memory Profiling**: Track memory allocation and leaks (tracemalloc, memory_profiler)
- **Line Profiling**: Profile at line-by-line granularity (line_profiler)
- **Call Graph**: Visualize function call relationships

### Performance Metrics
- **Execution Time**: How long operations take
- **Memory Usage**: Peak and average memory consumption
- **CPU Utilization**: Processor usage patterns
- **I/O Wait**: Time spent on I/O operations

### Optimization Strategies
- **Algorithmic**: Better algorithms and data structures
- **Implementation**: More efficient code patterns
- **Parallelization**: Multi-threading/processing
- **Caching**: Avoid redundant computation
- **Native Extensions**: C/Rust for critical paths

## Quick Start

```python
import time
import timeit

# Simple timing
start = time.time()
result = sum(range(1000000))
print(f"Execution time: {time.time() - start:.4f} seconds")

# Accurate benchmarking with timeit
execution_time = timeit.timeit("sum(range(1000000))", number=100)
print(f"Average time: {execution_time/100:.6f} seconds")
```

## Profiling Tools Summary

### cProfile - CPU Profiling
```bash
python -m cProfile -o output.prof script.py
python -m pstats output.prof
```

### line_profiler - Line-by-Line
```bash
uv add --dev line-profiler    # or: uv tool install line-profiler
kernprof -l -v script.py
```

### memory_profiler - Memory Usage
```bash
uv add --dev memory-profiler
python -m memory_profiler script.py
```

### py-spy - Production Profiling
```bash
uv tool install py-spy
py-spy record -o profile.svg -- python script.py
py-spy top --pid 12345
```

## Key Optimization Patterns

### Data Structure Selection
- **Dict/Set for lookups**: O(1) vs O(n) for list search
- **Generators for large datasets**: Constant memory vs full list
- **__slots__ on classes**: Reduces per-instance memory

### Code-Level Optimizations
- List comprehensions over loops (faster C implementation)
- `str.join()` over `+=` concatenation
- Local variables over global access in hot loops
- Inline simple operations in tight loops
- Built-in functions (implemented in C)

### Caching
- `functools.lru_cache` for expensive pure functions
- `weakref.WeakValueDictionary` for GC-friendly caches

### Parallelization
- **multiprocessing**: CPU-bound tasks, true parallelism
- **threading**: I/O-bound tasks with shared memory
- **asyncio**: I/O-bound tasks with many concurrent operations

### Memory Optimization
- `tracemalloc` for detecting memory leaks (snapshot comparison)
- Iterators over lists for file/stream processing
- `weakref` caches to allow garbage collection

### Database Optimization
- Batch operations with `executemany()` and single commit
- Index frequently queried columns
- Select only needed columns (avoid `SELECT *`)
- Use `EXPLAIN QUERY PLAN` for analysis

## Benchmarking

```python
from functools import wraps
import time

def benchmark(func):
    """Decorator to benchmark function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.6f} seconds")
        return result
    return wrapper
```

For pytest-based benchmarking: `pip install pytest-benchmark`

## Best Practices

1. **Profile before optimizing** - measure to find real bottlenecks
2. **Focus on hot paths** - optimize code that runs most frequently
3. **Use appropriate data structures** - dict for lookups, set for membership
4. **Avoid premature optimization** - clarity first, then optimize
5. **Use built-in functions** - they are implemented in C
6. **Cache expensive computations** - use lru_cache
7. **Batch I/O operations** - reduce system calls
8. **Use generators** for large datasets
9. **Consider NumPy** for numerical operations
10. **Profile production code** - use py-spy for live systems

## Common Pitfalls

- Optimizing without profiling
- Using global variables unnecessarily
- Not using appropriate data structures
- Creating unnecessary copies of data
- Not using connection pooling for databases
- Ignoring algorithmic complexity
- Over-optimizing rare code paths
- Not considering memory usage

## Performance Checklist

- [ ] Profiled code to identify bottlenecks
- [ ] Used appropriate data structures
- [ ] Implemented caching where beneficial
- [ ] Optimized database queries
- [ ] Used generators for large datasets
- [ ] Considered multiprocessing for CPU-bound tasks
- [ ] Used async I/O for I/O-bound tasks
- [ ] Minimized function call overhead in hot loops
- [ ] Checked for memory leaks
- [ ] Benchmarked before and after optimization

## References

- `references/optimization-patterns.md` - detailed code examples for all profiling tools, optimization patterns (list comprehensions, generators, string concat, dict lookups, local vars, function call overhead), advanced optimization (NumPy, lru_cache, __slots__, multiprocessing, async I/O), database optimization, memory leak detection, and benchmarking tools

## Resources

- **cProfile**: Built-in CPU profiler
- **memory_profiler**: Memory usage profiling
- **line_profiler**: Line-by-line profiling
- **py-spy**: Sampling profiler for production
- **NumPy**: High-performance numerical computing
- **Cython**: Compile Python to C
- **PyPy**: Alternative Python interpreter with JIT
