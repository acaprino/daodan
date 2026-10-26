<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Backend and Platform Performance

## API and Database Performance

### MUST

- **Implement pagination on all list endpoints.** Cursor-based pagination maintains consistent performance regardless of dataset size -- offset pagination with `LIMIT 20 OFFSET 20000` still internally processes 20,000 rows.
- **Enable response compression** -- Brotli or gzip reduces JSON payloads by 70-90%.
- **Create indexes on frequently queried columns and foreign keys.** Without indexes, every query becomes a full table scan. 1M rows: indexed lookup ~1ms vs full scan ~1000ms+.
- **Use EXPLAIN/EXPLAIN ANALYZE on all slow queries.** Watch for `type=ALL` (full table scan), missing indexes, and unexpected row counts.
- **Implement connection pooling** -- documented improvement: 150ms to 12ms average response time, CPU from 80% to 15%.

### DO

- Migrate to HTTP/2+ for multiplexed requests and header compression. HTTP/3 (QUIC) adds 0-RTT connection establishment, particularly beneficial for mobile with frequent network switching.
- Use GraphQL field selection or REST sparse fieldsets to avoid transferring unnecessary data -- one optimization replacing `SELECT *` with specific columns on a 5-table join improved query time from 45 seconds to 2 seconds.
- Use read replicas for read-heavy workloads.

### DON'T

- Wrap indexed columns in functions -- `WHERE YEAR(created_at) = 2025` makes the index useless. Use range comparisons instead.
- Ignore ORM-generated SQL -- ORMs frequently produce N+1 patterns and unnecessary JOINs.
- Over-index -- every index slows writes and consumes storage.

## Mobile Battery and Memory

### MUST

- **Use push notifications instead of polling** for real-time updates -- polling wakes the cellular radio repeatedly, each cycle costing significant battery.
- Batch network requests to minimize radio wake-ups.
- **Detect and fix memory leaks** using LeakCanary (Android) and Xcode Instruments (iOS). Common causes: inner class references, unclosed listeners, retained activities/fragments.
- **Respond to memory pressure callbacks** -- `onTrimMemory()` on Android, `didReceiveMemoryWarning` on iOS -- by clearing caches and releasing resources.

### DO

- Virtualize long lists using RecyclerView (Android), UICollectionView (iOS), or FlatList (React Native). Never render 1000+ items in a ScrollView.
- Flatten view hierarchies -- deep nesting causes slow layout passes.
- Profile regularly with Android Profiler, Xcode Instruments, and Firebase Performance Monitoring.
- Targets: cold start <2 seconds, frame rendering <16ms (60fps), memory <100MB during normal operations.

### DON'T

- Run background services indefinitely -- the OS kills them and they drain battery. Use WorkManager/BGTaskScheduler with appropriate constraints.
- Allocate objects in tight loops -- triggers excessive garbage collection causing visible jank.
- Use continuous GPS tracking unless essential -- GPS reduces battery by up to 33%.

### Desktop (Electron) Memory

- Each window spawns a new Chromium renderer process consuming ~50-100MB. Six windows can consume 1GB+.
- Monitor and prevent IPC listener accumulation -- each `ipcRenderer.on()` without cleanup is a memory leak.
- Never use synchronous IPC (`ipcRenderer.sendSync`) -- blocks the renderer completely.
- Tauri comparison: 30-50MB idle memory vs Electron's 200-500MB, <500ms startup vs 1-2 seconds, 2.5-10MB installer vs 80-150MB.

## SSR, SSG, and Hybrid Rendering

### MUST

- **Never use pure client-side rendering for SEO-critical pages.** CSR delivers a blank page until JavaScript downloads, parses, executes, and fetches data.
- **Account for hydration cost** in SSR applications -- the entire component tree re-executes client-side. On large apps, hydration can take 1-3 seconds during which the page appears interactive but isn't.

### Rendering Strategy Comparison

| Strategy | Best for | SEO | Performance | Server cost |
|----------|---------|-----|-------------|-------------|
| **SSG** | Blogs, docs, marketing | Excellent | Fastest (CDN-served) | Lowest |
| **ISR** | E-commerce catalogs, news | Excellent | Fast (cached + revalidated) | Low-Medium |
| **SSR** | Personalized pages, search results | Excellent | Good (hydration cost) | Higher |
| **CSR** | Dashboards, admin panels | Poor | Slow initial load | Low server |

### DO

- Use SSG/ISR wherever possible -- pre-built static pages served via CDN achieve near-zero TTFB, 10-100x faster than server-rendered pages.
- Use hybrid rendering: SSG for marketing pages, SSR for product listings with fresh data, CSR for authenticated dashboards.
- Implement **Island Architecture** (Astro) or **React Server Components** (Next.js) to hydrate only interactive components.
- Implement streaming SSR (React 18+, Next.js App Router) to progressively stream HTML.
- Cache SSR responses at the CDN edge with appropriate TTLs.

### DON'T

- Use SSR for content that rarely changes -- you pay server render cost on every request unnecessarily.
- Hydrate the entire page if only small sections need interactivity.
- Ignore serverless SSR cold starts (100-500ms+) -- pre-warm functions or use edge rendering.

## CDN Caching

### MUST

- **Use content hashing for all static assets** -- filenames like `app.a1b2c3.css`, set `Cache-Control: public, max-age=31536000, immutable`.
- **Never long-cache the SPA entry point** (`index.html`) -- use `Cache-Control: no-cache` so users always get the latest version that references current hashed assets.

### DO

- Use `stale-while-revalidate` for API and dynamic content: `Cache-Control: public, max-age=60, stale-while-revalidate=300`.
- Implement tag-based cache purging for surgical invalidation.
- Use cache shielding to reduce origin load.

### DON'T

- Cache personalized or authenticated responses at the CDN layer without `Vary` headers or private caching.
- Purge the entire cache when a single resource changes.
- Vary cache on Cookie header unless truly necessary -- it destroys hit rates.

## Official docs

- HTTP/2 spec (RFC 9113): https://www.rfc-editor.org/rfc/rfc9113
- HTTP/3 spec (RFC 9114): https://www.rfc-editor.org/rfc/rfc9114
- MDN `Cache-Control`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
- `stale-while-revalidate` (RFC 5861): https://www.rfc-editor.org/rfc/rfc5861
- Postgres EXPLAIN ANALYZE: https://www.postgresql.org/docs/current/sql-explain.html
- Postgres index types: https://www.postgresql.org/docs/current/indexes-types.html
- LeakCanary (Android): https://square.github.io/leakcanary/
- Xcode Instruments: https://developer.apple.com/tutorials/instruments
- Android WorkManager: https://developer.android.com/topic/libraries/architecture/workmanager
- iOS BGTaskScheduler: https://developer.apple.com/documentation/backgroundtasks/bgtaskscheduler
- Next.js rendering modes: https://nextjs.org/docs/app/building-your-application/rendering
- React Server Components: https://react.dev/reference/rsc/server-components
- Astro Islands: https://docs.astro.build/en/concepts/islands/
- Tauri vs Electron benchmarks (community): https://github.com/Elanis/web-to-desktop-framework-comparison
