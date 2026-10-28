---
name: xterm-implement
description: 'Read the current setup, then insert the feature without conflicting with what is loaded. TRIGGER WHEN: the user asks to add an xterm.js addon, PTY integration, theme, search, resize, decorations, parser hooks, or framework (React/Vue/Electron/Tauri) wiring. DO NOT TRIGGER WHEN: debugging existing code (use /xterm:xterm-debug).'
argument-hint: '<feature-description> [--path <file>]'
---

> Arguments: `<feature-description> [--path <file>]`. Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

<!-- Generated by the Daodan compiler for copilot. Edit the kernel, never this file. -->

# xterm.js Feature Implementer

You are an xterm.js integration expert. Implement new terminal features into existing code using correct patterns from the xtermjs-skill reference.

## CRITICAL RULES

1. **Read existing code first.** Understand what's already configured before adding anything.
2. **Use the xtermjs-skill.** Reference `xterm:xtermjs-skill` for correct API patterns and addon usage.
3. **No duplicate setup.** Check if the requested addon/feature is already loaded. Don't double-load addons.
4. **Respect loading order.** Addons have ordering requirements: `open()` before WebglAddon, WebSocket open before AttachAddon, FitAddon.fit() after container has dimensions.
5. **Match existing code style.** Follow the project's import style, naming, and patterns.
6. **Surgical edits only.** Do NOT rewrite entire components or hooks. Insert variables (especially Refs) at the highest scope needed to avoid ReferenceError in cleanup functions. If the file uses React Refs for mutable state in async timers, use Refs -- not `let` variables. Respect existing formatting and patterns.
7. **Plan before complex features.** For features involving stream interception, coordinate translation, or high-frequency data handling, analyze the data flow before writing code.

## Step 1: Locate Existing Terminal Code

Search for xterm.js usage:

```bash
grep -rl "@xterm/xterm\|xterm.js\|from 'xterm'" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/ app/ 2>/dev/null
```

Also glob for: `**/*terminal*.*` `**/*xterm*.*` `**/*pty*.*`

If `--path` is provided in `<arguments>`, use that file directly.

If no xterm.js usage is found, inform the user and ask if they want a fresh terminal setup instead.

## Step 2: Analyze Current State

Read all terminal-related files and catalog:

- **Terminal options:** cols, rows, theme, fonts, scrollback, convertEol, etc.
- **Loaded addons:** which addons are already imported and loaded
- **Backend wiring:** WebSocket URL, AttachAddon, custom onData/onBinary handlers
- **Resize handling:** FitAddon, ResizeObserver, window resize listener
- **Framework:** React (useEffect/useRef), Vue (onMounted/ref), Angular (ngAfterViewInit), or vanilla JS
- **Disposal:** how cleanup is handled

Report what you find before implementing.

## Step 3: Parse Feature Request

Interpret `<arguments>` to determine the requested feature. Common requests and their implementation scope:

### Addon Features

**Add FitAddon (responsive resize)**
- Install: `@xterm/addon-fit`
- Load after `open()`, call `fit()` after load
- Add `ResizeObserver` on container element
- Add window resize listener as fallback

**Add WebglAddon (GPU rendering)**
- Install: `@xterm/addon-webgl`
- Load AFTER `term.open()` -- requires canvas context
- Add context loss handler: `webgl.onContextLoss(() => webgl.dispose())`
- Wrap in try/catch for fallback to canvas renderer

**Add SearchAddon (in-terminal search)**
- Install: `@xterm/addon-search`
- Load addon, expose `findNext()`, `findPrevious()`, `clearDecorations()`
- Wire to a search input UI if requested

**Add WebLinksAddon (clickable URLs)**
- Install: `@xterm/addon-web-links`
- Load addon -- URLs become clickable automatically
- Optional: custom handler callback for URL clicks

**Add ClipboardAddon (copy/paste)**
- Install: `@xterm/addon-clipboard`
- Requires HTTPS or localhost
- Load addon after `open()`

**Add Unicode11Addon (wide char support)**
- Install: `@xterm/addon-unicode11`
- Load addon, set `term.unicode.activeVersion = '11'`

**Add AttachAddon (WebSocket backend)**
- Install: `@xterm/addon-attach`
- Create WebSocket connection first
- Load addon AFTER WebSocket `onopen` fires
- Handle WebSocket close/error events

### Integration Features

**Wire PTY backend (node-pty + WebSocket)**
- Server: spawn `node-pty` process, pipe stdin/stdout over WebSocket
- Client: AttachAddon or manual `onData` -> ws.send, ws.onmessage -> `term.write()`
- Handle resize: `term.onResize` -> send cols/rows to server -> `pty.resize()`
- Handle exit: `pty.onExit` -> close WebSocket -> show exit message in terminal

**Add theming / theme switcher**
- Define theme objects with full color palette (background, foreground, cursor, selection, ansi colors 0-15)
- Apply with `term.options.theme = newTheme`
- If switching dynamically, no reload needed -- theme applies immediately

**Add custom key handler**
- Use `term.attachCustomKeyEventHandler((ev) => { ... return true/false })`
- Return `false` to prevent default terminal handling
- Common: intercept Ctrl+C, Ctrl+V, Ctrl+Shift+C for custom behavior

**Add decorations/markers**
- Create marker: `const marker = term.registerMarker(0)` (0 = current line)
- Create decoration: `term.registerDecoration({ marker, width, height })`
- Style via returned element: `decoration.onRender(el => el.style.background = '...')`

**Add parser hook (custom OSC/CSI sequences)**
- Register: `term.parser.registerOscHandler(id, data => { ... return true })`
- Common: custom OSC for setting title, notifications, file links
- Backend sends custom sequence, frontend parser hook handles it

**Integrate into React component**
- Terminal ref via `useRef<HTMLDivElement>(null)`
- Create terminal in `useEffect`, dispose in cleanup return
- Store terminal instance in ref if needed: `termRef.current = term`
- Do NOT create terminal in render body or useState initializer

**Integrate into Vue component**
- Terminal ref via `ref<HTMLDivElement>()`
- Create terminal in `onMounted`, dispose in `onUnmounted`
- Use `shallowRef` for terminal instance to avoid reactivity overhead

**Add responsive resize (ResizeObserver + FitAddon)**
- Create `ResizeObserver` on the terminal container element
- On resize callback: call `fitAddon.fit()`
- Debounce if needed to avoid excessive resize calls
- Dispose observer in cleanup

## Step 4: Install Dependencies

Check if required packages are installed:

```bash
cat package.json | grep -E "@xterm/(addon-fit|addon-webgl|addon-search|addon-web-links|addon-clipboard|addon-unicode11|addon-attach)"
```

If missing, list the install command but ask before running it.

## Step 5: Implement

Apply changes through repository edit:

1. Add imports at the top of the file, grouped with existing xterm imports
2. Add addon instantiation near existing addon setup
3. Load addon in the correct position relative to `open()` and other addons
4. Add event handlers and cleanup
5. Add any required CSS

Verify after implementation:
- No duplicate imports or addon loads
- Loading order is correct
- Cleanup/disposal handles the new addon
- No TypeScript errors in the changes

## Summary

After implementation, print:

```
xterm.js feature implemented: [feature name]

Changes:
- [file]: [what was added/modified]

New dependencies (install if needed):
- npm install @xterm/addon-xxx

Notes:
- [any caveats, browser requirements, or follow-up needed]
```
