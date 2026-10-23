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

# Platform WebViews

Tauri uses three different web engines on desktop: WebView2 (Chromium) on Windows, WKWebView (Safari) on macOS, WebKitGTK (Safari-engine) on Linux. The version-matrix and UA strings live upstream -- this file is the strategy + the gotchas.

## When to use

Choosing CSS/JS features (Container Queries, View Transitions, OffscreenCanvas, etc.) and worrying about cross-engine compatibility, or debugging "works on my Windows machine but breaks on macOS/Linux."

## Engine baseline (worth memorizing)

| Platform | Engine | Updates with | Floor |
|----------|--------|--------------|-------|
| Windows | WebView2 (Chromium) | Edge runtime, evergreen | Win 10 1803+ |
| macOS | WKWebView (Safari) | macOS releases, NOT auto | macOS 10.15 |
| Linux | WebKitGTK | distro package | distro-dependent |

WebView2 is the most forgiving; WKWebView is tied to macOS version (a user on macOS 12 has Safari 15 features and nothing newer); WebKitGTK varies wildly by distro and is the realistic compatibility floor.

## Gotchas

- **`SharedArrayBuffer` is effectively absent on macOS/Linux.** Chromium-only. Don't design around it for cross-platform Tauri apps.
- **`OffscreenCanvas` 2D context is macOS 14+.** Windows works, Linux partial. Build a fallback path or restrict to Windows + recent macOS.
- **`structuredClone` only since Safari 15.4 (macOS 15)** -- on older macOS it silently doesn't exist. Polyfill or feature-detect.
- **CSS `env(safe-area-inset-*)` works natively only on WKWebView.** Android WebView and Linux ignore it (see `plugins-mobile.md` for the workaround).
- **Backdrop filter needs `-webkit-backdrop-filter` fallback** on WKWebView and older WebKitGTK.
- **`window.open()` blocked without user gesture** on WKWebView -- if you trigger it from a `setTimeout` or a fetch resolution, it silently fails.
- **WebView2 ignores system proxy** on some corporate networks -- traffic bypasses pac scripts. Surfaces as "works at home, breaks at customer site."
- **WebKitGTK on Wayland**: window operations (position, always-on-top) may not work; drag-and-drop may need `gtk-layer-shell`. X11 is more reliable.
- **`MediaRecorder` not on macOS until 14.5** -- if you're recording in-app, gate the feature.
- **DevTools differ wildly.**
  - Windows: `F12` or `window.open_devtools()` from Rust.
  - macOS: enable Safari → Settings → Advanced → "Show features for web developers", then Safari → Develop → [machine] → [app window]. There is no programmatic devtools toggle in release.
  - Linux: `WEBKIT_INSPECTOR_SERVER=127.0.0.1:9222` env var, then any browser at that URL.

## Cross-engine feature detection (the lazy-but-correct pattern)

```css
/* Container Queries */
@supports (container-type: inline-size) { .sidebar { container-type: inline-size; } }

/* View Transitions */
@supports (view-transition-name: any) { ::view-transition-old(root) { animation: fade-out .3s; } }

/* Backdrop filter fallback */
@supports not (backdrop-filter: blur(10px)) { .overlay { background: rgba(0,0,0,.8); } }
```

```typescript
// Engine detection -- WKWebView and WebKitGTK both report "WebKit"
const isChromium = /Chrome|Edg/.test(navigator.userAgent);
const hasOffscreen = typeof OffscreenCanvas !== 'undefined';
const hasSAB = typeof SharedArrayBuffer !== 'undefined';

// Reliable platform detection
import { platform } from '@tauri-apps/plugin-os';
const os = await platform(); // 'windows' | 'macos' | 'linux'
```

## Linux package dependency (in tauri.conf.json)

```json
"bundle": {
  "linux": {
    "deb": { "depends": ["libwebkit2gtk-4.1-0 (>= 2.40)"] },
    "rpm": { "depends": ["webkit2gtk4.1 >= 2.40"] }
  }
}
```

Without this, your `.deb` installs but the app refuses to launch with a missing-library error.

## Testing strategy

1. Develop on whatever you have (usually WebView2/Windows -- most lenient).
2. Smoke-test on macOS for WKWebView Safari-version surprises.
3. Compatibility floor on WebKitGTK (Ubuntu LTS = oldest WebKit you'll realistically hit).
4. CI matrix all three (see `ci-cd.md`).

## Official docs

- WebView2 release notes / feature tracking: https://learn.microsoft.com/en-us/microsoft-edge/webview2/release-notes
- WebKit feature support per Safari version: https://webkit.org/blog/category/web-inspector/ (and https://caniuse.com filtered by Safari)
- WebKitGTK release notes: https://webkitgtk.org/2.46.x/api-docs.html (replace version)
- MDN compatibility tables: https://developer.mozilla.org/en-US/docs/Web (each API page has a Browser compat section)
- caniuse: https://caniuse.com/

## Related

- `plugins-mobile.md` -- Android WebView safe-area workaround
- `ci-cd.md` -- the cross-platform matrix that catches engine-specific breakage
- `high-frequency-ui.md` -- engine-specific perf notes for trading UIs
