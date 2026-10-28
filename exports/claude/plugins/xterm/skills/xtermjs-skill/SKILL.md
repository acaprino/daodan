---
name: xtermjs-skill
description: >
  Build, configure, debug and extend browser and Electron terminal UIs with xterm.js (@xterm/xterm).
  TRIGGER WHEN: working with xterm.js, @xterm/xterm, FitAddon, WebglAddon, SearchAddon, AttachAddon, node-pty over WebSocket, ANSI/VT sequences, or embedding a web terminal in React/Vue/Electron.
---

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

# xterm.js Development Skill

xterm.js (`@xterm/xterm`) is a terminal emulator for the browser and Electron. It is not a shell: connect it to a backend process (such as `node-pty` over WebSocket) to execute commands.

## Reference router

| Task | Reference |
|---|---|
| Custom themes, key handlers, `SearchAddon`, markers/decorations, OSC/CSI parser hooks, high-throughput streaming, ConPTY quirks, WebGL sleep recovery, or coordinate translation | `references/advanced-api-and-resiliency.md` |

## 1. Installation

```bash
npm install @xterm/xterm
# Install only needed addons:
npm install @xterm/addon-fit @xterm/addon-attach @xterm/addon-web-links \
            @xterm/addon-search @xterm/addon-webgl @xterm/addon-clipboard \
            @xterm/addon-web-fonts @xterm/addon-unicode11
```

Always import the CSS (`import '@xterm/xterm/css/xterm.css';`).

## 2. Basic Setup

```ts
import { Terminal } from '@xterm/xterm';

const term = new Terminal({
  cols: 80,
  rows: 24,
  cursorBlink: true,
  scrollback: 5000,
  fontFamily: '"Cascadia Code", Menlo, monospace',
  fontSize: 14,
  theme: {
    background: '#1e1e1e',
    foreground: '#d4d4d4',
    cursor: '#d4d4d4',
  },
});

term.open(document.getElementById('terminal')!);
term.write('Hello from \x1B[1;32mxterm.js\x1B[0m\r\n$ ');
```

Call `term.open(element)` only after the element is mounted in the DOM with non-zero dimensions. Use `\r\n` for newlines when writing directly.

## 3. Official Addons

| Addon | Package | Purpose |
|---|---|---|
| FitAddon | `@xterm/addon-fit` | Resize terminal to fill its container |
| AttachAddon | `@xterm/addon-attach` | Connect to a WebSocket backend |
| SearchAddon | `@xterm/addon-search` | In-terminal text search |
| WebglAddon | `@xterm/addon-webgl` | GPU-accelerated WebGL2 renderer |
| WebLinksAddon | `@xterm/addon-web-links` | Clickable URLs |
| ClipboardAddon | `@xterm/addon-clipboard` | Browser clipboard integration |
| WebFontsAddon | `@xterm/addon-web-fonts` | Wait for web fonts before rendering |
| Unicode11Addon | `@xterm/addon-unicode11` | Unicode 11 character width support |

```ts
import { FitAddon } from '@xterm/addon-fit';
import { WebglAddon } from '@xterm/addon-webgl';
import { WebLinksAddon } from '@xterm/addon-web-links';

const fitAddon = new FitAddon();
term.loadAddon(fitAddon);
term.loadAddon(new WebLinksAddon());
term.open(document.getElementById('terminal')!);

try {
  const webgl = new WebglAddon();
  webgl.onContextLoss(() => webgl.dispose());
  term.loadAddon(webgl);
} catch {
  console.warn('WebGL2 unavailable, falling back to default renderer');
}

fitAddon.fit();
const ro = new ResizeObserver(() => fitAddon.fit());
ro.observe(document.getElementById('terminal')!);
```

## 4. Backend Integration: `node-pty` + WebSocket

### Frontend (`AttachAddon` or Manual Wiring)

```ts
import { AttachAddon } from '@xterm/addon-attach';

const socket = new WebSocket('ws://localhost:3000/ws');
term.loadAddon(new AttachAddon(socket));

term.onResize(({ cols, rows }) => {
  socket.send(JSON.stringify({ type: 'resize', cols, rows }));
});
```

For custom framing without `AttachAddon`, wire `ptyProcess.onData(d => term.write(d))`, `term.onData(d => ptyProcess.write(d))`, and `term.onBinary(d => ptyProcess.write(d))`.

### Backend (Node.js + `node-pty`)

```ts
import * as pty from 'node-pty';
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 3000 });

wss.on('connection', (ws) => {
  const shell = process.platform === 'win32' ? 'powershell.exe' : 'bash';
  const ptyProcess = pty.spawn(shell, [], {
    name: 'xterm-color',
    cols: 80,
    rows: 24,
    env: process.env,
  });

  ptyProcess.onData((data) => ws.send(data));
  ws.on('message', (msg) => {
    const parsed = JSON.parse(msg.toString());
    if (parsed.type === 'resize') {
      ptyProcess.resize(parsed.cols, parsed.rows);
    } else {
      ptyProcess.write(msg.toString());
    }
  });
  ws.on('close', () => ptyProcess.kill());
});
```

## 5. React Integration Pattern

```tsx
import { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

export function XTerminal() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const term = new Terminal({ cursorBlink: true });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current!);
    fitAddon.fit();

    const ro = new ResizeObserver(() => fitAddon.fit());
    ro.observe(containerRef.current!);

    return () => {
      ro.disconnect();
      term.dispose();
    };
  }, []);

  return <div ref={containerRef} style={{ width: '100%', height: '400px' }} />;
}
```

## 6. Common Pitfalls and Disposal

| Problem | Cause | Fix |
|---|---|---|
| Terminal renders blank / wrong size | `fit()` called before DOM paint or `display: none` | Call `fitAddon.fit()` after `open()`, use `ResizeObserver`, avoid `display: none` |
| Characters appear wrong width | Unicode width table | Load `Unicode11Addon`, set `term.unicode.activeVersion = '11'` |
| Backspace does not work | PTY termios mismatch | Send `\x7f` or `\x08`; check PTY settings |
| WebGL context lost after sleep/tab switch | GPU resource reclaim | Handle `onContextLoss`, DOM `webglcontextlost`, and health check (see `references/advanced-api-and-resiliency.md`) |
| `\n` without `\r` causes staircase | Missing carriage return | Use `\r\n` or set `convertEol: true` |

Always call `term.dispose()` (and `marker.dispose()` / `decoration.dispose()`) on teardown to prevent memory leaks.
