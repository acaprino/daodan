<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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

# Frontend Patterns for Tauri

How the JS/TS side talks to Rust: invoke, channels, events, and the convention of typing them at the boundary.

## When to use

Designing the frontend layer of a Tauri app -- TypeScript wrappers around Rust commands, streaming progress channels, event listeners, plugin usage. Most code lives upstream; this file calls out the conventions that make the boundary maintainable.

## When NOT to use

Pure Rust code (commands, state, channels on the Rust side) -- see `rust-patterns.md`.

## Gotchas

- **Always wrap `invoke()` in a typed function**, never call `invoke` from React/Vue components directly. The string `'greet'` is a magic identifier; if it changes in Rust, you want one TS file to update, not 30 components.
- **`Channel<T>` is one-shot.** Construct a fresh `new Channel()` per call, set `.onmessage` *before* passing it to `invoke`, otherwise you race with the first emission.
- **`listen()` returns a Promise of an unlisten function**, not the function directly. The React-hook footgun:
  ```typescript
  // wrong: cleanup never runs
  useEffect(() => { listen('event', h); }, []);
  // right
  useEffect(() => {
    const p = listen('event', h);
    return () => { p.then(fn => fn()); };
  }, []);
  ```
- **`@tauri-apps/plugin-fs` `BaseDirectory.AppData`** is the only safe write target on iOS sandboxing -- writing to absolute paths fails silently in release builds.
- **Capabilities are explicit.** Adding a plugin in Rust does NOT grant the JS side permission. You must list `"<plugin>:default"` (or specific allow-rules) in `src-tauri/capabilities/default.json` or invocation throws "permission denied" only at runtime, not at build.
- **Platform detection is async.** `platform()` from `@tauri-apps/plugin-os` returns a Promise; do not call it inside a render path -- cache it once at app boot.

## Capabilities snippet (the file you forget exists)

```json
// src-tauri/capabilities/default.json
{
  "$schema": "https://schemas.tauri.app/config/2/Capability",
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:default",
    "http:default",
    "notification:default",
    "clipboard-manager:default",
    "opener:default"
  ]
}
```

## Official docs

- JS API `invoke` / `Channel`: https://v2.tauri.app/develop/calling-rust/
- Event API (`listen`, `emit`): https://v2.tauri.app/develop/calling-frontend/
- Capabilities + permissions: https://v2.tauri.app/security/capabilities/
- All `@tauri-apps/plugin-*` JS APIs: https://v2.tauri.app/plugin/
- `@tauri-apps/plugin-os`: https://v2.tauri.app/plugin/os/

## Related

- `rust-patterns.md` -- the Rust side of every example here
- `ipc-streaming.md` -- when Channels aren't enough (HFT/streaming)
- `plugins-core.md` -- per-plugin permission keys
