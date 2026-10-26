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

# xterm.js Advanced API, Stream Handling, and Browser Resiliency

On-demand reference for `xterm:xtermjs-skill`.

## 1. Theming

Pass an `ITheme` object in options or update `term.options.theme = {...}` at runtime:

```ts
const darkTheme = {
  background: '#0d1117',
  foreground: '#c9d1d9',
  cursor: '#58a6ff',
  cursorAccent: '#0d1117',
  selectionBackground: '#264f78',
  black:   '#484f58', red:     '#ff7b72', green:   '#3fb950', yellow:  '#d29922',
  blue:    '#58a6ff', magenta: '#bc8cff', cyan:    '#39c5cf', white:   '#b1bac4',
  brightBlack:   '#6e7681', brightRed:   '#ffa198', brightGreen:  '#56d364',
  brightYellow:  '#e3b341', brightBlue:  '#79c0ff', brightMagenta:'#d2a8ff',
  brightCyan:    '#56d4dd', brightWhite: '#f0f6fc',
};

const term = new Terminal({ theme: darkTheme });
term.options.theme = darkTheme;
```

## 2. Key Event Handling

```ts
// Intercept keys before terminal processes them (return false to suppress, true to allow)
term.attachCustomKeyEventHandler((ev: KeyboardEvent) => {
  if (ev.ctrlKey && ev.shiftKey && ev.key === 'C') {
    const selection = term.getSelection();
    if (selection) navigator.clipboard.writeText(selection);
    return false;
  }
  return true;
});
```

## 3. Search (`SearchAddon`), Decorations, and Markers

```ts
searchAddon.findNext('search term', {
  regex: false,
  wholeWord: false,
  caseSensitive: false,
  incremental: false,
  decorations: {
    matchBackground: '#ffff0040',
    matchBorder: '#ffff00',
    matchOverviewRuler: '#ffff00',
    activeMatchBackground: '#ff000080',
    activeMatchBorder: '#ff0000',
    activeMatchColorOverviewRuler: '#ff0000',
  },
});
searchAddon.findPrevious('search term');

const marker = term.registerMarker(0);
const decoration = term.registerDecoration({
  marker,
  overviewRulerOptions: { color: '#ff0000' },
});
decoration?.onRender((element) => {
  element.style.backgroundColor = 'rgba(255,0,0,0.2)';
});
```

## 4. Parser Hooks (Custom Sequences)

```ts
// Register a custom OSC sequence handler (e.g. OSC 1337)
term.parser.registerOscHandler(1337, (data: string) => {
  console.log('Custom OSC 1337 payload:', data);
  return true;
});

// Register a custom CSI sequence handler
term.parser.registerCsiHandler({ final: 'z' }, (params) => {
  console.log('Custom CSI z params:', params);
  return true;
});
```

## 5. Key Terminal Options Reference

```ts
const term = new Terminal({
  cols: 80,
  rows: 24,
  cursorBlink: true,
  cursorStyle: 'block',      // 'block' | 'underline' | 'bar'
  scrollback: 10000,
  tabStopWidth: 4,
  convertEol: false,         // auto-add \r on \n (avoid for real PTY)
  disableStdin: false,
  allowProposedApi: false,
  allowTransparency: false,
  windowsPty: undefined,     // pass { backend: 'conpty' | 'winpty', buildNumber } on Windows (v5+)
  macOptionIsMeta: false,
  rightClickSelectsWord: false,
  fontSize: 14,
  fontFamily: 'monospace',
  fontWeight: 'normal',
  fontWeightBold: 'bold',
  lineHeight: 1.0,
  letterSpacing: 0,
  logLevel: 'info',          // 'debug' | 'info' | 'warn' | 'error' | 'off'
});
```

## 6. High-Performance Data Handling

When connected to high-throughput backends (LLMs, build tools, log streams), naive patterns cause UI freezes and data corruption:

- **UTF-8 Boundary Handling**: Multi-byte UTF-8 sequences can be split across read chunks from the PTY. Maintain a remainder buffer to reassemble them before passing to `term.write()`.
- **Coalescing PTY Output with React State**: Do not synchronize React state on every PTY `onData` chunk. Accumulate data in intermediate buffers, use `requestAnimationFrame` to extract terminal state at most 60 times per second, and never call `term.refresh()` during active output (it resets scroll position).
- **Cursor Ghosting During Rapid Output**: Hide the cursor during PTY writes with `term.write('\x1b[?25l')`, then use a debounced timer (80-100ms) that restores the cursor (`\x1b[?25h`) when output stabilizes. Consolidate cursor movement detection into a single regex.
- **Viewport Index Calculation**: Use `buffer.baseY + buffer.cursorY` for the absolute buffer line index (`cursorY` alone reads relative to the viewport).
- **Throttling Expensive UI Updates**: Throttle minimap/canvas re-renders to 150ms with a trailing render guarantee, cap hardware pixel dimensions at high DPR, and coalesce bookmark sync via `requestAnimationFrame`.

## 7. Stream Interception and ANSI Manipulation

- **ConPTY Windows Quirks**: Windows ConPTY corrupts supplementary plane characters (emoji) passed through `CreateProcessW`; strip or replace emoji before passing to ConPTY. When the shell resolves to a `.cmd`/`.bat` shim, use `cmd.exe` quoting (`""` for embedded quotes, `%%` for percent signs).
- **Paste Sanitization**: Filter terminal output control characters from pasted text, call `preventDefault()` on the native paste event to avoid double-paste, and debounce rapid paste events.
- **Banner/Output Interception**: Buffer initial PTY output until a delimiter is detected, replace with custom content, re-activate on screen clear (`ESC[2J`), and filter CUP positioning sequences during post-replacement cooldown. Prefer HTML overlays over inline ANSI manipulation where possible.

## 8. Browser Quirks and WebGL Resiliency

- **Container Initialization**: Never use `display: none` on the xterm container during initialization (`cols`/`rows` calculation fails). Use `visibility: hidden` or mount only when visible.
- **WebGL Context Loss After Sleep/Standby**: Use a 3-layer detection strategy triggering fallback to canvas:
  1. Addon callback: `webglAddon.onContextLoss(() => fallbackToCanvas())`
  2. DOM event: listen for `webglcontextlost` on the addon's canvas element
  3. Periodic health check: timer verifying the WebGL context is still valid
- **Tab Switching and Resize Throttling**: Defer `fitAddon.fit()` to the next `requestAnimationFrame` when switching tabs. Throttle terminal resize events and reset PTY size tracking after spawning a new process.

## 9. Viewport Virtualization and Coordinate Translation ("Coordinate Lying")

When injecting custom content (banners, status bars) unknown to the backend PTY, absolute cursor positioning (CUP sequences) shifts unless translated:

1. **Subtract injected rows** before sending dimensions to the PTY at spawn and on resize.
2. **Clamp values**: enforce a minimum (`Math.max(10, rows - CUP_ROW_OFFSET)`).
3. **Intercept and translate**: add the offset back to incoming CUP sequences (`\x1b[<row>;<col>H`) before `term.write()`. Derive the offset dynamically from actual banner content (`bannerLines.length`).
