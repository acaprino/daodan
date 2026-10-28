<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
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

# Tauri 2 Core Plugins

Universal plugins (work on desktop AND mobile). For mobile-only plugins (biometric, haptics, nfc, barcode-scanner), see `plugins-mobile.md`.

## When to use

Choosing which plugin to add for a capability you need (filesystem, HTTP, store, SQL, deep links, dialogs, etc.) and registering it correctly.

## Universal plugin matrix

| Plugin | Desktop | Mobile | Use for |
|--------|---------|--------|---------|
| `fs` | yes | yes | File read/write (use `BaseDirectory.AppData` for cross-platform) |
| `http` | yes | yes | HTTP client that bypasses CORS (vs browser fetch) |
| `notification` | yes | yes | OS notifications |
| `clipboard-manager` | yes | yes | Clipboard read/write |
| `dialog` | yes | yes | Native open/save/message dialogs |
| `opener` | yes | yes | Open URL in system browser (preferred for OAuth) |
| `store` | yes | yes | Persistent key-value (JSON file under app data) |
| `sql` | yes | yes | SQLite |
| `log` | yes | yes | Structured logging to stdout/file/webview |
| `os` | yes | yes | Platform/arch detection |
| `deep-link` | yes | yes | Custom URL scheme handling |

Add via `npm run tauri add <name>` -- it patches Cargo.toml, package.json, and capabilities in one shot.

## Gotchas

- **Adding the plugin in `lib.rs` is half the job.** You also need the JS package (`npm i @tauri-apps/plugin-<name>`) AND the permission entry in `capabilities/default.json`. `tauri add` does all three; manual installs forget #3 every time.
- **`opener` vs `shell` for OAuth.** Use `opener::openUrl` for OAuth/external links -- it invokes the OS default browser. The `shell` plugin's `open` works on desktop but is more permissive than necessary and adds attack surface. Google specifically blocks OAuth in WebViews (see `authentication.md`).
- **`tauri-plugin-store` is async-by-default.** `await store.save()` is required after `set` to actually flush to disk -- without it the app exits and writes are lost.
- **`tauri-plugin-log` colors break on Windows terminals** that don't support ANSI codes -- gate `with_colors` behind `cfg!(debug_assertions)` if you ship CLI users.
- **`tauri-plugin-sql` migrations live in a `migrations` Vec** at builder time, not in app code. Adding migrations after launch requires a release.

## Minimal lib.rs registration shape

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_log::Builder::new().build())
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error");
}
```

## Deep-link config (desktop)

```json
// tauri.conf.json
"plugins": {
  "deep-link": { "desktop": { "schemes": ["myapp"] } }
}
```

For mobile deep-link config (Android Intent Filters, iOS Associated Domains), see `plugins-mobile.md`.

## Official docs

- Plugin index: https://v2.tauri.app/plugin/
- Per-plugin permission reference: each page has a "Permissions" section, e.g. https://v2.tauri.app/plugin/file-system/#permissions
- `tauri add` CLI: https://v2.tauri.app/reference/cli/#add
- Awesome Tauri (community plugins): https://github.com/tauri-apps/awesome-tauri

## Related

- `plugins-mobile.md` -- biometric, barcode, haptics, nfc, geolocation
- `frontend-patterns.md` -- JS-side usage examples for these plugins
- `authentication.md` -- why `opener` matters for OAuth
- `shell-plugin.md` -- when to reach for `shell` instead of `opener`
