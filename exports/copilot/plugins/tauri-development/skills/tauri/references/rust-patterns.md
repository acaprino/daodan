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

# Rust Patterns for Tauri

Backend conventions: entry point, commands, state, channels, events, error handling. The lib.rs/main.rs split and `cfg(mobile)` are the only Tauri-specific bits; the rest is idiomatic Rust.

## When to use

Writing or auditing the `src-tauri/src/` code of a Tauri 2 app. For the JS side of the same boundary, see `frontend-patterns.md`.

## Gotchas

- **All code in `lib.rs`, NOT `main.rs`.** Mobile builds invoke `lib::run()` via `mobile_entry_point` and never see `main.rs`. Putting your `tauri::Builder` in `main.rs` makes desktop work and mobile silently fail to start.
- **`#[cfg_attr(mobile, tauri::mobile_entry_point)]` on `pub fn run()`** is mandatory for mobile. Missing it = the app launches and immediately closes on Android/iOS.
- **`#[cfg(mobile)]` / `#[cfg(desktop)]` for plugin registration** -- mobile-only plugins (biometric, haptics, nfc) won't compile for desktop targets. Without the cfg gate, your `cargo tauri build` fails on the wrong platform.
- **State must be `Send + Sync`.** Use `Mutex<T>` (or `tokio::sync::Mutex` for async commands) -- `RefCell` will not compile through `State<T>`. Forgetting `tokio::sync::Mutex` in async commands deadlocks the runtime under contention.
- **Custom error types need manual `serde::Serialize`.** `thiserror` gives you `Display`; Tauri's IPC needs `Serialize`. The standard pattern (in the snippet below) serializes the error via `to_string()` so the JS side just sees the message.
- **`Channel::send()` returns `Result` -- ignore it intentionally** with `.ok()`. The frontend may have torn down the channel; that's not a backend error.
- **Async commands must return `Result<T, E>` for both arms to serialize**, even if you don't expect failures. `async fn foo() -> String` works but you lose the error-propagation channel.

## The error-handling pattern (the one piece worth memorizing)

```rust
#[derive(Debug, thiserror::Error)]
enum AppError {
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Custom error: {0}")]
    Custom(String),
}

impl serde::Serialize for AppError {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&self.to_string())
    }
}

#[tauri::command]
async fn risky() -> Result<String, AppError> { Ok("ok".into()) }
```

## Cargo.toml release profile (mirror in CI)

```toml
[profile.release]
lto = true
opt-level = "s"      # "3" for speed
codegen-units = 1
strip = true
panic = "abort"
```

## Official docs

- Commands + state + channels: https://v2.tauri.app/develop/calling-rust/
- Events from Rust: https://v2.tauri.app/develop/calling-frontend/
- Plugin authoring + builder API: https://v2.tauri.app/develop/plugins/
- Conditional compilation in Rust: https://doc.rust-lang.org/reference/conditional-compilation.html

## Related

- `frontend-patterns.md` -- the TS side of every example here
- `plugins-core.md` -- which plugins to register and their permission keys
- `ipc-streaming.md` -- composite patterns for high-throughput Rust→JS streams
