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
