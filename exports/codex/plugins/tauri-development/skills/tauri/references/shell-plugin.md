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

# Shell Plugin

Spawn child processes, run sidecar binaries, stream stdout/stderr. The hard parts are scope-based permissions and a few cross-platform spawn gotchas.

## When to use

Running a CLI tool the user has installed (git, node, ffmpeg) or a binary you ship as a sidecar. For OAuth and "open URL" actions, use `opener` instead -- safer scope.

## When NOT to use

External URL handoff (browsers, mailto, tel) -- use `tauri-plugin-opener` (`openUrl`). The shell plugin's `open` is more permissive than necessary.

## Gotchas

- **Every command needs an explicit scope entry** in `capabilities/default.json`. Tauri 2 dropped the v1 "allow any cmd" mode -- you list the exact `cmd` + `args` shape (or use `{ "validator": "<regex>" }` for variable args). Forgotten scopes throw at runtime, not at build.
- **Windows: pop-up cmd.exe windows.** Spawning console binaries on Windows shows a black flash unless you set `creation_flags(0x08000000)` (CREATE_NO_WINDOW) on the Command before `.spawn()`. Affects every CLI tool spawn from a windowed app.
- **PATH is not the user's PATH.** Spawned processes inherit the app's environment, which on macOS launched-from-Finder lacks `/usr/local/bin`, `/opt/homebrew/bin`, etc. Specify full paths or set `envs([...])` explicitly when calling Homebrew/MacPorts binaries.
- **Sidecar filenames must end with the target triple** (e.g. `my-tool-aarch64-apple-darwin`). Tauri picks the right one at runtime; missing the suffix = "sidecar not found." Get your triple via `rustc -Vv | grep host`.
- **`spawn()` returns a `Receiver` you must drain.** If you don't `recv()` events, the channel buffers up and stalls the child's stdio. Run the receive loop in `tokio::spawn`.
- **`child.kill()` is best-effort on Windows** -- console children may need extra teardown. Always set a sensible timeout for your wait loop, don't rely on `kill()` to immediately reap.
- **`shell:allow-stdin-write` is a separate permission** -- omitting it makes `child.write()` fail silently in release builds.

## Permission scope shape (the part that's easy to mis-spell)

```json
{
  "identifier": "shell:allow-execute",
  "allow": [
    { "name": "git-status", "cmd": "git", "args": ["status"] },
    { "name": "run-script", "cmd": "node", "args": [{ "validator": "\\S+" }] },
    { "name": "my-tool", "sidecar": true, "args": [{ "validator": ".*" }] }
  ]
}
```

Scope keys: `name` (referenced from JS as `Command.create('name')`), `cmd` (literal binary), `args` (mix of literal strings and `{validator: regex}`), `sidecar: true` for bundled binaries.

## Sidecar config

```json
// tauri.conf.json
"bundle": {
  "externalBin": ["binaries/my-tool"]
}
```

Files on disk: `binaries/my-tool-x86_64-pc-windows-msvc.exe`, `binaries/my-tool-aarch64-apple-darwin`, etc.

## Official docs

- Shell plugin: https://v2.tauri.app/plugin/shell/
- Permission reference: https://v2.tauri.app/plugin/shell/#default-permission
- Sidecar binaries: https://v2.tauri.app/develop/sidecar/
- Rust API: https://docs.rs/tauri-plugin-shell
- JS API: https://v2.tauri.app/reference/javascript/shell/

## Related

- `plugins-core.md` -- when to use `opener` instead
- `frontend-patterns.md` -- JS Channel pattern (used for streaming spawn output)
- `rust-patterns.md` -- error handling for spawn results
