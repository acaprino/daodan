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

# Window Management

Multi-window, frameless, system tray, native menus, and global shortcuts. All standard Tauri API -- this file calls out the gotchas, not the surface.

## When to use

Adding a second window (settings, splash, overlay), system tray icon, native menu bar, or system-wide hotkey to a desktop app.

## When NOT to use

Mobile -- multi-window, tray, menus, and global shortcuts are desktop-only. Mobile apps have a single root window.

## Gotchas

- **Always check existence before creating.** `WebviewWindowBuilder::new(app, "settings", ...)` with a label that already exists throws -- you want `app.get_webview_window("settings").map(|w| w.set_focus())` first.
- **Frameless drag region is CSS, not config.** `-webkit-app-region: drag` on a div makes it the title bar; `no-drag` on buttons inside it lets clicks through. Forgetting `no-drag` makes minimize/close unusable.
- **Tray icon needs an explicit icon source.** `app.default_window_icon().unwrap().clone()` works; passing a path that doesn't exist gives no error and a blank tray slot.
- **Close-to-tray needs `api.prevent_close()` AND `window.hide()`.** Just preventing close leaves the window invisible-but-existing; the user can't bring it back without the tray menu.
- **Menu accelerators: `CmdOrCtrl`, not `Ctrl`.** Using `Ctrl` directly on macOS shows the wrong glyph and binds the wrong modifier. Always `CmdOrCtrl+S` for cross-platform.
- **`CheckMenuItem` state is *not* persisted** -- toggle handler must store + restore from your app state.
- **Global shortcuts can collide silently.** `register()` returns `Result` but a successful register on top of an existing OS-level binding may "win" in unpredictable ways. Document required hotkeys and let users override.
- **`onCloseRequested` fires per-window**, not for the whole app. If you want "quit on last window closed," check `app.webview_windows().len()` in the handler.
- **Window labels must be unique strings** that you'll hardcode across both Rust and JS -- there's no shared enum. A typo gives you `None` from `get_webview_window`.

## The check-then-create pattern (Rust)

```rust
if let Some(win) = app.get_webview_window("settings") {
    win.set_focus().map_err(|e| e.to_string())?;
    return Ok(());
}
WebviewWindowBuilder::new(&app, "settings", WebviewUrl::App("/settings".into()))
    .title("Settings").inner_size(600.0, 400.0).center().build()?;
```

## Capabilities for global-shortcut

```json
"permissions": [
  "core:default",
  "global-shortcut:allow-register",
  "global-shortcut:allow-unregister"
]
```

## Inter-window comm options

- Tauri events (`emit` / `listen`) -- broadcast or per-window with `get_webview_window("x").emit(...)`.
- Shared `tauri::State<T>` -- both windows read/write through commands. Better for large state; events are better for notifications.

## Official docs

- WebviewWindow API (Rust): https://docs.rs/tauri/latest/tauri/webview/struct.WebviewWindowBuilder.html
- WebviewWindow API (JS): https://v2.tauri.app/reference/javascript/api/namespacewebviewwindow/
- Tray icon: https://v2.tauri.app/learn/system-tray/
- Menu API: https://v2.tauri.app/learn/window-menu/
- Global shortcut plugin: https://v2.tauri.app/plugin/global-shortcut/
- Window events: https://v2.tauri.app/develop/calling-frontend/#window-events

## Related

- `frontend-patterns.md` -- `getCurrentWebviewWindow()` and event listening
- `rust-patterns.md` -- state management and command shape
- `plugins-core.md` -- the global-shortcut plugin alongside core plugins
