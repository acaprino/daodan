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
