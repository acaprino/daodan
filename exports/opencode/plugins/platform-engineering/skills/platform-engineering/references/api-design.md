<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# API Design and State Management

## API Versioning and Error Handling

### MUST

- **Version your APIs from day one** -- breaking changes without versioning strand old mobile clients that can't force-update like web. Use URL path versioning (`/v1/resource`) for public APIs.
- **Implement pagination** on all list endpoints -- unbounded result sets crash mobile clients and overload servers.
- **Use standardized error responses** (RFC 7807/RFC 9457 Problem Details) with `type`, `title`, `status`, `detail`, and `instance` fields.

## REST vs GraphQL

### DO

- **Choose REST for simple CRUD, public APIs, and when HTTP caching matters.** REST's URL-based caching works natively with CDNs, proxies, and browser HTTP caches.
- **Choose GraphQL for complex nested data needs and multi-platform backends.** Research shows 66% performance improvement for mobile apps migrating from REST to GraphQL by eliminating redundant network calls. Facebook invented GraphQL in 2012 specifically because REST was too inflexible for mobile.
- **Use cursor-based pagination** for real-time or large datasets (avoids the shifting-window problem); offset-based for fixed-page navigation.

### DON'T

- Use GraphQL for simple CRUD or when HTTP caching is critical -- GraphQL's POST-to-single-endpoint pattern breaks standard CDN caching.
- Expose GraphQL introspection or allow unbounded query depth in production.

### Platform Recommendations

| Platform | Recommendation |
|----------|---------------|
| **SPA** | REST or GraphQL both work well |
| **PWA** | REST preferred -- URL-based caching integrates cleanly with service workers |
| **Mobile** | GraphQL shines -- reduces round-trips on cellular networks; use persisted queries |
| **Desktop** | REST usually sufficient; aggregate multiple calls server-side |

## State Management by Platform

### SPA

- Separate server state from UI state. Use TanStack Query or SWR for server data.
- Client state: Zustand (~3KB, ideal for small-to-medium React apps), Redux Toolkit (~45KB, enterprise-grade), or Pinia (Vue 3 standard).
- Start with built-in state (useState, ref) and graduate to external libraries when state is shared across many components.
- DON'T use React Context as a global state manager -- it triggers unnecessary re-renders of all consumers on any state change.

### PWA

- Use IndexedDB (via Dexie.js or localForage) for structured offline data -- localStorage is limited to ~5MB and is synchronous/blocking.
- Use the Cache API with service workers for asset and API response caching.
- Implement Background Sync for queuing failed writes.

### Mobile

- Use platform-standard persistence (Room on Android, CoreData/SwiftData on iOS).
- Follow unidirectional data flow: UI to Action to State to UI.
- Android: ViewModel + StateFlow. iOS: SwiftUI + ObservableObject.
- Use WorkManager (Android) and BGTaskScheduler (iOS) for background sync.

### Desktop

- **Never share mutable state directly between main and renderer processes.**
- Electron: use `ipcMain.handle`/`ipcRenderer.invoke` with preload scripts and context isolation.
- Tauri: use the `invoke` command system -- the Rust core process manages global state (settings, DB connections).
- Keep shared state between frontend and backend minimal and well-structured.

## Official docs

- RFC 7807 / 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457.html
- GraphQL spec: https://spec.graphql.org/
- REST API design (Microsoft guidance): https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
- Google API design guide: https://cloud.google.com/apis/design
- TanStack Query: https://tanstack.com/query
- SWR: https://swr.vercel.app/
- Zustand: https://zustand-demo.pmnd.rs/
- Redux Toolkit: https://redux-toolkit.js.org/
- Pinia: https://pinia.vuejs.org/
- Dexie.js (IndexedDB wrapper): https://dexie.org/
- Android Room: https://developer.android.com/training/data-storage/room
- iOS SwiftData: https://developer.apple.com/documentation/swiftdata
- Tauri IPC: https://v2.tauri.app/develop/calling-rust/
- Electron context isolation: https://www.electronjs.org/docs/latest/tutorial/context-isolation
